# Manimator batch IR pipeline

Run hundreds or thousands of prompts through the same **contract-first IR pipeline** as the interactive LangGraph app, then export **JSONL supervision files** per stage for fine-tuning or analysis.

**Always run CLIs from the repository root** (`openclassrooms/`) so `import logging` resolves to the stdlib (see repo `README.md` and `docs/PROJECT_FORWARD.md`).

---

## Prerequisites

- **uv** workspace synced: `make sync` or `uv sync --all-packages` from the repo root.
- **API keys** in `.env` at repo root (and/or `manimator/.env`) for every LLM stage you enable—same as a normal Manimator run (intent, decompose, planner, codegen, repair, critic, etc.).
- **Disk**: each full run writes under `outputs/runs/<run_id>/` (`ir/`, `code/`, `renders/`, `manim_media/`, …). Budget tens of GB for ~2k samples if you include **render**; IR-only subsets use far less.
- **Time / cost**: 2k full pipelines are dominated by LLM calls and optional Manim renders. Start with a **pilot** (`--count 10` on querygen + `--stages intent,scene_plan` or low `--concurrency`) before a long unattended batch.

---

## End-to-end: ~2k dataset

### 1. Generate `queries.jsonl` (~2000 lines)

Built-in seeds: **~132 STEM/CS topics** × **20 templates** → **2640** unique prompts; the default `--count 2000` takes the first 2000 (deterministic order). Use **`--shuffle`** for a random slice (set **`--seed`** for reproducibility).

```bash
cd /path/to/openclassrooms

# Default: 2000 lines using bundled topics × templates
uv run --package manimator python -m manimator.batch.querygen \
  --output data/batch_queries_2k.jsonl \
  --count 2000

# Random order, reproducible
uv run --package manimator python -m manimator.batch.querygen \
  --output data/batch_queries_2k.jsonl \
  --count 2000 \
  --shuffle \
  --seed 42
```

**Custom topics** (one short phrase per line; `#` comments and blank lines ignored). You need enough **topic × template** combinations to reach `--count`, or the tool appends `[variant_N]` suffixes when cycling.

```bash
uv run --package manimator python -m manimator.batch.querygen \
  --output data/my_queries.jsonl \
  --count 2000 \
  --topics-file path/to/topics.txt
```

### 2. Pilot run (strongly recommended)

```bash
# Tiny input: copy first 5 lines from data/batch_queries_2k.jsonl to data/pilot.jsonl, then:
uv run --package manimator python -m manimator.batch.runner \
  --input data/pilot.jsonl \
  --batch-id pilot_001 \
  --concurrency 2 \
  --stages intent,scene_plan
```

Inspect `outputs/batches/pilot_001/progress.jsonl` and one `outputs/runs/<run_id>/ir/` folder before scaling up.

### 3. Full batch (~2k)

```bash
uv run --package manimator python -m manimator.batch.runner \
  --input data/batch_queries_2k.jsonl \
  --batch-id dataset_2k_v1 \
  --profile through_critic \
  --concurrency 8 \
  --render-concurrency 2
```

- **`--profile through_critic`** (default): stops after critic—good for SFT JSONL **without** TTS.
- **`--profile full_delivery`**: also runs narration + final packaging (heavier deps and disk).
- If the process stops, re-run the **same** command with **`--resume`** (same `--batch-id`). Skips stages whose IR already exists **and** matches `batch_cache.json` + manifest fingerprint.

### 4. Export per-stage JSONL (training format)

```bash
uv run --package manimator python -m manimator.batch.export \
  --batch-id dataset_2k_v1 \
  --outputs-root outputs
```

Artifacts appear under:

`outputs/datasets/dataset_2k_v1/<stage>.jsonl`

Each line is roughly:

`{ "input": { ... }, "output": <IR dict>, "metadata": { "run_id", "batch_id", "stage", "pipeline_fingerprint", "ts" } }`

Stage-specific `input` shapes are built from whatever IR existed on disk for that run (see `export.py`).

---

## All commands (reference)

| Step | Command |
|------|---------|
| Generate queries | `uv run --package manimator python -m manimator.batch.querygen --output FILE.jsonl --count N` |
| Run batch | `uv run --package manimator python -m manimator.batch.runner --input FILE.jsonl --batch-id ID` |
| Export datasets | `uv run --package manimator python -m manimator.batch.export --batch-id ID` |

