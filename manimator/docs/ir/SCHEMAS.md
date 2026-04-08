## IR schema sources

Manimator keeps its “true” IR schemas in `manimator/contracts/` (Pydantic models with validators).

### Core IR
- **Intent**: `manimator/contracts/intent.py`
- **Scene plan**: `manimator/contracts/scene_plan.py`
- **Scene spec**: `manimator/contracts/scene_spec.py`
- **Validation result**: `manimator/contracts/validation.py`
- **Critic result**: `manimator/contracts/critic.py`

### LLM-output schemas (pre-domain mapping)
LLMs often emit extra fields and partial shapes. We parse them into permissive models and then map into the strict IR:

- `manimator/contracts/llm_outputs.py`

This separation is intentional so we can:\n- keep strict IR stable\n- accept richer model outputs without constantly widening domain contracts\n
