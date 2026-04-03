import asyncio

from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from amoeba.observability import log_llm_event
from amoeba.runtime import load_agent_env
from manimator.contracts.intent import IntentClassificationPayload, IntentResult
from manimator.prompts.registry import get_intent_prompt

load_agent_env()

OUT_OF_SCOPE_TOPICS = [
    "biology", "heart", "blood", "anatomy", "chemistry", "physics experiments",
    "cooking", "history", "geography", "music", "art", "literature",
]

_ACTIVE_INTENT_PROMPT = get_intent_prompt()

_intent_agent = Agent(
    name=_ACTIVE_INTENT_PROMPT.name,
    role=_ACTIVE_INTENT_PROMPT.system,
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
    log_llm_event(
        "intent_classification",
        prompt_name=_ACTIVE_INTENT_PROMPT.name,
        prompt_version=_ACTIVE_INTENT_PROMPT.version,
        in_scope=result.in_scope,
        concept_type=result.concept_type.value,
        modality=result.modality.value,
        complexity=result.complexity,
    )
    return result


if __name__ == "__main__":
    asyncio.run(classify_intent("What is a circle?"))
    asyncio.run(classify_intent("Teach me about the Multilayer perceptron?"))
