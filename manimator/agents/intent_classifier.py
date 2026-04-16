import os
import asyncio

from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from amoeba.exceptions import JSONParseError, LLMError, StructuredOutputError
from amoeba.observability import log_llm_event, new_trace_id
from amoeba.observability.tracing import log_trace_summary
from amoeba.runtime import load_agent_env
from manimator.contracts.intent import (
    ConceptType,
    IntentClassificationPayload,
    IntentResult,
    Modality,
)
from manimator.agents.json_llm import response_format_json_object
from manimator.observability.metrics import append_metrics_jsonl
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


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _dry_run_result(raw_query: str) -> IntentResult:
    """Deterministic path for CI / pipeline debugging (no LLM)."""
    q = raw_query.lower()
    oos_kw = (
        "heart", "blood", "cook", "pasta", "biology", "anatomy",
        "geography", "music", "literature",
    )
    in_scope = not any(k in q for k in oos_kw)
    if in_scope:
        return IntentResult(
            in_scope=True,
            raw_query=raw_query,
            concept_type=ConceptType.MATH,
            modality=Modality.TWO_D,
            complexity=2,
            reject_reason=None,
            confidence=1.0,
        )
    return IntentResult(
        in_scope=False,
        raw_query=raw_query,
        concept_type=ConceptType.MATH,
        modality=Modality.TWO_D,
        complexity=1,
        reject_reason="dry-run heuristic: query matched out-of-scope keywords",
        confidence=1.0,
    )


async def _intent_think_parse_with_retries(
    *,
    user_msg: str,
    model: str | None,
    trace_id: str,
) -> IntentClassificationPayload:
    """
    Retry transient empty responses and malformed JSON on the same model
    (``INTENT_TRANSIENT_RETRIES``, default 1 → up to 2 attempts).
    """
    retries = max(0, int(os.getenv("INTENT_TRANSIENT_RETRIES", "1")))
    extra = response_format_json_object(disable_env_var="INTENT_DISABLE_JSON_MODE")
    last: BaseException | None = None
    for attempt in range(retries + 1):
        _intent_agent.reset_history()
        kwargs: dict = {"max_tokens": 256, **extra}
        if model:
            kwargs["model"] = model
        try:
            return await _intent_agent.think_and_parse(
                user_msg,
                schema=IntentClassificationPayload,
                **kwargs,
            )
        except (LLMError, JSONParseError, StructuredOutputError) as e:
            last = e
            if attempt >= retries:
                raise
            delay = min(5.0, 0.4 * (2**attempt))
            log_llm_event(
                "intent_classification.transient_retry",
                trace_id=trace_id,
                attempt=attempt + 1,
                max_attempts=retries + 1,
                delay_s=delay,
                error=str(e),
                model=model or os.getenv("INTENT_CLASSIFIER_MODEL", ""),
            )
            await asyncio.sleep(delay)
    assert last is not None
    raise last


def _tokens_total(tokens: dict | None) -> int | None:
    if not tokens:
        return None
    t = tokens.get("total_tokens")
    if t is not None:
        return int(t)
    p = tokens.get("prompt_tokens")
    c = tokens.get("completion_tokens")
    if p is not None and c is not None:
        return int(p) + int(c)
    return None


async def classify_intent(raw_query: str) -> IntentResult:
    trace_id = new_trace_id()
    prompt = _ACTIVE_INTENT_PROMPT
    user_msg = f"Classify this query: {raw_query}"
    fallback = os.getenv("INTENT_CLASSIFIER_FALLBACK_MODEL", "").strip() or None

    if _truthy_env("MANIMATOR_DRY_RUN"):
        result = _dry_run_result(raw_query)
        log_trace_summary(
            event="intent_classification",
            trace_id=trace_id,
            prompt_version=prompt.version,
            prompt_name=prompt.name,
            input_text=raw_query,
            output=result.model_dump(),
            latency_ms=0.0,
            model="dry_run",
            dry_run=True,
        )
        append_metrics_jsonl(
            {
                "event": "intent_classification",
                "trace_id": trace_id,
                "prompt_version": prompt.version,
                "ok": True,
                "dry_run": True,
                "in_scope": result.in_scope,
            }
        )
        return result

    first_error: BaseException | None = None
    try:
        payload = await _intent_think_parse_with_retries(
            user_msg=user_msg,
            model=None,
            trace_id=trace_id,
        )
    except (LLMError, JSONParseError, StructuredOutputError) as e:
        first_error = e
        if not fallback:
            lr = _intent_agent.last_llm_response
            log_trace_summary(
                event="intent_classification",
                trace_id=trace_id,
                prompt_version=prompt.version,
                prompt_name=prompt.name,
                input_text=raw_query,
                error=str(e),
                tokens=lr.tokens if lr else None,
                latency_ms=lr.latency_ms if lr else None,
                model=lr.model if lr else None,
                cost=lr.cost if lr else None,
            )
            append_metrics_jsonl(
                {
                    "event": "intent_classification",
                    "trace_id": trace_id,
                    "prompt_version": prompt.version,
                    "ok": False,
                    "error": str(e),
                }
            )
            raise
        log_llm_event(
            "intent_classification.fallback",
            trace_id=trace_id,
            fallback_model=fallback,
            error=str(e),
        )
        try:
            payload = await _intent_think_parse_with_retries(
                user_msg=user_msg,
                model=fallback,
                trace_id=trace_id,
            )
        except (LLMError, JSONParseError, StructuredOutputError) as e2:
            lr = _intent_agent.last_llm_response
            log_trace_summary(
                event="intent_classification",
                trace_id=trace_id,
                prompt_version=prompt.version,
                prompt_name=prompt.name,
                input_text=raw_query,
                error=str(e2),
                used_fallback=True,
                tokens=lr.tokens if lr else None,
                latency_ms=lr.latency_ms if lr else None,
                model=lr.model if lr else None,
                cost=lr.cost if lr else None,
            )
            append_metrics_jsonl(
                {
                    "event": "intent_classification",
                    "trace_id": trace_id,
                    "prompt_version": prompt.version,
                    "ok": False,
                    "used_fallback": True,
                    "error": str(e2),
                }
            )
            raise

    result = payload.into_result(raw_query)

    lr = _intent_agent.last_llm_response
    log_llm_event(
        "intent_classification",
        prompt_name=prompt.name,
        prompt_version=prompt.version,
        trace_id=trace_id,
        in_scope=result.in_scope,
        concept_type=result.concept_type.value,
        modality=result.modality.value,
        complexity=result.complexity,
        used_fallback=first_error is not None,
    )
    log_trace_summary(
        event="intent_classification",
        trace_id=trace_id,
        prompt_version=prompt.version,
        prompt_name=prompt.name,
        input_text=raw_query,
        output=result.model_dump(),
        tokens=lr.tokens if lr else None,
        latency_ms=lr.latency_ms if lr else None,
        model=lr.model if lr else None,
        cost=lr.cost if lr else None,
        used_fallback=first_error is not None,
    )
    append_metrics_jsonl(
        {
            "event": "intent_classification",
            "trace_id": trace_id,
            "prompt_version": prompt.version,
            "ok": True,
            "in_scope": result.in_scope,
            "latency_ms": lr.latency_ms if lr else None,
            "model": lr.model if lr else None,
            "tokens_total": _tokens_total(lr.tokens if lr else None),
            "used_fallback": first_error is not None,
        }
    )
    return result


if __name__ == "__main__":
    asyncio.run(classify_intent("What is a circle?"))
    asyncio.run(classify_intent("Teach me about the Multilayer perceptron?"))
