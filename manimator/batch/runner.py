"""CLI: batch JSONL → per-run IR + progress JSONL (asyncio, resume, concurrency)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from manimator.batch.cache_meta import read_batch_cache_fingerprint, write_batch_cache
from manimator.batch.fingerprint import compute_pipeline_fingerprint, prompt_versions_snapshot
from manimator.batch.ir_load import load_pipeline_state
from manimator.batch.manifest import (
    BatchSampleRef,
    manifest_path,
    progress_path,
    raw_query_hash,
    read_batch_manifest,
    write_batch_manifest,
)
from manimator.batch.stages import (
    LogicalStage,
    artifact_ready,
    resolve_stage_list,
    run_logical_stage,
)
from manimator.paths import get_run_paths
from manimator.pipeline.state import PipelineState


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _stable_run_id(batch_id: str, row_index: int, raw_query: str, explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    import hashlib

    h = hashlib.sha256(f"{batch_id}:{row_index}:{raw_query}".encode("utf-8")).hexdigest()[:16]
    return h


def _load_input_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _should_skip(
    ir_dir: Path,
    stage: LogicalStage,
    *,
    resume: bool,
    fingerprint: str,
) -> bool:
    if not resume:
        return False
    if not artifact_ready(ir_dir, stage):
        return False
    cached = read_batch_cache_fingerprint(ir_dir)
    return cached == fingerprint


def _hydrate_state(ir_dir: Path, raw_query: str, run_id: str) -> PipelineState:
    summary = ir_dir / "run_summary.json"
    if summary.is_file():
        return load_pipeline_state(ir_dir, run_id=run_id)
    return PipelineState(raw_query=raw_query, run_id=run_id)


async def _run_one_sample(
    *,
    row_index: int,
    row: dict[str, Any],
    batch_id: str,
    fingerprint: str,
    stages: tuple[LogicalStage, ...],
    resume: bool,
    max_critic_replans: int,
    outputs_root: Path,
    progress_file: Path,
    progress_lock: asyncio.Lock,
    sem: asyncio.Semaphore,
    render_sem: asyncio.Semaphore | None,
) -> None:
    raw_query = str(row.get("raw_query") or row.get("query") or "").strip()
    if not raw_query:
        async with progress_lock:
            _append_jsonl(
                progress_file,
                {
                    "run_id": "",
                    "row_id": str(row.get("row_id", row_index)),
                    "stage": "_input",
                    "ts_start": _ts(),
                    "ts_end": _ts(),
                    "duration_s": 0.0,
                    "ok": False,
                    "skipped": False,
                    "error": "empty raw_query",
                    "pipeline_fingerprint": fingerprint,
                },
            )
        return

    run_id = _stable_run_id(batch_id, row_index, raw_query, row.get("run_id"))
    row_id = str(row.get("row_id", row_index))
    paths = get_run_paths(run_id, outputs_root=outputs_root)
    ir_dir = paths.ir_dir

    async with sem:
        state = _hydrate_state(ir_dir, raw_query, run_id)

        if state.intent is not None and not state.intent.in_scope:
            async with progress_lock:
                for st in stages:
                    _append_jsonl(
                        progress_file,
                        {
                            "run_id": run_id,
                            "row_id": row_id,
                            "stage": st.value,
                            "ts_start": _ts(),
                            "ts_end": _ts(),
                            "duration_s": 0.0,
                            "ok": True,
                            "skipped": True,
                            "skip_reason": "intent_out_of_scope",
                            "tokens_total": None,
                            "pipeline_fingerprint": fingerprint,
                        },
                    )
            return

        for st in stages:
            t0 = time.perf_counter()
            ts_start = _ts()
            if _should_skip(ir_dir, st, resume=resume, fingerprint=fingerprint):
                state = load_pipeline_state(ir_dir, run_id=run_id)
                async with progress_lock:
                    _append_jsonl(
                        progress_file,
                        {
                            "run_id": run_id,
                            "row_id": row_id,
                            "stage": st.value,
                            "ts_start": ts_start,
                            "ts_end": _ts(),
                            "duration_s": round(time.perf_counter() - t0, 4),
                            "ok": True,
                            "skipped": True,
                            "tokens_total": None,
                            "pipeline_fingerprint": fingerprint,
                        },
                    )
                continue

            try:
                if st is LogicalStage.render and render_sem is not None:
                    async with render_sem:
                        await run_logical_stage(state, st, max_critic_replans=max_critic_replans)
                else:
                    await run_logical_stage(state, st, max_critic_replans=max_critic_replans)

                if st is LogicalStage.intent and state.error:
                    dur = time.perf_counter() - t0
                    write_batch_cache(ir_dir, pipeline_fingerprint=fingerprint)
                    async with progress_lock:
                        _append_jsonl(
                            progress_file,
                            {
                                "run_id": run_id,
                                "row_id": row_id,
                                "stage": st.value,
                                "ts_start": ts_start,
                                "ts_end": _ts(),
                                "duration_s": round(dur, 4),
                                "ok": False,
                                "skipped": False,
                                "error": str(state.error),
                                "tokens_total": None,
                                "pipeline_fingerprint": fingerprint,
                            },
                        )
                    break

                dur = time.perf_counter() - t0
                write_batch_cache(ir_dir, pipeline_fingerprint=fingerprint)
                async with progress_lock:
                    _append_jsonl(
                        progress_file,
                        {
                            "run_id": run_id,
                            "row_id": row_id,
                            "stage": st.value,
                            "ts_start": ts_start,
                            "ts_end": _ts(),
                            "duration_s": round(dur, 4),
                            "ok": True,
                            "skipped": False,
                            "error": None,
                            "tokens_total": None,
                            "pipeline_fingerprint": fingerprint,
                        },
                    )
            except Exception as e:
                dur = time.perf_counter() - t0
                async with progress_lock:
                    _append_jsonl(
                        progress_file,
                        {
                            "run_id": run_id,
                            "row_id": row_id,
                            "stage": st.value,
                            "ts_start": ts_start,
                            "ts_end": _ts(),
                            "duration_s": round(dur, 4),
                            "ok": False,
                            "skipped": False,
                            "error": f"{type(e).__name__}: {e}",
                            "tokens_total": None,
                            "pipeline_fingerprint": fingerprint,
                        },
                    )
                break


async def _async_main(args: argparse.Namespace) -> int:
    outputs_root = Path(args.outputs_root).resolve()
    batch_id = args.batch_id or uuid.uuid4().hex[:12]
    input_path = Path(args.input).resolve()
    rows = _load_input_rows(input_path)

    fingerprint = compute_pipeline_fingerprint()
    prompt_snap = prompt_versions_snapshot()
    mpath = manifest_path(outputs_root, batch_id)

    if mpath.is_file() and not args.resume and not args.overwrite:
        print(
            f"Manifest already exists at {mpath}. Use --resume to continue or --overwrite to replace.",
            file=sys.stderr,
        )
        return 3

    if args.resume and not mpath.is_file():
        print("--resume requires an existing batch_manifest.json for this --batch-id.", file=sys.stderr)
        return 4

    if args.resume and mpath.is_file():
        existing = read_batch_manifest(mpath)
        if existing.get("pipeline_fingerprint") != fingerprint:
            print(
                "Refusing resume: pipeline_fingerprint differs from existing manifest "
                "(env/config changed). Re-run without --resume or use a new --batch-id.",
                file=sys.stderr,
            )
            return 2
    if not (args.resume and mpath.is_file()):
        samples = [
            BatchSampleRef(
                row_id=str(r.get("row_id", i)),
                run_id=_stable_run_id(batch_id, i, str(r.get("raw_query") or r.get("query") or "").strip(), r.get("run_id")),
                raw_query_hash=raw_query_hash(str(r.get("raw_query") or r.get("query") or "").strip()),
            )
            for i, r in enumerate(rows)
        ]
        write_batch_manifest(
            outputs_root=outputs_root,
            batch_id=batch_id,
            pipeline_fingerprint=fingerprint,
            prompt_versions=prompt_snap,
            samples=samples,
        )

    stages = resolve_stage_list(
        [s.strip() for s in args.stages.split(",")] if args.stages else None,
        profile=args.profile,
    )
    progress_file = progress_path(outputs_root, batch_id)
    progress_lock = asyncio.Lock()
    sem = asyncio.Semaphore(max(1, int(args.concurrency)))
    render_sem: asyncio.Semaphore | None = None
    if int(args.render_concurrency) > 0:
        render_sem = asyncio.Semaphore(max(1, int(args.render_concurrency)))

    tasks = [
        _run_one_sample(
            row_index=i,
            row=row,
            batch_id=batch_id,
            fingerprint=fingerprint,
            stages=stages,
            resume=bool(args.resume),
            max_critic_replans=int(args.max_critic_replans),
            outputs_root=outputs_root,
            progress_file=progress_file,
            progress_lock=progress_lock,
            sem=sem,
            render_sem=render_sem,
        )
        for i, row in enumerate(rows)
    ]
    await asyncio.gather(*tasks)
    print(json.dumps({"batch_id": batch_id, "manifest": str(mpath), "progress": str(progress_file)}, indent=2))
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Manimator batch IR runner (run from repo root: python -m manimator.batch.runner).")
    p.add_argument("--input", type=Path, required=True, help="JSONL with raw_query (or query) per line; optional row_id, run_id.")
    p.add_argument("--batch-id", default=None, help="Stable id for outputs/batches/<id>/ (default: random).")
    p.add_argument("--outputs-root", type=Path, default=Path("outputs"), help="Root containing runs/ and batches/.")
    p.add_argument(
        "--profile",
        choices=("through_critic", "full_delivery"),
        default="through_critic",
        help="Default stage list when --stages is omitted.",
    )
    p.add_argument(
        "--stages",
        default=None,
        help="Comma-separated logical stages (overrides profile), e.g. intent,scene_plan",
    )
    p.add_argument("--resume", action="store_true", help="Skip stages when IR artifact + batch_cache fingerprint match.")
    p.add_argument("--concurrency", type=int, default=8, help="Max concurrent samples.")
    p.add_argument(
        "--render-concurrency",
        type=int,
        default=2,
        help="Separate cap for render stage (default 2); set 0 to disable extra render limiting.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing a new manifest when one already exists (without --resume).",
    )
    p.add_argument(
        "--max-critic-replans",
        type=int,
        default=0,
        help="After critic replan_required, re-run plan→codegen→validation up to N times (default 0).",
    )
    args = p.parse_args()
    rc = asyncio.run(_async_main(args))
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
