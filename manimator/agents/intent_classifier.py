import json
import os
from dotenv import load_dotenv
import litellm
from manimator.contracts.intent import ConceptType, IntentResult, Modality
from manimator.manim_utils import strip_markdown_code_blocks
load_dotenv()

MODEL = os.getenv("INTENT_CLASSIFIER_MODEL", "groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are an intent classifier for an AI math animation system.
The system can ONLY animate topics in: mathematics, computer science, and AI/ML.

Given a user query, classify it and return a JSON object with exactly these fields:
{
    "in_scope": true or false,
    "concept_type": one of "math", "cs", "ai", "mixed",
    "modality": one of "2d", "3d", "graph", "mixed",
    "complexity": integer 1-5,
    "reject_reason": null or string explaining why out of scope
}

Complexity guide:
1 = single concept (what is a circle)
2 = simple process (how does binary search work)
3 = multi-step concept (gradient descent, recursion)
4 = complex system (transformer attention, dynamic programming)
5 = multi-concept proof or derivation

Modality guide:
2d = flat animations, graphs, text
3d = 3D surfaces, spatial concepts
graph = network/tree/graph structures
mixed = combination needed

Return ONLY the JSON object. No explanation, no markdown, no extra text.
"""


OUT_OF_SCOPE_TOPICS = [
    "biology", "heart", "blood", "anatomy", "chemistry", "physics experiments",
    "cooking", "history", "geography", "music", "art", "literature",
]


async def classify_intent(raw_query: str) -> IntentResult:
    response = await litellm.acompletion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Classify this query: {raw_query}"},
        ],
        temperature=0.0,
        max_tokens=256,
    )

    raw = response.choices[0].message.content.strip()
    print("Classify", raw)

    # # Strip markdown code blocks if model wraps response
    # if raw.startswith("```"):
    #     raw = raw.split("```")[1]
    #     if raw.startswith("json"):
    #         raw = raw[4:]
    # raw = raw.strip()
    raw = strip_markdown_code_blocks(raw)

    data = json.loads(raw)

    return IntentResult(
        in_scope=data["in_scope"],
        raw_query=raw_query,
        concept_type=ConceptType(data["concept_type"]),
        modality=Modality(data["modality"]),
        complexity=int(data["complexity"]),
        reject_reason=data.get("reject_reason"),
        confidence=1.0,
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(classify_intent("What is a circle?"))
    asyncio.run(classify_intent("Teach me about the Multilayer perceptron?"))

