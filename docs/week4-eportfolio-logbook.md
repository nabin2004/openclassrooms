# BCU E-Portfolios — Logbook (Markdown)

**Final Year Project — Nabin Oli**  
**Logbook — Final Year Individual Honors project**

---

## Week 4: Finetuning pipeline initialization and SFT dataset generation pipeline — Nabin Oli (23189629)

**Posted by** Nabin Oli on 19 April 2026 at 14:00  
**Last updated** 19 April 2026 at 14:30

*Disclaimer: The following links, especially GitHub links, may change or become unavailable over time due to ongoing development. The links provided reflect the progress at the time of writing.*

This week focused on **initializing the post-training / finetuning track** (tooling choices, reproducibility, and how training will connect to the existing Manimator IR pipeline) and on **standing up a supervised fine-tuning (SFT) dataset generation pipeline** so we can export per-stage **JSONL supervision files** from batch runs—aligned with Phase 1 Week 4 in the project roadmap (synthetic data → first training bundle).

### Supervisor’s suggestion (carried forward / refined)

- Study related work on **Manim-based video generators** driven by LLMs and collect **evaluation metrics** suitable for structured outputs (JSON plans, code, renders).
- **Start local fine-tuning** in a controlled way: anchor on one base model class, define train/val splits, and iterate on **data quality** before scaling GPU time.
- Continue work on **metrics for evaluating the Intermediate Representation** (schema validity, stage-wise success, and downstream render success).

### Deliverables and progress

#### Finetuning pipeline — initialization

- Captured a **lecture-facing finetuning playbook** (stack options, QLoRA/LoRA, TRL/Unsloth/Axolotl-style workflows, eval discipline) so experiments stay comparable as the project moves from API baselines to local weights.
- Aligned initialization work with the **strategic roadmap**: Phase 1 closes with a **training-ready export**; Phase 2 targets **local fine-tuning** (director/planner first), using the same JSONL shapes as batch exports.
- **Links:** [Finetuning playbook](https://github.com/nabin2004/openclassrooms/blob/main/docs/finetuning_playbook.md) | [Strategic roadmap (Phase 1–2)](https://github.com/nabin2004/openclassrooms/blob/main/STRATEGIC_ROADMAP.md)

#### SFT dataset generation pipeline (batch IR → JSONL)

- Used the **Manimator batch IR pipeline** to generate large prompt lists (**`querygen`**), run the **same contract-first pipeline** as interactive mode (**`runner`** with profiles such as through critic vs full delivery), and **export per-stage JSONL** for analysis or SFT.
- Documented end-to-end operation: pilot runs, resume semantics, concurrency, and export CLI—so dataset builds are **repeatable** and suitable for versioning (`batch-id`, manifests, IR under `outputs/runs/<run_id>/`).
- **Links:** [Batch IR README](https://github.com/nabin2004/openclassrooms/blob/main/manimator/batch/README.md) | [Batch export module](https://github.com/nabin2004/openclassrooms/blob/main/manimator/batch/export.py)

### Overall progress summary

- **Bridged research notes to executable workflow:** finetuning is no longer only a roadmap bullet—initialization is captured in-repo and tied to measurable exports.
- **Unblocked SFT data:** the batch runner + export path turns pipeline stages into **supervision examples** (per-stage JSONL) instead of one-off JSON in logs.
- **Next focus:** narrow the first **target stage** for LoRA/SFT (e.g. director vs planner), freeze a **schema_version** convention for training rows, and stand up a **minimal training run** on a small JSONL slice before scaling.

---

*This file is written for BCU E-Portfolio / Mahara-style logbook paste; adapt timestamps and links if your fork or branch differs.*
