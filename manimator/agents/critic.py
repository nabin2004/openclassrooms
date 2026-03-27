import json
import os
from dotenv import load_dotenv
import litellm

from manimator.contracts.critic import CriticResult, DEFAULT_THRESHOLD

load_dotenv()

MODEL = os.getenv("CRITIC_MODEL", "gpt-4o-mini")  # needs vision support


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

    # Prepare multimodal input
    content = [
        {"type": "text", "text": json.dumps({"scene_ids": scene_ids})}
    ]

    for path in keyframe_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"file://{path}"}
        })

    response = await litellm.acompletion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()

    # reuse your helper if you want
    if raw.startswith("```"):
        raw = raw.split("```")[1].replace("json", "").strip()

    try:
        data = json.loads(raw)

        r_visual = data["r_visual"]
        r_semantic = data["r_semantic"]
        combined = round(0.5 * r_visual + 0.5 * r_semantic, 6)

        replan_required = combined < DEFAULT_THRESHOLD

        return CriticResult(
            replan_required=replan_required,
            failed_scene_ids=data.get("failed_scene_ids", []),
            r_visual=r_visual,
            r_semantic=r_semantic,
            combined_score=combined,
            critic_feedback=data.get("critic_feedback", []),
            keyframe_paths=keyframe_paths,
            replan_count=replan_count,
        )

    except Exception as e:
        raise ValueError(f"Failed to parse CriticResult: {e}\nRaw:\n{raw}")