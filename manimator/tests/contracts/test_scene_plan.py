import pytest
from pydantic import ValidationError
from manimator.contracts.scene_plan import ScenePlan, SceneEntry, SceneClass, Budget, TransitionStyle


def valid_plan():
    return ScenePlan(
        scene_count=2,
        transition_style=TransitionStyle.FADE,
        scenes=[
            SceneEntry(id=0, title="Loss surface", scene_class=SceneClass.THREE_D, budget=Budget.MEDIUM, prerequisite_ids=[]),
            SceneEntry(id=1, title="Gradient step", scene_class=SceneClass.THREE_D, budget=Budget.LOW, prerequisite_ids=[0]),
        ]
    )


def test_valid_plan():
    plan = valid_plan()
    assert plan.scene_count == 2


def test_scene_count_mismatch():
    with pytest.raises(ValidationError, match="scene_count"):
        ScenePlan(scene_count=3, transition_style=TransitionStyle.CUT, scenes=[
            SceneEntry(id=0, title="Only one", scene_class=SceneClass.SCENE, budget=Budget.LOW, prerequisite_ids=[]),
        ])


def test_unknown_prerequisite():
    with pytest.raises(ValidationError, match="unknown prerequisite"):
        ScenePlan(scene_count=1, transition_style=TransitionStyle.CUT, scenes=[
            SceneEntry(id=0, title="Bad prereq", scene_class=SceneClass.SCENE, budget=Budget.LOW, prerequisite_ids=[99]),
        ])


def test_cycle_detection():
    with pytest.raises(ValidationError, match="Cycle"):
        ScenePlan(scene_count=2, transition_style=TransitionStyle.CUT, scenes=[
            SceneEntry(id=0, title="A", scene_class=SceneClass.SCENE, budget=Budget.LOW, prerequisite_ids=[1]),
            SceneEntry(id=1, title="B", scene_class=SceneClass.SCENE, budget=Budget.LOW, prerequisite_ids=[0]),
        ])


def test_scene_count_cap():
    with pytest.raises(ValidationError):
        ScenePlan(scene_count=7, transition_style=TransitionStyle.CUT, scenes=[
            SceneEntry(id=i, title=f"Scene {i}", scene_class=SceneClass.SCENE, budget=Budget.LOW, prerequisite_ids=[])
            for i in range(7)
        ])