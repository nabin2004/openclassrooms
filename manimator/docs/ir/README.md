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

### Caching (future)
- Suggested cache key inputs:
  - `raw_query`
  - prompt versions (`INTENT_CLASSIFIER_PROMPT_VERSION`, `SCENE_DECOMPOSER_PROMPT_VERSION`, `SCENE_PLANNER_PROMPT_VERSION`, `CODE_REPAIR_PROMPT_VERSION`)
  - config profile (`MANIMATOR_VIDEO_CONFIG`) and other relevant env knobs
- Suggested cache values:
  - `intent.json` (skip intent stage)
  - `scene_plan.json` (skip decomposer)
  - `scene_specs.json` (skip planner)
  - `generated_codes.json` + `code/*.py` (skip codegen)

### Training / finetuning / RL datasets (future)
Each IR edge is a supervised signal. Examples:
- decomposer: `raw_query → scene_plan.json`
- planner: `SceneEntry (+ feedback) → SceneSpec`
- validator/repair loop: `ValidationResult → fixed_code`
- critic: `(renders/keyframes + spec) → CriticResult`

Practical dataset exports usually look like JSONL with fields:
- `input` (prompt + context)
- `output` (the target IR artifact)
- `metadata` (run_id, prompt version, model, tokens/cost, timestamps)
