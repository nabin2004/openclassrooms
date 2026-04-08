import json
import os

import logging
from amoeba.core.litellm_chat import acompletion_system_user
from amoeba.runtime import load_agent_env
from amoeba.utils import strip_fences

from manimator.contracts.validation import ValidationResult
from manimator.prompts.registry import get_code_repair_prompt

load_agent_env()

MODEL = os.getenv("CODE_REPAIR_MODEL", "groq/llama-3.1-8b-instant")
log = logging.getLogger(__name__)

_ACTIVE_PROMPT = get_code_repair_prompt()


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
        system=_ACTIVE_PROMPT.system,
        user=json.dumps(payload),
        temperature=0.1,
        error_context="Repair agent",
    )
    log.debug("Raw LLM response (repair): %r", raw)
    fixed_code = strip_fences(raw)
    return fixed_code