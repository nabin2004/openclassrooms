## Knowledge Graph + Reasoning layer (pre-planning)

This doc proposes a **Semantic-Web-inspired layer** that sits *before* scene decomposition/planning.

Goal: make Manimator behave like it “knows what’s already taught” by querying a structured graph
instead of stuffing everything into prompts.

### Where it fits in the pipeline

```text
raw_query
  ↓
IntentResult (IR)
  ↓
ConceptGraph + LearnerState (KG layer)
  ↓
TeachingPlan (new IR)
  ↓
ScenePlan (IR)
  ↓
SceneSpec (IR)
  ↓
code / validate / render / critique / narrate
```

### Why do this?
- **Consistency**: prerequisites/dependencies are explicit, not “whatever the model remembers today”.
- **Reasoning**: compute “what is missing” deterministically (or with simple rules) before prompting.
- **Caching**: graph queries + IR snapshots give stable cache keys and reusability.
- **Training**: creates clean supervised slices (graph-query → plan) for finetuning/RL later.

### What we store
- **Concept graph**: topics as nodes, prerequisite edges, difficulty tags, alternative paths.
- **Learner state** (optional, per-user): what’s known, what’s weak, what was recently taught.
- **Teaching plan**: which concepts to cover, in what order, at what depth, and why.

### What we do *not* overdo (v0)
Do **not** start with heavy OWL tooling.
Start with a simple schema + deterministic reasoning in code.
Add SPARQL/RDF stores later if they earn their complexity.

### Files in this folder
- `ONTOLOGY.md`: the minimal ontology/schema to start with
- `TEACHING_PLAN_IR.md`: the proposed `TeachingPlan` IR (versioned contract)
- `REASONING.md`: query patterns + rules (missing prerequisites, alternative paths)
- `DEPLOYMENT.md`: how to store/query this locally now and how to host later

