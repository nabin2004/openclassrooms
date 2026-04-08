## IR schema sources

Manimator keeps its “true” IR schemas in `manimator/contracts/` (Pydantic models with validators).

### Core IR
- **Intent classifier output + intent IR**: `manimator/contracts/intent.py`
  - `ConceptType` (enum)
  - `Modality` (enum)
  - `IntentClassificationPayload` (LLM output schema)
  - `IntentResult` (IR schema)

- **Scene plan IR**: `manimator/contracts/scene_plan.py`
  - `SceneClass` (enum)
  - `Budget` (enum)
  - `TransitionStyle` (enum)
  - `SceneEntry` (IR schema)
  - `ScenePlan` (IR schema; `schema_version="1.0.0"`)

- **Scene spec IR**: `manimator/contracts/scene_spec.py`
  - `MobjectSpec`
  - `AnimationSpec`
  - `CameraOp`
  - `SceneSpec` (IR schema; `schema_version="1.0.0"`)
  - `MANIM_CLASS_WHITELIST` (safety allowlist used by validators)

- **Validation IR**: `manimator/contracts/validation.py`
  - `ErrorType` (enum)
  - `ValidationResult` (IR schema; `schema_version="1.0.0"`)

- **Critic IR**: `manimator/contracts/critic.py`
  - `CriticResult` (IR schema; `schema_version="1.0.0"`)
  - `MAX_REPLANS`, `DEFAULT_THRESHOLD` (control constants used by pipeline)

### LLM-output schemas (pre-domain mapping)
LLMs often emit extra fields and partial shapes. We parse them into permissive models and then map into the strict IR:

- `manimator/contracts/llm_outputs.py`

Current models in `llm_outputs.py`:
- `LLMScenePlanPayload` and `LLMSceneEntryPayload` (scene decomposer output)
- `LLMPlannerPayload`, `LLMObjectSpec`, `LLMAnimationSpec`, `LLMCameraOp` (scene planner output)

This separation is intentional so we can:
- keep strict IR stable (contracts remain tight and versioned)
- accept richer model outputs (extra fields ignored) without widening domain contracts constantly
