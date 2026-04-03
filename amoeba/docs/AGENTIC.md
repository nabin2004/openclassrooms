# Amoeba agentic primitives

Amoeba is evolving into a small library of reusable pieces for LLM-backed agents. This document describes the stable, dependency-facing helpers. Higher-level orchestration (graphs, ticks, tools) lives under `amoeba.core` and `amoeba.graph` and will grow over time.

## Environment

- **`amoeba.runtime.load_agent_env`** — Call once at process startup (or from each agent module) to load `.env`. The helper is idempotent so multiple agents can call it without redundant work.

## LLM calls

- **`amoeba.core.responses.completion_message_text`** — Normalizes a LiteLLM / OpenAI-style chat completion response to a single string. Handles `None` content and simple list-shaped multimodal payloads.

- **`amoeba.core.litellm_chat.acompletion_system_user`** — Async helper for the common pattern: one system message, one user message, then return text. Raises `RuntimeError` on empty content; pass `error_context="Planner"` (or similar) so logs and failures name the caller. Extra keyword arguments are forwarded to `litellm.acompletion` (e.g. provider-specific options).

- **`amoeba.core.llm.LLMClient`** — Stateful client with model from an env key or default, optional chat history, and memory hooks via `Agent`. It uses `completion_message_text` internally so `content` is never assumed to be a plain string.

## Model output cleanup

- **`amoeba.utils.strip_fences`** — Strips leading markdown fences (e.g. ` ```json `) from model output before `json.loads`. Language tags recognized include `json`, `python`, `py`, `js`, and `typescript`.

- **`amoeba.utils.safe_parse_json`** — Combines `strip_fences` with `json.loads` and raises `ValueError` with the cleaned snippet on failure.

## Using Amoeba from application code

Application packages (for example **manimator**) should depend on the workspace package `amoeba` and import these primitives directly. Domain-specific agents keep their prompts and parsing logic local; shared wiring stays in Amoeba.
