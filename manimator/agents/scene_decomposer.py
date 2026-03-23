from manimator.contracts.intent import IntentResult
from manimator.contracts.scene_plan import Budget, SceneClass, SceneEntry, ScenePlan, TransitionStyle


async def decompose_scenes(intent: IntentResult) -> ScenePlan:
    # STUB — hardcoded 2-scene plan
    return ScenePlan(
        scene_count=2,
        transition_style=TransitionStyle.FADE,
        total_duration_target=30,
        scenes=[
            SceneEntry(
                id=0,
                title="Introduction",
                scene_class=SceneClass.SCENE,
                budget=Budget.MEDIUM,
                prerequisite_ids=[],
            ),
            SceneEntry(
                id=1,
                title="Main concept",
                scene_class=SceneClass.SCENE,
                budget=Budget.HIGH,
                prerequisite_ids=[0],
            ),
        ],
    )