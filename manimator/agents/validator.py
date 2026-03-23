import ast
from manimator.contracts.scene_spec import SceneSpec
from manimator.contracts.validation import ErrorType, ValidationResult


async def validate_code(code: str, spec: SceneSpec, retry_count: int = 0) -> ValidationResult:
    # STUB: just checks Python syntax via AST
    try:
        ast.parse(code)
        return ValidationResult(
            passed=True,
            scene_id=spec.scene_id,
            retry_count=retry_count,
        )
    except SyntaxError as e:
        return ValidationResult(
            passed=False,
            scene_id=spec.scene_id,
            failing_code=code,
            error_type=ErrorType.SYNTAX,
            error_message=str(e),
            error_line=e.lineno,
            retry_count=retry_count,
            original_spec=spec,
        )