import json
import os

from amoeba.core.litellm_chat import acompletion_system_user
from amoeba.runtime import load_agent_env
from amoeba.utils import strip_fences

from manimator.contracts.validation import ValidationResult

load_agent_env()

MODEL = os.getenv("CODE_REPAIR_MODEL", "groq/llama-3.1-8b-instant")


SYSTEM_PROMPT = """
You are a Manim code repair assistant.

You will be given:
- Broken Manim Python code
- The error type and message
- The original scene specification

Your job:
- Fix the code so it runs correctly
- Do NOT change the structure unless necessary
- Do NOT remove animations or objects unless required
- Keep it minimal and valid

Return ONLY valid Python code.
No explanations.
"""


async def repair_code(validation: ValidationResult) -> str:
    if validation.passed:
        return validation.failing_code or ""

    payload = {
        "error_type": validation.error_type,
        "error_message": validation.error_message,
        "code": validation.failing_code,
        "spec": validation.original_spec.model_dump(),
    }

    raw = await acompletion_system_user(
        model=MODEL,
        system=SYSTEM_PROMPT,
        user=json.dumps(payload),
        temperature=0.1,
        error_context="Repair agent",
    )
    print("[DEBUG] Raw LLM response (repair):", repr(raw))
    fixed_code = strip_fences(raw)
    return fixed_code