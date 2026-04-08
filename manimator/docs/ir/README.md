## Manimator Intermediate Representation (IR)

Manimator is a **contract-first compiler pipeline**. Each stage produces a typed, versioned artifact (the IR) that can be:
- inspected/debugged by humans
- cached (skip stages when the same input/IR already exists)
- used as datasets later (finetuning / RL / evals)

### Where IR lives
Each run is grouped under:

- `outputs/runs/<run_id>/ir/`

This folder is append/overwrite-safe: each pipeline node re-emits the current best-known IR snapshot.

### IR artifacts (current)
- `run_summary.json`: run metadata and counts
- `intent.json`: `IntentResult`
- `scene_plan.json`: `ScenePlan`
- `scene_specs.json`: list of `SceneSpec`
- `generated_codes.json`: map scene_id → code text
- `code_paths.json`: map scene_id → code file path (on disk)
- `validation_results.json`: ordered list of `ValidationResult`
- `rendered_paths.json`: map scene_id → mp4 path
- `narrated_paths.json`: map scene_id → narrated mp4 path
- `critic_result.json`: `CriticResult`
- `scene_transcripts.json`: map scene_id → transcript
- `full_transcript.json`: wrapper containing full transcript string

### Recommended future use
- **Caching**: use `(raw_query, prompt_versions, config)` as a cache key; if `scene_plan.json` exists, you can skip decomposition.\n+- **Training data**: each artifact is a supervised signal. For example:\n+  - decomposer: `raw_query → scene_plan.json`\n+  - planner: `SceneEntry (+ feedback) → SceneSpec`\n+  - repair: `ValidationResult → fixed_code`\n+
