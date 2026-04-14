# BCU E-Portfolios
Profile picture for Nabin Oli
Search for people
Final Year Project - Nabin Oli
by Nabin Oli
Logbook Final Year Individual Honors project

Individual Honors Project

**Week 3: Pipeline Robustness, IR Snapshots, and Amoeba Abstractions**
Posted by Nabin Oli on 9 April 2026 at 15:30

This week focused on stabilizing the agentic pipeline, building out the Amoeba library for LLM operations, implementing robust Intermediate Representation (IR) snapshots for reproducibility, and adding observability across the generation lifecycle.

**Supervisor's suggestion:**

1. Study other related papers on Manim based video generator using the LLMs and look for evaluation metrics.

2. Start with finetuning the local LLM.

3. Work on metrics for evaluating the Intermediate representation.


**Deliverables and Progress:**

**Amoeba Library Development (LLM Abstractions)**:
   - Fixed agent packaging and built robust error-handling hierarchies (`AmoebaError`, `LLMError`, `StructuredOutputError`) for safe LLM operations.
   - Introduced a `run_subprocess` utility in Amoeba with exceptions sharing timeouts and logging to replace ad-hoc module calls.
   - Implemented Agent observability, token tracing hooks (`log_trace_summary`), and standardized the `LLMResponse` models for consistency.
   - *Link*: [Amoeba Package Source](https://github.com/nabin2004/openclassrooms/tree/main/amoeba/src/amoeba) | [Amoeba Docs](https://github.com/nabin2004/openclassrooms/tree/main/amoeba/docs)

**Manimator Pipeline Resilience and Logging**:
   - Unified error handling across the system with a typed hierarchy under `manimator.exceptions.py`.
   - Refactored the runtime to isolate outputs per run instead of a global state. The system now creates per-run directories (`outputs/runs/<run_id>/`) with segregated code, renders, audio, and traces.
   - Implemented global `configure_logging`, sharing trace IDs and correlating pipeline events to observability metrics.
   - *Link*: [Exceptions Module](https://github.com/nabin2004/openclassrooms/blob/main/manimator/exceptions.py) | [Manimator Pipeline Details](https://github.com/nabin2004/openclassrooms/tree/main/manimator/pipeline)

**Structured Pydantic Returns and Prompt Registry**:
   - Replaced hand-rolled JSON parsing in the Planner and Scene Decomposer with Amoeba's `Agent.think_and_parse` relying on permissive LLM Pydantic contracts.
   - Set up versioned prompt registries (`manimator/prompts/`) for managing instructions dynamically for the scene planner, decomposer, and code repair agents.
   - *Link*: [Prompts Registry](https://github.com/nabin2004/openclassrooms/tree/main/manimator/prompts) | [LLM Outputs Contracts](https://github.com/nabin2004/openclassrooms/blob/main/manimator/contracts/llm_outputs.py)

**Intermediate Representation (IR) and Knowledge Graph (KG) Specs**:
   - Developed a `write_ir_bundle` function to persist run snapshots as machine-readable JSON files, capturing intent, plans, code generation, and critic scores for analysis.
   - Documented the architecture for the semantic Knowledge Graph (KG) and ontological teaching plans to guide future integrations.
   - *Link*: [IR Serializer](https://github.com/nabin2004/openclassrooms/blob/main/manimator/ir.py) | [IR and KG Documentation](https://github.com/nabin2004/openclassrooms/tree/main/manimator/docs) | [GitHub Wiki](https://github.com/nabin2004/openclassrooms/wiki)

**Audio Muxing and TTS Model Integration**:
   - Integrated KittenTTS to enable automated narration generation from natural-pace text-to-speech modeling.
   - Implemented audio multiplexing capabilities (`mux.py`) to properly mix generated speech and conform visuals.
   - *Link*: [Audio Module](https://github.com/nabin2004/openclassrooms/tree/main/manimator/audio)

**Overall progress summary**
- Hardened pipeline execution environment (per-run directories, structured timeouts).
- Extracted and solidified core LLM abstractions into the standalone `Amoeba` library.
- Migrated manual LLM JSON parsing to strict Pydantic structures for deterministic plan/spec validation.
- Improved reproducibility dramatically by persisting unified Intermediate Representation (IR) runs containing complete execution traces and code artifacts.
- Integrated KittenTTS text-to-speech modeling and audio-visual multiplexing to implement a real narration overlay.
