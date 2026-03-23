import pytest
from pydantic import ValidationError
from manimator.contracts.validation import ValidationResult, ErrorType, MAX_RETRIES
from manimator.contracts.scene_spec import SceneSpec, MobjectSpec, AnimationSpec
from manimator.contracts.scene_plan import SceneClass, Budget


def make_spec():
    return SceneSpec(
        scene_id=0, class_name="TestScene", scene_class=SceneClass.SCENE,
        budget=Budget.LOW, imports=["Scene"],
        objects=[MobjectSpec(name="c", type="Circle")],
        animations=[AnimationSpec(type="Create", target="c")],
    )


def test_passed_result():
    result = ValidationResult(passed=True, scene_id=0, retry_count=0)
    assert result.passed


def test_failure_requires_all_fields():
    with pytest.raises(ValidationError, match="required when passed=False"):
        ValidationResult(passed=False, scene_id=0, retry_count=0)


def test_valid_failure():
    result = ValidationResult(
        passed=False, scene_id=1,
        failing_code="class X(Scene): pass",
        error_type=ErrorType.NAME_ERROR,
        error_message="NameError: name 'GradientArrow' is not defined",
        error_line=14,
        retry_count=1,
        original_spec=make_spec(),
    )
    assert result.error_type == ErrorType.NAME_ERROR


def test_retry_count_at_max_raises():
    with pytest.raises(ValidationError, match="MAX_RETRIES"):
        ValidationResult(passed=True, scene_id=0, retry_count=MAX_RETRIES)