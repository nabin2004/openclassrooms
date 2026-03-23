from manimator.contracts.critic import CriticResult


async def critique_render(
    scene_ids: list[int],
    keyframe_paths: list[str],
    replan_count: int = 0,
) -> CriticResult:
    # STUB: always passes with high scores
    return CriticResult(
        replan_required=False,
        failed_scene_ids=[],
        r_visual=0.90,
        r_semantic=0.90,
        combined_score=0.90,
        critic_feedback=[],
        keyframe_paths=keyframe_paths,
        replan_count=replan_count,
    )