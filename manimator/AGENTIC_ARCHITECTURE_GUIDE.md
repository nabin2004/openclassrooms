# Manimator agentic architecture: lock-in guide

This document is for **freezing an architecture** so you can move on to **synthetic data generation** and **local fine-tuning** without re-litigating tools, “how many agents,” and skills every week.

It is written against the current codebase: LangGraph pipeline in `manimator/pipeline/graph.py`, shared state in `manimator/pipeline/state.py`, and the **director-like** behavior in `manimator/agents/scene_decomposer.py` (topic → scenes) plus `manimator/agents/planner.py` (scene → structured spec).

---

## 1. Vocabulary you actually need


| Term                     | What it means in practice                                                                           | In Manimator today                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Agent**                | Any LLM call with a fixed role, prompt, and I/O contract                                            | `classify_intent`, `decompose_scenes`, `plan_scene`, `generate_code`, …            |
| **Node**                 | One step in a **deterministic** control-flow graph                                                  | LangGraph nodes: `classify` → `decompose` → `plan` → …                             |
| **Tool / function call** | The model **decides** to invoke something at runtime (search, run code, DB)                         | Mostly **not** used here; you use **structured outputs** (JSON → Pydantic) instead |
| **Skill / rule file**    | Human-written instructions **outside** the model weights (e.g. Cursor `SKILL.md`, repo `AGENTS.md`) | Your long `SYSTEM_PROMPT` strings + repo conventions                               |
| **Contract**             | Schema + validation boundary between stages                                                         | `manimator/contracts/`* (`ScenePlan`, `SceneSpec`, `ValidationResult`, …)          |


**Key insight:** You do **not** have to pick “agents **or** tools **or** skills.” They stack:

- **Contracts** = stability and trainability (what you log as labels).
- **Nodes** = reliability (order of operations, retries, caps).
- **Tools** = optional; add only when the model must branch on **fresh** external facts mid-run.
- **Skills / prompts** = cheap iteration before you freeze data formats.

---

## 2. What you already have (good news)

You already implemented the pattern most production agent systems wish they had:

1. **Narrow roles per call** (intent, director/decomposer, planner, codegen, validator, repair, critic).
2. **Explicit state** carried through the graph (`PipelineState`).
3. **Loops with budgets** (`MAX_RETRIES`, `MAX_REPLANS`) instead of unbounded “agent chat.”

The **director** is not a single class name; it is the **decomposition + planning** chain:

- **Strategic director:** `scene_decomposer.py` — *what* scenes exist and in what order.
- **Tactical director:** `planner.py` — *how* each scene is staged (objects, beats, voiceover).

That split is **correct** for education video: different context windows, different failure modes, different training data slices.

---

## 3. One question that resolves “how many agents?”

Ask only this:

> **Does this step need a *different* system prompt, a *different* model, or a *different* training dataset slice?**

- **Yes** → separate agent (separate module + env var for model).
- **No** → keep it inside an existing node (or a pure function, no LLM).

Examples:

- Merging decomposer + planner into **one** giant agent **reduces** files but **increases** confusion in the model and **muddies** fine-tuning data (bad for your goal).
- Splitting codegen into five micro-agents for “imports,” “animations,” … **multiplies** failure points unless each slice has a **stable JSON contract** and you **need** different models.

**Default recommendation for you:** keep **roughly** the current number of **roles**, even if you rename or regroup files. The graph length is not your enemy; **unclear contracts** are.

---

## 4. Pathways (pick one as “north star” for v1)

### Pathway A — “Frozen pipeline” (best default for synthetic data + local FT)

**Idea:** Treat the system as a **compiler**: fixed DAG, structured intermediate representations (IR), bounded repair loops.

- **Pros:** Easy to log `(input, stage_output)` pairs; reproducible; matches your code today.
- **Cons:** Less flexible for open-ended “research assistant” behavior (you do not need that for Manimator v1).

**Lock-in checklist:**

- Every stage output is JSON-serializable or has a stable `.model_dump()`.
- One log line (or JSONL row) per stage per run id.
- Model IDs are config (env), not hardcoded in business logic.

**When to add tools:** only for **validator**-adjacent steps (e.g. run Manim in sandbox, parse stderr) — you already run Manim in `node_render`; extending **machine-checkable** signals is high value, not more LLM agents.

---

### Pathway B — “Single orchestrator + tools” (OpenClaw-style mental model)

**Idea:** One top-level model with **function calling**; tools = `plan_scene`, `run_manim`, `search_docs`, etc.

- **Pros:** Feels simple conceptually; good for **exploratory** UIs.
- **Cons:** Harder to get **clean training data** (branchy traces, implicit state); harder to test; easier to hide bugs behind “the model decided.”

**Verdict for your stated goal:** use this for a **future chat UX**, not as the core batch pipeline, unless you are willing to invest heavily in trace normalization.

---

### Pathway C — “Hierarchical multi-agent” (planner / workers / critic)

**Idea:** Explicit “manager” agent delegates to workers (storyboard, layout, code, audio).

- **Pros:** Matches large-team mental models; can parallelize.
- **Cons:** Coordination overhead; duplicated context; **more** data fragmentation unless you standardize IR.

