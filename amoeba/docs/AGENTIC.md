# Amoeba agentic primitives

For installation, patterns, best practices, gotchas, and experimental modules, see **[GUIDE.md](GUIDE.md)**.

This page is a **short API reference** for stable, dependency-facing helpers. Higher-level orchestration (graphs, ticks, tools) lives under `amoeba.core` and `amoeba.graph` and will grow over time.

## Environment

- **`amoeba.runtime.load_agent_env`** — Call once at process startup (or from each agent module) to load `.env`. The helper is idempotent so multiple agents can call it without redundant work.

## LLM calls

- **`amoeba.core.responses.completion_message_text`** — Normalizes a LiteLLM / OpenAI-style chat completion response to a single string. Handles `None` content and simple list-shaped multimodal payloads.

- **`amoeba.core.litellm_chat.acompletion_system_user`** — Async helper for the common pattern: one system message, one user message, then return text. Raises `RuntimeError` on empty content; pass `error_context="Planner"` (or similar) so logs and failures name the caller. Extra keyword arguments are forwarded to `litellm.acompletion` (e.g. provider-specific options).

- **`amoeba.core.llm.LLMClient`** — Stateful client with model from an env key or default. `call()` accepts `max_tokens` and forwards extra kwargs to LiteLLM. Uses `completion_message_text` internally.

- **`amoeba.core.agent.Agent`** — `role` is the system prompt; `think(user)` runs one turn (memory recall, LLM, snapshot, history). `think_and_parse` uses `safe_parse_json` and a Pydantic schema. For **stateless** classifiers, pass `memory=StatelessMemoryAdapter()` and call `reset_history()` before each request so prior turns are not sent to the model.

## Model output cleanup

- **`amoeba.utils.strip_fences`** — Strips leading markdown fences (e.g. ` ```json `) from model output before `json.loads`. Language tags recognized include `json`, `python`, `py`, `js`, and `typescript`.

- **`amoeba.utils.safe_parse_json`** — Combines `strip_fences` with `json.loads` and raises `ValueError` with the cleaned snippet on failure.

## Errors and observability

- **`amoeba.exceptions`** — `AmoebaError` base with `context`, `retryable`, and `user_message`. LLM failures map to `LLMError` / `LLMTimeoutError` / `LLMRateLimitError` / `LLMResponseError`. Parsing: `JSONParseError`, `StructuredOutputError`, `ConfigurationError`. Use **`exc.format_detail()`** for log-friendly dumps.
- **`amoeba.observability`** — `get_logger`, `log_llm_event`, `log_structured`, trace helpers `get_trace_id` / `set_trace_id` / `new_trace_id` (contextvar, safe across async tasks).
- **`amoeba.observability.tracing.log_trace_summary`** — One JSON log line per logical request (`trace_id`, `prompt_version`, `input`, `output`, `tokens`, `latency_ms`, `model`, `cost`, `error`). Logger **`amoeba.trace`**.
- **`amoeba.core.safe_acompletion.acompletion_safe`** — Single entry for `litellm.acompletion`: optional **`timeout`**, **`max_total_tokens`**, **`require_non_empty_text`**, returns **`LLMResponse`** (`text`, **`tokens`**, **`latency_ms`**, **`model`**, **`cost`**, **`raw`**). Alias **`LLMCallResult`**. Used by **`LLMClient`** and **`acompletion_system_user`**.
- **`amoeba.core.retry.async_retry_llm`** — Retries only **retryable** errors (default: rate limit + timeout) with exponential backoff.
- **`amoeba.core.result.Result`** — Optional `ok` / `value` / `error` for pipelines that should not always raise.

## Using Amoeba from application code

Application packages (for example **manimator**) should depend on the workspace package `amoeba` and import these primitives directly. Domain-specific agents keep their prompts and parsing logic local; shared wiring stays in Amoeba.

Catch **`AmoebaError`** (or specific subclasses) at API boundaries and map **`user_message`** for clients; log **`format_detail()`** or structured fields for operators.
