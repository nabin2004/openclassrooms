from pydantic import BaseModel, Field, model_validator
from manimator.contracts.scene_plan import Budget, SceneClass

ANIMATION_BUDGET_CAP: dict[Budget, int] = {
    Budget.LOW: 3,
    Budget.MEDIUM: 6,
    Budget.HIGH: 10,
}

MANIM_CLASS_WHITELIST = {
    "Scene", "ThreeDScene", "MovingCameraScene", "ZoomedScene", "GraphScene",
    "Axes", "ThreeDAxes", "NumberPlane", "Surface", "ParametricFunction",
    "Circle", "Square", "Rectangle", "Triangle", "Polygon", "RegularPolygon",
    "Arrow", "Vector", "Line", "DashedLine", "Dot", "Cross",
    "Text", "Tex", "MathTex", "Title", "BulletedList",
    "VGroup", "HGroup", "Group",
    "Create", "Write", "FadeIn", "FadeOut", "Transform", "ReplacementTransform",
    "MoveToTarget", "Rotate", "ScaleInPlace", "GrowFromCenter",
    "DrawBorderThenFill", "ShowCreation", "Uncreate",
    "BLUE", "RED", "GREEN", "YELLOW", "WHITE", "BLACK", "ORANGE", "PURPLE",
    "UP", "DOWN", "LEFT", "RIGHT", "IN", "OUT", "ORIGIN",
}


class MobjectSpec(BaseModel):
    name: str = Field(pattern=r"^[a-z_][a-z0-9_]*$")  # valid Python identifier
    type: str
    init_params: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def type_in_whitelist(self) -> "MobjectSpec":
        if self.type not in MANIM_CLASS_WHITELIST:
            raise ValueError(
                f"'{self.type}' is not in the Manim class whitelist. "
                f"Add it explicitly if it's a valid Manim class."
            )
        return self


class AnimationSpec(BaseModel):
    type: str
    target: str  # must match a MobjectSpec.name
    run_time: float = Field(default=1.0, ge=0.1, le=10.0)
    params: dict = Field(default_factory=dict)


class CameraOp(BaseModel):
    type: str = Field(pattern=r"^(move_camera|set_camera_orientation|begin_ambient_rotation)$")
    phi: float | None = None
    theta: float | None = None
    zoom: float | None = Field(default=None, ge=0.1, le=5.0)


class SceneSpec(BaseModel):
    scene_id: int = Field(ge=0)
    class_name: str = Field(pattern=r"^[A-Z][a-zA-Z0-9]*$")  # PascalCase
    scene_class: SceneClass
    imports: list[str] = Field(min_length=1)
    objects: list[MobjectSpec] = Field(min_length=1)
    animations: list[AnimationSpec] = Field(min_length=1)
    camera_ops: list[CameraOp] = Field(default_factory=list)
    voiceover_script: str | None = None
    budget: Budget

    @model_validator(mode="after")
    def animation_count_within_budget(self) -> "SceneSpec":
        cap = ANIMATION_BUDGET_CAP[self.budget]
        if len(self.animations) > cap:
            raise ValueError(
                f"Budget '{self.budget}' allows max {cap} animations, "
                f"got {len(self.animations)}"
            )
        return self

    @model_validator(mode="after")
    def camera_ops_only_for_3d_or_moving(self) -> "SceneSpec":
        allowed = {SceneClass.THREE_D, SceneClass.MOVING_CAMERA}
        if self.camera_ops and self.scene_class not in allowed:
            raise ValueError(
                f"camera_ops are only valid for ThreeDScene or MovingCameraScene, "
                f"got {self.scene_class}"
            )
        return self

    @model_validator(mode="after")
    def animation_targets_exist(self) -> "SceneSpec":
        object_names = {obj.name for obj in self.objects}
        for anim in self.animations:
            if anim.target not in object_names:
                raise ValueError(
                    f"Animation targets '{anim.target}' which is not defined in objects. "
                    f"Defined objects: {object_names}"
                )
        return self