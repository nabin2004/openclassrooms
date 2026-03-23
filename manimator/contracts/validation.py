from enum import Enum
from pydantic import BaseModel, Field, model_validator
from manimator.contracts.scene_spec import SceneSpec

class ErrorType(str, Enum):
    SYNTAX = "syntax"
    NAME_ERROR = "name_error"
    IMPORT = "import"
    EMPTY_SCENE = "empty_scene"
    CAMERA_CONFLICT = "camera_conflict"
    TIMEOUT = "timeout"

MAX_RETRIES = 3

class ValidationResult(BaseModel):
    passed: bool
    scene_id: int = Field(ge=0)
    failing_code: str | None = None
    error_type: ErrorType | None = None
    error_message: str | None = None
    error_line: int | None = Field(default=None, ge=1)
    retry_count: int = Field(ge=0)
    original_spec: SceneSpec | None = None

    @model_validator(mode="after")
    def failure_fields_required_when_not_passed(self) -> "ValidationResult":
        if not self.passed:
            missing = []
            if self.failing_code is None:
                missing.append("failing_code")
            if self.error_type is None:
                missing.append("error_type")
            if self.error_message is None:
                missing.append("error_message")
            if self.original_spec is None:
                missing.append("original_spec")
            if missing:
                raise ValueError(
                    f"Fields required when passed=False: {missing}"
                )
        return self

    @model_validator(mode="after")
    def retry_count_below_max(self) -> "ValidationResult":
        if self.retry_count >= MAX_RETRIES:
            raise ValueError(
                f"retry_count={self.retry_count} has reached MAX_RETRIES={MAX_RETRIES}. "
                f"Do not route to repair agent — emit partial result instead."
            )
        return self