**Verdict:** only worth it when you **parallelize** across scenes **and** each worker has a **tight** contract. Your graph already parallelizes **cheaply** at the **data** level (per-scene lists) without extra “manager” LLM calls.

---

### Pathway D — “Hybrid” (recommended evolution)

**Idea:** Keep **Pathway A** as the spine. Add **tools** only at **edges**:


| Edge          | Tool-like behavior                             | Why                          |
| ------------- | ---------------------------------------------- | ---------------------------- |
| After codegen | Deterministic lint / AST check / Manim dry-run | Cuts repair iterations       |
| After render  | FFmpeg probes, duration checks                 | Grounds the critic in facts  |
| Optional      | Retrieval over Manim docs / your style guide   | Only if prompts get unwieldy |


No new **LLM agents** required for most of this—scripts and libraries are enough.

---

## 5. Cutting-edge without chaos (practical robustness)

These items matter more than buzzwords:

1. **Contract-first:** If `SceneSpec` changes, version it (`schema_version` field) so old traces remain usable.
2. **Golden tests:** Small fixed inputs where expected JSON shape is asserted (you already have contract tests; extend with **one** end-to-end “tiny topic” pipeline test when feasible).
3. **Telemetry:** `run_id`, `stage`, `latency_ms`, `model`, `token_usage` (if available), `success`, `error_class` — store raw prompts/outputs **only** if your threat model allows.
4. **Budgets:** You already cap retries/replans; document **why** each cap exists next to `MAX_RETRIES` / `MAX_REPLANS`.
5. **Separation of “creative” vs “executable”:** Director/planner can be florid; codegen should be constrained to **allowed APIs** and patterns (your prompts already move this way).

---

## 6. Synthetic data for local fine-tuning (what to actually record)

**Goal:** datasets that teach a **local** model to **imitate one stage** at a time, not to imitate the whole internet.

### 6.1 High-value dataset slices (in order)


| Slice        | Input (X)                                 | Target (Y)          | Notes                                                              |
| ------------ | ----------------------------------------- | ------------------- | ------------------------------------------------------------------ |
| **Intent**   | `raw_query`                               | `IntentResult` JSON | Teaches scope gating                                               |
| **Director** | `IntentResult` + style constraints        | `ScenePlan` JSON    | Teaches pedagogy / ordering                                        |
| **Planner**  | `SceneEntry` (+ optional critic feedback) | `SceneSpec` JSON    | Teaches visual grammar                                             |
| **Codegen**  | `SceneSpec`                               | Manim Python        | Hardest; needs validator stderr as extra context for “repair” data |
| **Repair**   | `(bad_code, ValidationResult)`            | `fixed_code`        | Very valuable if stderr is structured                              |


### 6.2 Minimal JSONL schema (example)

One object per **stage completion** (not per token):

```json
{
  "run_id": "uuid",
  "stage": "plan_scene",
  "schema_version": 1,
  "model_serving": "groq/llama-3.1-8b-instant",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "output": { }
}
```

`output` is the parsed contract (or raw string for code). Add `validation` / `critic` fields when recording repair loops.

### 6.3 Local FT strategy (short)

- **Start with director + planner JSON** (smaller action space, cleaner metrics).
- Add **codegen** once validation noise is **structured** (error codes, failing line ranges).
- Prefer **LoRA / QLoRA** on a single base model per slice first; merge only after you see metric lift.

---

## 7. Executable 7-day lock plan

Use this literally as a checklist; adjust days if part-time.


| Day   | Action                                                                                                                      |
| ----- | --------------------------------------------------------------------------------------------------------------------------- |
| **1** | Write a one-page **IR diagram**: `IntentResult` → `ScenePlan` → `SceneSpec` → code. Put it in the same folder as this file. |
| **2** | Declare **Pathway A + D** as v1 north star; explicitly defer Pathway B chat orchestrator.                                   |
| **3** | Add **run_id** + **stage logging** (JSONL append). No fancy UI.                                                             |
| **4** | Freeze **director** prompt + `ScenePlan` schema; bump `schema_version` if you change fields.                                |
| **5** | Generate **N=50** synthetic runs on diverse CS topics; spot-check failure modes.                                            |
| **6** | Define **acceptance metrics** per stage (e.g. % JSON parse success, % validation pass).                                     |
| **7** | Export first **training bundle** (JSONL + README of license / PII policy).                                                  |


---

## 8. Anti-patterns (save future you)

- **More agents to fix bad prompts** — fix the contract and the prompt first.
- **Tools everywhere** — each tool needs tests and mock fixtures; you pay forever.
- **One mega-prompt “do everything”** — destroys label quality for FT.
- **Skipping versioning** — you will poison datasets when schemas drift.
- **Training on full traces without stage segmentation** — local models learn confusion, not roles.

---

## 9. One-sentence recommendation

**Lock Pathway A (compiler DAG + contracts) as your architecture, keep the decomposer/planner split as your “director,” add tool-like deterministic checks at codegen/render boundaries, and build synthetic data per stage with versioned JSONL—defer single orchestrator + heavy tool use until you have traces worth the complexity.**

When this file disagrees with impulse (“I need more agents”), re-read **section 3** and **section 8**.