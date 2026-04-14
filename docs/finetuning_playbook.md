# Finetuning exploration playbook (suggestions only)

Use this as lecture-facing notes, a personal checklist, or paste sections into an LLM when you design experiments. Nothing here is a mandate; tradeoffs depend on GPU budget, license constraints, and whether you optimize for **research velocity** or **production serving**.

---

## 1. Why start early (what your lecturer likely means)

- **Data and eval gaps** show up only when you try to train: label noise, distribution shift, metric gaming, and “looks good to humans but fails structurally” (very relevant for JSON/Manim-style pipelines in [STRATEGIC_ROADMAP.md](../STRATEGIC_ROADMAP.md)).
- **Serving mismatches** show up when you move from notebook weights to a real server: batching, KV cache memory, quantization, and tool-calling/JSON constraints.
- **Post-training RE** skills come from iterating on **SFT → preference optimization → (optional) lightweight RL** loops with tight offline metrics, not from picking a “final” model once.

---

## 2. Model suggestions (open weights, strong ecosystem “support”)

Interpret “support” as: Hugging Face checkpoints, active community, TRL/Unsloth compatibility, inference server support, and clear licensing/docs.

| Direction | Suggestion | Why it fits early tinkering / post-training |
|-----------|------------|-----------------------------------------------|
| **Default 8B-class workhorse** | **Meta Llama 3.1 8B Instruct** (or newer Llama 3.x instruct family you can legally access) | Excellent instruction baseline; huge cookbook of LoRA/QLoRA recipes; easy to compare against API baselines. Your roadmap already names this class. |
| **VRAM-friendly + strong coding/math** | **Qwen2.5-7B-Instruct** (or newer Qwen instruct in same tier) | Often strong JSON/structured behavior; good when 8B+Llama is tight on memory. Also referenced in your roadmap. |
| **European / Mistral ecosystem** | **Mistral Small / Ministral** or **Mixtral** (if you have GPU for MoE) | Good if you care about vendor-neutral European stacks; MoE is a separate serving lesson (memory + expert routing). |
| **Google open line** | **Gemma 2 9B IT** (or current Gemma instruct) | Solid tooling on HF; useful if your course standardizes on Kaggle/GCP. |
| **Smaller for ultra-fast iteration** | **3B–4B instruct models** (e.g. Qwen/Llama small instruct variants) | Lets you debug **data pipeline and eval** before burning GPU on 8B; limitation: behavior gap vs production target size. |

**Practical note:** For a **post-training RE** portfolio, pick **one 8B anchor model** and one **smaller** model. Run the *same* data and eval on both; your story becomes scaling and failure analysis, not chasing checkpoints.

---

## 3. Training stack suggestions (post-training–centric)

- **QLoRA / LoRA**: Start here (matches Phase 2 in [STRATEGIC_ROADMAP.md](../STRATEGIC_ROADMAP.md)). Learn rank, alpha, which modules to adapt, and catastrophic forgetting on held-out tasks.
- **Libraries (pick one primary, skim others)**:
  - **Hugging Face TRL**: `SFTTrainer`, DPO/ORPO trainers—good “research default” aligned with papers and HF models.
  - **Axolotl** or **Llama-Factory**: Fast config-driven iteration if YAML/config reproducibility matters for coursework.
  - **Unsloth** (optional): Speed/memory wins for LoRA on single GPUs; useful when iteration cycles are the bottleneck.
- **Alignment / preference learning (when SFT plateaus)**:
  - **DPO / IPO / ORPO** on pairs of outputs; learn limitations of noisy preferences and length bias early.
- **Evaluation** (invest early, not last):
  - Held-out **JSON schema validity**, task-specific **unit tests** (e.g. Manim AST checks if you codegen), plus a small **human rubric** set.
  - Optional **LLM-as-judge** only with calibration and known position bias.

---

## 4. Deployment and inference servers (what to try and when)

| Option | Best for | Tradeoffs / limitations to “tinker” with |
|--------|----------|-------------------------------------------|
| **vLLM** | Research and many production teams needing **fast iteration**, **OpenAI-compatible** APIs, continuous batching, good multi-GPU story | Operational complexity still real; advanced features vary by version; you learn PagedAttention and scheduling quirks. |
| **SGLang** | High-performance structured workloads, overlap-heavy serving | Newer moving target; excellent when batching + structured gen matter. |
| **Triton Inference Server** | **Enterprise** multi-model fleets, strict ops integration (Kubernetes, metrics, model repo layout) | Often paired with **TensorRT-LLM** or other backends; more moving parts—great if your goal includes “how big shops ship,” heavier for solo early tinkering. |
| **Text Generation Inference (TGI)** | Hugging Face–centric deployment | Straightforward for HF models; compare feature set vs vLLM for your use case. |
| **Ollama / llama.cpp** | Laptop CPU/GPU smoke tests, local demos | Not usually “data center serving,” but invaluable for **artifact size, quant formats, and on-device limits**. |

**Suggestion for your stated goals:** Use **vLLM or SGLang** while you iterate on **post-training**; add **Triton (+ TensorRT-LLM)** as a *second milestone* if you want deployment credibility for large orgs. Always mirror **the same quantization** (e.g. AWQ/GPTQ vs FP16) across train and serve when debugging quality regressions.

---

## 5. Limitations to expose on purpose (good early experiments)

- **Format compliance**: JSON / tool schemas break under greedy decoding; try temperature, constrained decoding, and “repair pass” data (your roadmap mentions repair loops).
- **Distribution shift**: train on one topic family, test on another; measure collapse and hallucinated APIs.
- **Quantization**: compare BF16/FP16 LoRA merge vs quantized inference; watch calibration-sensitive tasks.
- **Long context**: irrelevant context hurts smaller models first—good lesson for retrieval-augmented vs finetuned memory.
- **Preference optimization**: cheap wins, then **reward hacking**—teaches you why RLHF pipelines need constraints.

---

## 6. Copy-paste “master prompt” for experiment design

Use this with an assistant or as a template in your lab notebook:

```
You are helping me design an early post-training (SFT + optional DPO) experiment on a single GPU (specify: ___ GB).

Context:
- Goal: [e.g. structured ScenePlan JSON for an educational video pipeline]
- Base model candidates: [e.g. Llama-3.1-8B-Instruct vs Qwen2.5-7B-Instruct]
- Constraints: [license, no paid API for training labels, deadline ___]

Deliverables:
1) Pick a primary base model and a smaller cheap model for debugging; justify with ecosystem support (HF, TRL, inference servers).
2) Propose dataset format, train/val split, and 3 offline metrics that catch real failures (not BLEU).
3) Propose a minimal training config (LoRA rank, lr, epochs) and ablations worth 2–3 runs only.
4) Propose evaluation that includes “hard negatives” (edge cases) and schema validation.
5) Propose serving path: start with vLLM or SGLang; note when Triton+TRT-LLM would matter.
6) List the top 10 limitations I should expect and how to detect each from metrics or qualitative samples.

Assume I want to grow into a research engineer role focused on post-training, not pretraining.
```

---

## 7. Tie-in to this repository (optional framing)

Your [STRATEGIC_ROADMAP.md](../STRATEGIC_ROADMAP.md) already points to **director (decomposer/planner) first**, **QLoRA**, and **Llama-3.1-8B / Qwen2.5-7B**—that is a coherent story for coursework: smaller action space than full Manim codegen, clearer metrics, faster iteration.
