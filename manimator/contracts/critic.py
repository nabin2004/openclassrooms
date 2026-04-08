from pydantic import BaseModel, Field, model_validator

MAX_REPLANS = 2
DEFAULT_THRESHOLD = 0.6

class CriticResult(BaseModel):
    schema_version: str = "1.0.0"
    replan_required: bool
    failed_scene_ids: list[int] = Field(default_factory=list)
    r_visual: float = Field(ge=0.0, le=1.0)
    r_semantic: float = Field(ge=0.0, le=1.0)
    combined_score: float = Field(ge=0.0, le=1.0)
    critic_feedback: list[str] = Field(default_factory=list)
    keyframe_paths: list[str] = Field(default_factory=list)
    replan_count: int = Field(ge=0)

    @model_validator(mode="after")
    def combined_score_matches_components(self) -> "CriticResult":
        expected = round(0.5 * self.r_visual + 0.5 * self.r_semantic, 6)
        if abs(self.combined_score - expected) > 0.01:
            raise ValueError(
                f"combined_score={self.combined_score} does not match "
                f"0.5*r_visual + 0.5*r_semantic = {expected}"
            )
        return self

    @model_validator(mode="after")
    def feedback_required_when_replan(self) -> "CriticResult":
        if self.replan_required and not self.critic_feedback:
            raise ValueError(
                "critic_feedback must be non-empty when replan_required=True. "
                "A re-plan without feedback repeats the same failure."
            )
        return self

    @model_validator(mode="after")
    def failed_scene_ids_required_when_replan(self) -> "CriticResult":
        if self.replan_required and not self.failed_scene_ids:
            raise ValueError(
                "failed_scene_ids must be non-empty when replan_required=True."
            )
        return self

    @model_validator(mode="after")
    def replan_count_below_max(self) -> "CriticResult":
        if self.replan_count >= MAX_REPLANS:
            raise ValueError(
                f"replan_count={self.replan_count} has reached MAX_REPLANS={MAX_REPLANS}. "
                f"Set replan_required=False and accept best result."
            )
        return self