import pytest
from pydantic import ValidationError
from manimator.contracts.scene_spec import SceneSpec, MobjectSpec, AnimationSpec, CameraOp
from manimator.contracts.scene_plan import SceneClass, Budget


def valid_spec():
    return SceneSpec(
        scene_id=0,
        class_name="LossSurface",
        scene_class=SceneClass.THREE_D,
        budget=Budget.MEDIUM,
        imports=["ThreeDScene", "Surface", "Axes"],
        objects=[MobjectSpec(name="axes", type="ThreeDAxes")],
        animations=[AnimationSpec(type="Create", target="axes")],
        camera_ops=[CameraOp(type="move_camera", phi=75.0, theta=-45.0)],
    )


def test_valid_spec():
    spec = valid_spec()
    assert spec.class_name == "LossSurface"


def test_budget_animation_cap():
    with pytest.raises(ValidationError, match="Budget"):
        SceneSpec(
            scene_id=0, class_name="TooMany", scene_class=SceneClass.SCENE,
            budget=Budget.LOW,  # max 3
            imports=["Scene"],
            objects=[MobjectSpec(name="c", type="Circle")],
            animations=[AnimationSpec(type="Create", target="c") for _ in range(4)],
        )


def test_camera_ops_rejected_on_base_scene():
    with pytest.raises(ValidationError, match="camera_ops"):
        SceneSpec(
            scene_id=0, class_name="Flat", scene_class=SceneClass.SCENE,
            budget=Budget.LOW, imports=["Scene"],
            objects=[MobjectSpec(name="c", type="Circle")],
            animations=[AnimationSpec(type="Create", target="c")],
            camera_ops=[CameraOp(type="move_camera", phi=45.0)],
        )


def test_animation_target_must_exist():
    with pytest.raises(ValidationError, match="targets"):
        SceneSpec(
            scene_id=0, class_name="BadTarget", scene_class=SceneClass.SCENE,
            budget=Budget.LOW, imports=["Scene"],
            objects=[MobjectSpec(name="circle", type="Circle")],
            animations=[AnimationSpec(type="Create", target="nonexistent")],
        )


def test_unknown_manim_class_rejected():
    with pytest.raises(ValidationError, match="whitelist"):
        MobjectSpec(name="thing", type="GradientArrow")