---

## Input JSONL (`runner`)

Each line is one JSON object:

| Field | Required | Description |
|--------|----------|-------------|
| `raw_query` or `query` | Yes | Prompt text for the pipeline. |
| `row_id` | No | Stable id for logs (default: line index). |
| `run_id` | No | Default: deterministic hash from `(batch_id, row_index, raw_query)`. |

---

## Outputs (layout)

| Path | Purpose |
|------|---------|
| `outputs/runs/<run_id>/ir/*` | Same IR files as the main app (`intent.json`, `scene_plan.json`, …). |
| `outputs/batches/<batch_id>/batch_manifest.json` | `pipeline_fingerprint`, prompt version snapshot, sample list. |
| `outputs/batches/<batch_id>/progress.jsonl` | One JSON object per stage attempt: `ok`, `skipped`, `duration_s`, `error`, timestamps. |
| `outputs/runs/<run_id>/ir/batch_cache.json` | Fingerprint sidecar for **`--resume`** skip decisions. |
| `outputs/datasets/<batch_id>/<stage>.jsonl` | Emitted by **`batch.export`**. |

---

## Stages (`runner`)

Logical stages map to `manimator.pipeline.graph` nodes:

`intent` → `scene_plan` → `scene_specs` → `codegen` → `validation` (validate / repair loop) → `render` → `critic` → optional `narrate` → `finalize`.

| Flag | Meaning |
|------|---------|
| `--profile through_critic` | Default; stop after critic. |
| `--profile full_delivery` | Include narration + finalize. |
| `--stages a,b,c` | Comma list; overrides `--profile`. |

---

## Resume and caching

With **`--resume`**:

1. **`batch_manifest.json`** must already exist for that `--batch-id`.
2. Current **`pipeline_fingerprint`** must match the manifest (prompt env vars + serialized `VideoConfig` + `MANIMATOR_VIDEO_CONFIG`). If you change prompts or config, use a **new** `--batch-id` or omit `--resume`.
3. A stage is **skipped** when its primary IR file exists **and** `ir/batch_cache.json` contains the same fingerprint.

IR produced **outside** this batch runner (no `batch_cache.json`) is **not** auto-skipped.

---

## Concurrency and renders

| Flag | Default | Notes |
|------|---------|-------|
| `--concurrency` | 8 | Cap concurrent **samples** (each runs stages sequentially). |
| `--render-concurrency` | 2 | Extra semaphore around **`node_render`** only; set **`0`** to disable. |
| `--max-critic-replans` | 0 | Bounded critic → replan → plan → codegen → validation tails. |

For API rate limits, lower **`--concurrency`**. For CPU-heavy Manim, keep **`--render-concurrency`** small (1–2).

---

## Manifest collisions

If `outputs/batches/<batch_id>/batch_manifest.json` exists and you **omit** `--resume`, the runner exits unless you pass **`--overwrite`** (rewrites manifest from the current `--input` file).

---

## Monitoring a long batch

```bash
# Lines written (each stage attempt is one line)
wc -l outputs/batches/dataset_2k_v1/progress.jsonl

# Recent failures (requires jq)
grep '"ok": false' outputs/batches/dataset_2k_v1/progress.jsonl | tail -5
```

Token usage in progress rows is reserved for future wiring (`tokens_total` may be `null` today unless extended per agent).

---

## Tests

```bash
uv run --package manimator -m pytest manimator/tests/batch/ -q
```

---

## Module layout

| Module | Role |
|--------|------|
| `querygen.py` | Build `queries.jsonl` from topics × templates. |
| `seed_topics.py` | Default topic list for querygen. |
| `ir_load.py` | Load `PipelineState` from `ir/*.json`. |
| `fingerprint.py` | Stable env + config fingerprint. |
| `manifest.py` | Batch manifest read/write. |
| `cache_meta.py` | Per-run `batch_cache.json`. |
| `state_merge.py` | Apply `node_*` return dicts to state. |
| `stages.py` | Logical stages → graph nodes. |
| `runner.py` | Async batch orchestration + `progress.jsonl`. |
| `export.py` | Scan manifest runs → dataset JSONL. |
