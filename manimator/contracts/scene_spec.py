from pydantic import BaseModel, Field, model_validator
from manimator.contracts.scene_plan import Budget, SceneClass

ANIMATION_BUDGET_CAP: dict[Budget, int] = {
    Budget.LOW: 999,  # Effectively unlimited
    Budget.MEDIUM: 999,  # Effectively unlimited
    Budget.HIGH: 999,  # Effectively unlimited
}

MANIM_CLASS_WHITELIST = {
    "Scene", "ThreeDScene", "MovingCameraScene", "ZoomedScene",
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
    # Additional classes for advanced animations
    "ValueTracker", "ParametricFunction", "FunctionGraph", "ImplicitFunction",
    "Wait", "Indicate", "FocusOn", "IndicateTransform", "Flash", "Circumscribe",
    "MoveAlongPath", "AnimationGroup", "Succession", "LaggedStart", "LaggedEnd",
    "FadeTransformPieces", "TransformMatchingShapes", "TransformMatchingTex",
    "CounterclockwiseTransform", "ClockwiseTransform", "CyclicReplace",
    "UpdateFromAlpha", "UpdateFromFunc", "FixedInFrameMObject", "ThreeDVMobject",
    "Sphere", "Cube", "Prism", "Cylinder", "Cone", "Torus", "Surface",
    "DotCloud", "PointCloud", "LabeledDot", "LabeledArrow", "CurvedArrow",
    "CurvedDoubleArrow", "Angle", "RightAngle", "Elbow", "DoubleArrow",
    "VectorField", "StreamLines", "ComplexFunction", "ComplexPlane",
    "BraceLabel", " Brace", "SurroundingRectangle", "BackgroundRectangle",
    "Crosshair", "ScreenRectangle", "LabeledLine", "TangentLine",
    "CoordinateSystem", "NumberLine", "UnitInterval", "DecimalNumber",
    "Integer", "Variable", "MathTable", "BarChart", "Axes", "ThreeDAxes",
    "NumberPlane", "ComplexPlane", "PolarPlane", "ImageMobject", "SVGMobject",
    "Code", "Paragraph", "MarkupText", "BulletedList", "OrderedList",
    "TipableVMobject", "VMobject", "Mobject", "Animation", "Wait",
    # Animation methods
    "animate", "play", "wait", "add", "remove", "bring_to_front", "bring_to_back",
    "move_to", "next_to", "shift", "scale", "rotate", "flip", "stretch", "apply_function",
    "become", "match_height", "match_width", "match_depth", "center", "align_to",
    "set_color", "set_fill", "set_stroke", "set_opacity", "set_sheen", "set_gloss",
    "fade", "darken", "lighten", "invert_colors", "save_state", "restore",
}


class MobjectSpec(BaseModel):
    name: str 
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
    target: str | None = None # must match a MobjectSpec.name
    run_time: float = Field(default=1.0, ge=0.1, le=10.0)
    params: dict = Field(default_factory=dict)


class CameraOp(BaseModel):
    type: str = Field(pattern=r"^(move_camera|set_camera_orientation|begin_ambient_rotation)$")
    phi: float | None = None
    theta: float | None = None
    zoom: float | None = Field(default=None, ge=0.1, le=5.0)


class SceneSpec(BaseModel):
    schema_version: str = "1.0.0"
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
        """Validate that animation targets exist in objects or are valid method calls"""
        object_names = {obj.name for obj in self.objects}
        
        for anim in self.animations:
            target = anim.target
            
            # Handle Wait animations which don't need a target
            if target is None or target.lower() in ("none", "null"):
                continue
            
            # Handle special camera targets
            if target.startswith("camera.") or target == "camera":
                continue
            
            # Handle method calls like "b_tracker.set_value"
            if "." in target:
                base_target = target.split(".")[0]
                if base_target not in object_names:
                    raise ValueError(
                        f"Animation target '{target}' has base object '{base_target}' which is not defined in objects. "
                        f"Defined objects: {object_names}"
                    )
            else:
                # Handle array indexing like "latency_array[9]" or slicing "latency_array[0:8]"
                if "[" in target and "]" in target:
                    base_target = target.split("[")[0]
                    if base_target not in object_names:
                        raise ValueError(
                            f"Animation target '{target}' has base object '{base_target}' which is not defined in objects. "
                            f"Defined objects: {object_names}"
                        )
                else:
                    # Direct object reference
                    if target not in object_names:
                        raise ValueError(
                            f"Animation target '{target}' is not defined in objects. "
                            f"Defined objects: {object_names}"
                        )
        return self