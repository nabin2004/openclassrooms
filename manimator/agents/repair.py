from manimator.contracts.validation import ValidationResult


async def repair_code(validation: ValidationResult) -> str:
    # STUB — returns the failing code unchanged
    # Real implementation will use LLM to patch
    return validation.failing_code or ""
