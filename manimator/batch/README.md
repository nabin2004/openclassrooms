# Manimator batch IR pipeline

Process many prompts (~2k) into the same **per-run IR layout** as the interactive LangGraph pipeline, with **resume**, **bounded concurrency**, and **JSONL dataset export**.

Run CLIs from the **repository root** so `import logging` resolves to the stdlib (see repo `README.md` / `PROJECT_FORWARD.md`).

```bash
uv run --package manimator python -m manimator.batch.runner --input queries.jsonl --batch-id my_batch
uv run --package manimator python -m manimator.batch.export --batch-id my_batch
```

## Input JSONL

Each line is a JSON object:

- **`raw_query`** (or `query`): required text.
- **`row_id`**: optional stable id for logs (default: line index).
- **`run_id`**: optional; default is a deterministic hash from `(batch_id, row_index, raw_query)`.

## Outputs

| Path | Purpose |
|------|---------|
| `outputs/runs/<run_id>/ir/*` | Same artifacts as the main pipeline (`intent.json`, …). |
| `outputs/batches/<batch_id>/batch_manifest.json` | `pipeline_fingerprint`, prompt version snapshot, sample list. |
| `outputs/batches/<batch_id>/progress.jsonl` | One line per stage attempt: `ok`, `skipped`, `duration_s`, `error`. |
| `outputs/runs/<run_id>/ir/batch_cache.json` | Fingerprint sidecar used with `--resume` to decide safe skips. |
| `outputs/datasets/<batch_id>/<stage>.jsonl` | Built by `batch.export` (supervision rows). |

## Stages

Logical stages map to existing graph nodes (`manimator.pipeline.graph`):

`intent` → `scene_plan` → `scene_specs` → `codegen` → `validation` (validate/repair loop) → `render` → `critic` [→ `narrate` → `finalize` if profile `full_delivery`].

- **`--profile through_critic`** (default): stop after critic (good for SFT data without TTS).
- **`--profile full_delivery`**: also run narration and final packaging.
- **`--stages a,b,c`**: overrides profile with an explicit subset.

## Resume and caching

With **`--resume`**:

1. The runner refuses to start if `batch_manifest.json` is missing or if the current **`pipeline_fingerprint`** (prompt env vars + `VideoConfig` + `MANIMATOR_VIDEO_CONFIG`) differs from the manifest (avoids silent mixing of configs).
2. A stage is **skipped** when its primary IR file exists **and** `ir/batch_cache.json` contains the same `pipeline_fingerprint` as the manifest.

Runs that were produced **outside** the batch runner (no `batch_cache.json`) are **not** skipped automatically, so stale artifacts are not reused by mistake.

## Concurrency

- **`--concurrency`**: max samples in flight (default 8).
- **`--render-concurrency`**: extra cap around `node_render` only (default 2). Set to **`0`** to disable the extra render semaphore.

## Critic replans

**`--max-critic-replans`** (default **0**): after `node_critique`, if `replan_required` and the budget allows, re-run `plan` → `codegen` → `validation` up to N times. The LangGraph app uses `MAX_REPLANS` from contracts; this flag bounds **extra** tails for batch jobs.

## Manifest collisions

If `batch_manifest.json` already exists and you omit **`--resume`**, the runner exits unless you pass **`--overwrite`** (rewrites manifest and sample list from the input file).

```bash
cd openclassrooms   # repo root
uv run --package manimator python -m manimator.batch.runner --input queries.jsonl --batch-id my_batch
uv run --package manimator python -m manimator.batch.export --batch-id my_batch
```