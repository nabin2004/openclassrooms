import json
import os
from dotenv import load_dotenv
import litellm

from manimator.contracts.validation import ValidationResult

load_dotenv()

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


def strip_markdown_code_blocks(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            content = parts[1].strip()
            if "\n" in content:
                first_line = content.split("\n", 1)[0].lower()
                if first_line in {"python", "py"}:
                    content = content.split("\n", 1)[1]
            return content.strip()
    return text


async def repair_code(validation: ValidationResult) -> str:
    if validation.passed:
        return validation.failing_code or ""

    payload = {
        "error_type": validation.error_type,
        "error_message": validation.error_message,
        "code": validation.failing_code,
        "spec": validation.original_spec.model_dump(),
    }

    response = await litellm.acompletion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        temperature=0.1,  # keeps it deterministic
    )

    raw = response.choices[0].message.content.strip()
    print("[DEBUG] Raw LLM response (repair):", repr(raw))
    fixed_code = strip_markdown_code_blocks(raw)
    return fixed_code