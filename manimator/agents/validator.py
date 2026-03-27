import ast
from manimator.contracts.scene_spec import SceneSpec
from manimator.contracts.validation import ErrorType, ValidationResult


def has_construct_method(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "construct":
            return True
    return False


def has_self_play(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "play":
                    return True
    return False


def check_imports(code: str, spec: SceneSpec) -> tuple[bool, str | None]:
    for imp in spec.imports:
        if imp not in code:
            return False, f"Missing import: {imp}"
    return True, None


async def validate_code(code: str, spec: SceneSpec, retry_count: int = 0) -> ValidationResult:
    try:
        tree = ast.parse(code)
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

    # 1. Ensures construct exists
    if not has_construct_method(tree):
        return ValidationResult(
            passed=False,
            scene_id=spec.scene_id,
            failing_code=code,
            error_type=ErrorType.EMPTY_SCENE,
            error_message="Missing construct() method",
            retry_count=retry_count,
            original_spec=spec,
        )

    # 2. Ensures at least one animation (self.play)
    if not has_self_play(tree):
        return ValidationResult(
            passed=False,
            scene_id=spec.scene_id,
            failing_code=code,
            error_type=ErrorType.EMPTY_SCENE,
            error_message="No self.play() call found",
            retry_count=retry_count,
            original_spec=spec,
        )

    # 3. Checks if imports exist in code
    ok, msg = check_imports(code, spec)
    if not ok:
        return ValidationResult(
            passed=False,
            scene_id=spec.scene_id,
            failing_code=code,
            error_type=ErrorType.IMPORT,
            error_message=msg,
            retry_count=retry_count,
            original_spec=spec,
        )

    # 4. (Light) Name check; ensures object names appear
    for obj in spec.objects:
        if obj.name not in code:
            return ValidationResult(
                passed=False,
                scene_id=spec.scene_id,
                failing_code=code,
                error_type=ErrorType.NAME_ERROR,
                error_message=f"Object '{obj.name}' not used in code",
                retry_count=retry_count,
                original_spec=spec,
            )

    return ValidationResult(
        passed=True,
        scene_id=spec.scene_id,
        retry_count=retry_count,
    )