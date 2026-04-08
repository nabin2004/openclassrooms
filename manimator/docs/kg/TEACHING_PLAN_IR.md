## TeachingPlan IR (new proposed contract)

This IR sits between:
- `IntentResult` (what the user asked)
- `ScenePlan` (how we will break it into scenes)

It is the output of the KG + reasoning layer.

### Why a separate IR?
`ScenePlan` is optimized for video production (scene count, transitions, scene titles).
`TeachingPlan` is optimized for pedagogy and reasoning (concept dependencies, what to skip/expand).

### Proposed schema (v0)

```json
{
  "schema_version": "1.0.0",
  "topic": "Transformer architecture",
  "target_concepts": ["transformer", "transformer.attention"],
  "assumed_known": ["vector", "matrix_multiply"],
  "missing_prerequisites": ["dot_product", "softmax"],
  "weak_concepts": ["softmax"],
  "learning_path": [
    {
      "concept_id": "dot_product",
      "depth": "brief",
      "why": "required for attention scoring",
      "prereqs": ["vector"]
    },
    {
      "concept_id": "softmax",
      "depth": "full",
      "why": "user weak on it; crucial normalization step",
      "prereqs": ["exp", "sum"]
    },
    {
      "concept_id": "transformer.attention",
      "depth": "full",
      "why": "core of the request",
      "prereqs": ["dot_product", "softmax"]
    }
  ],
  "constraints": {
    "max_scenes": 8,
    "style": "3b1b",
    "avoid": ["history_of_transformers"]
  },
  "provenance": {
    "graph_version": "concept_graph@2026-04-08",
    "reasoner": "v0-deterministic",
    "signals": {
      "user_profile": true,
      "dry_run": false
    }
  }
}
```

### How it connects to existing IR
- Inputs:
  - `IntentResult` (`manimator/contracts/intent.py`)
  - `ConceptGraph` (new dataset / store)
  - optional `LearnerState` (per-user)
- Outputs:
  - feeds `scene_decomposer` as *constraints + ordered teaching targets* (instead of only raw query)

### Logging + persistence
When implemented, `TeachingPlan` should be written into the IR bundle:
- `outputs/runs/<run_id>/ir/teaching_plan.json`

That makes “this is the recipe we used to teach Transformers” explicit and replayable.

