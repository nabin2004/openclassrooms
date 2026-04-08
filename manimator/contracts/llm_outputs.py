from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LLMObjectSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    type: str
    init_params: dict = Field(default_factory=dict)


class LLMAnimationSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    target: str | None = None
    run_time: float | None = None
    params: dict = Field(default_factory=dict)


class LLMCameraOp(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    phi: float | None = None
    theta: float | None = None
    zoom: float | None = None


class LLMPlannerPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    imports: list[str] = Field(default_factory=list)
    objects: list[LLMObjectSpec]
    animations: list[LLMAnimationSpec]
    camera_ops: list[LLMCameraOp] = Field(default_factory=list)
    voiceover_script: str | None = None


class LLMSceneEntryPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    title: str
    scene_class: str
    budget: str | None = None
    prerequisite_ids: list[int] = Field(default_factory=list)


class LLMScenePlanPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scene_count: int
    scenes: list[LLMSceneEntryPayload]
    transition_style: str
    total_duration_target: int | None = None

