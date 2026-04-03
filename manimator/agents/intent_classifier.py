import asyncio

from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from amoeba.runtime import load_agent_env
from manimator.contracts.intent import IntentClassificationPayload, IntentResult

load_agent_env()

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

_intent_agent = Agent(
    name="intent_classifier",
    role=SYSTEM_PROMPT,
    model_env_key="INTENT_CLASSIFIER_MODEL",
    default_model="groq/llama-3.1-8b-instant",
    temperature=0.0,
    memory=StatelessMemoryAdapter(),
)


async def classify_intent(raw_query: str) -> IntentResult:
    _intent_agent.reset_history()
    payload = await _intent_agent.think_and_parse(
        f"Classify this query: {raw_query}",
        schema=IntentClassificationPayload,
        max_tokens=256,
    )
    result = payload.into_result(raw_query)
    print("Classify", result.model_dump())
    return result


if __name__ == "__main__":
    asyncio.run(classify_intent("What is a circle?"))
    asyncio.run(classify_intent("Teach me about the Multilayer perceptron?"))
