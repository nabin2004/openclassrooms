import json
import os
import litellm

import logging
from manimator.contracts.critic import CriticResult, DEFAULT_THRESHOLD

MODEL = os.getenv("CRITIC_MODEL", "gpt-4o-mini")  # needs vision support
log = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a strict visual critic for Manim animations.

You will be given:
- Scene IDs
- Rendered keyframes (images)

Evaluate:
1. Visual quality (layout, spacing, readability)
2. Semantic correctness (does it match expected intent)

Return JSON:

{
  "r_visual": float (0-1),
  "r_semantic": float (0-1),
  "failed_scene_ids": [int],
  "critic_feedback": ["string"]
}

Rules:
- Be critical, not generous
- If anything is unclear, reduce scores
- If major issues exist, mark scenes as failed
- Feedback must be specific and actionable
- No explanations outside JSON
- Most generated scenes are mediocre. Scores above 0.8 should be rare.
"""


async def critique_render(
    scene_ids: list[int],
    keyframe_paths: list[str],
    replan_count: int = 0,
) -> CriticResult:
    # STUB IMPLEMENTATION: Since render is a stub, we'll do a basic critique
    # without actual image analysis
    log.debug("Using stub critic implementation (no actual image analysis)")
    
    # For now, assume the generated scenes are acceptable
    # In a real implementation, this would analyze the rendered frames
    r_visual = 0.7  # Reasonable visual quality
    r_semantic = 0.8  # Good semantic match
    combined = round(0.5 * r_visual + 0.5 * r_semantic, 6)
    
    replan_required = combined < DEFAULT_THRESHOLD
    
    return CriticResult(
        replan_required=replan_required,
        failed_scene_ids=[],  
        r_visual=r_visual,
        r_semantic=r_semantic,
        combined_score=combined,
        critic_feedback=["Stub implementation - no actual analysis performed"],
        keyframe_paths=keyframe_paths,
        replan_count=replan_count,
    )