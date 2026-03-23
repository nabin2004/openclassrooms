from manimator.contracts.scene_plan import SceneEntry
from manimator.contracts.scene_spec import AnimationSpec, MobjectSpec, SceneSpec


async def plan_scene(scene: SceneEntry, feedback: str | None = None) -> SceneSpec:
    # STUB: hardcoded valid scene spec
    return SceneSpec(
        scene_id=scene.id,
        class_name=scene.title.replace(" ", ""),
        scene_class=scene.scene_class,
        budget=scene.budget,
        imports=["Scene", "Circle", "Create"],
        objects=[MobjectSpec(name="circle", type="Circle")],
        animations=[AnimationSpec(type="Create", target="circle")],
    )