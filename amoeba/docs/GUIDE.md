# Amoeba usage guide

This document explains how to adopt Amoeba in an application, recommended patterns, sharp edges, and areas that are still experimental. For a short API cheat sheet, see [AGENTIC.md](AGENTIC.md).

## What Amoeba is (today)

Amoeba is a **small, dependency-first layer** for LLM-backed agents: response normalization, LiteLLM calls, optional `Agent` + memory hooks, JSON cleanup, and building blocks for tools and tick loops. It is **not** a full orchestration framework yet; app code (prompts, domain models, pipelines) stays in your package while shared mechanics live here.

## Installation

In a **uv workspace** (as in this repo), add `amoeba` to your package dependencies and pin it to the workspace:

```toml
# your-package/pyproject.toml
dependencies = [
    "amoeba",
    # ...
]

[tool.uv.sources]
amoeba = { workspace = true }
```

Then:

```bash
uv lock
uv sync --all-packages
```

Amoeba declares `litellm`, `pydantic`, and `python-dotenv`. Your app must still configure provider API keys (for example in `.env`) the way LiteLLM expects.

## Getting started

### 1. Environment

Call **`amoeba.runtime.load_agent_env()`** once at process startup (or from each agent module). It is **idempotent**; duplicate calls are harmless.

### 2. One-shot HTTP-style call (no `Agent`)

When you only need system + user messages and a string back (or you parse JSON yourself):

```python
from amoeba.core.litellm_chat import acompletion_system_user

text = await acompletion_system_user(
    model="groq/llama-3.1-8b-instant",
    system="You are a helpful assistant.",
    user="Summarize: ...",
    temperature=0.2,
    error_context="My feature name",
)
```

Pass **`error_context`** so failures name the caller. Extra keyword arguments are forwarded to **`litellm.acompletion`** (provider-specific flags, etc.).

### 3. `Agent` + structured output

When you want **system prompt as `role`**, optional **memory recall**, **chat history**, and **Pydantic** parsing of JSON:

```python
from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from pydantic import BaseModel

class MyPayload(BaseModel):
    answer: str
    score: float

agent = Agent(
    name="my_agent",
    role="You return JSON with fields answer (str) and score (float).",
    model_env_key="MY_MODEL",
    default_model="gpt-4o-mini",
    temperature=0.0,
    memory=StatelessMemoryAdapter(),  # see “Memory” below
)

async def run_once(user_text: str) -> MyPayload:
    agent.reset_history()
    return await agent.think_and_parse(user_text, schema=MyPayload, max_tokens=512)
```

Use a **separate** Pydantic model for **LLM output** when your domain model includes fields the model never returns (for example `raw_query`, `run_id`), then map into your domain type.

## Choosing a pattern

| Need | Prefer |
|------|--------|
| Single request, no history, no memory | **`acompletion_system_user`** |
| Same, but you already use `LLMClient` | **`LLMClient.call`** |
| Multi-turn in one session, memory, snapshots | **`Agent`** with default **`DagestanAdapter()`** |
| Each request independent (classifiers, extractors) | **`Agent`** + **`StatelessMemoryAdapter`** + **`reset_history()`** per call |
| Raw completion object | **`litellm.acompletion`** + **`completion_message_text`** |

## Best practices

1. **Structured outputs** — Prefer Pydantic models and **`think_and_parse`** / **`safe_parse_json`** so fence-stripped JSON is validated in one place.

2. **Model selection** — **`LLMClient`** reads **`os.environ`** when constructed. Changing env vars at runtime does not update an existing client; create a new **`Agent`** or restart the process.

3. **Prompts live in the app** — Keep system prompts and domain vocabulary in your application package; Amoeba should stay generic.

4. **LiteLLM extras** — Use **`**kwargs`** on **`think`** / **`LLMClient.call`** / **`acompletion_system_user`** for parameters your provider needs, rather than forking Amoeba.

5. **Irreversible side effects** — For tools that mutate the world, use **`amoeba.core.tool.Tool`** with **`Reversibility.IRREVERSIBLE`** and a **`confidence_threshold`**, and route execution through **`ToolRegistry.execute`** so gating stays centralized.

6. **Testing** — Mock **`litellm.acompletion`** or inject a thin wrapper if you need deterministic tests; Amoeba does not ship a fake LLM.

## Gotchas

### Chat history grows every `think()`

Each **`think()`** appends user and assistant messages to **`_history`** and sends them on the next call. For **stateless** endpoints, call **`reset_history()`** before each logical request (and see memory below).

### Memory recall changes the system prompt

With the default **`DagestanAdapter`**, **`recall()`** may inject prior context into the system string. That is intentional for continuity but surprising if you expected a pure single-shot call. Use **`StatelessMemoryAdapter`** when recall and snapshots must not affect behavior.

### `Agent.as_node()` and async

**`as_node()`** uses **`asyncio.get_event_loop().run_until_complete(self.run(state))`**. That pattern is **fragile** if an event loop is already running (Jupyter, some web servers, other async frameworks). Prefer **`await agent.run(state)`** from async code instead of **`as_node()`**.

### In-memory backend is minimal

**`InMemoryBackend`** supports snapshots and latest-recall fallback enough for **`Agent.think()`** to run. It does **not** implement semantic **`search_chunks`** (that path returns empty). Do not assume embedding-based recall works until a real backend is wired.

### `DagestanLiveBackend` and `connect()`

**`DagestanAdapter.connect()`** is reserved for a future live Dagestan client. The placeholder type exists so imports resolve; **live behavior is not implemented**.

### JSON errors

**`safe_parse_json`** raises **`ValueError`** with context, not **`json.JSONDecodeError`** directly. Catch **`ValueError`** or inspect the message when handling parse failures.

### `ToolRegistry` default argument

**`ToolRegistry.__init__(tools=[])`** uses a shared default list if callers mutate that list (classic Python footgun). Prefer **`ToolRegistry(tools=[...])`** with a fresh list or **`ToolRegistry()`** then **`register()`**.

### Package layout

Installable code lives under **`src/amoeba/`**. Do not add **`__init__.py`** at the **repository root** **`amoeba/`** folder; that has shadowed the real package in the past.

## Experimental and future-facing

These APIs exist for direction and experiments; treat them as **unstable** unless noted otherwise.

- **`amoeba.core.tick.Ticker`** — **`tick()`** is suitable for driving **`agent.run(state)`** once per step. **`run_at(hz=...)`** is a **fixed-rate loop** intended for embodied / continuous scenarios; exercise it carefully (timing, cancellation, backpressure).

- **`amoeba.core.tool`** — **`Tool`**, **`@action`**, **`ToolRegistry`**, and **`to_llm_schema()`** are early; schema shape may evolve to match stricter OpenAI / LiteLLM tool formats.

- **`amoeba.graph.*`** — Module files may be **empty placeholders**; no stable graph API is committed yet.

- **`amoeba.envs.*`** and **`amoeba.core.perception`** — Placeholders for environment and perception loops.

- **Full Dagestan integration** — Memory interfaces describe an eventual three-layer model (temporal / embedding / graph). Only the in-memory path is meaningfully exercised today.

When you depend on experimental pieces, **pin Amoeba to a commit or version** and expect small breaking changes until the API stabilizes.

## See also

- [AGENTIC.md](AGENTIC.md) — concise list of primitives and imports.
- Workspace **`AGENTS.md`** (repo root) — project-wide Python and `uv` conventions for this monorepo.
