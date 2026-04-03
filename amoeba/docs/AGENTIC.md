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

## Using Amoeba from application code

Application packages (for example **manimator**) should depend on the workspace package `amoeba` and import these primitives directly. Domain-specific agents keep their prompts and parsing logic local; shared wiring stays in Amoeba.
