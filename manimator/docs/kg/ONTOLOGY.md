## Minimal ontology / schema (v0)

This is a pragmatic “Semantic Web–style” schema for teaching concepts.

You can serialize it as:
- JSON (easy)
- Turtle/RDF (later, if you adopt rdflib/SPARQL)

### Core entities

#### Concept
Represents a teachable unit.

Required fields:
- `id`: stable identifier (string slug), e.g. `transformer.attention`
- `label`: human-friendly name, e.g. `Self-Attention`

Optional fields:
- `description`: brief definition
- `difficulty`: `easy|medium|hard` (or numeric)
- `tags`: list of strings (`nlp`, `deep_learning`, `linear_algebra`)
- `canonical_order`: integer hint for ordering within a chapter/track
- `sources`: links or references (docs, papers)

#### Prerequisite edge
Directed edge: `ConceptA requires ConceptB`

Representations:
- triple form (RDF-ish): `:A :requires :B`
- JSON edge: `{ "from": "A", "type": "requires", "to": "B" }`

Optional edge attributes:
- `strength`: `hard|soft` (hard prerequisite vs recommended)
- `reason`: short text

#### Alternative paths
Some topics can be taught via different prerequisite sets.

Represent as:
- `:GradientDescent :hasPath :CalculusPath`
- `:GradientDescent :hasPath :GeometryPath`

In JSON:
- `paths`: list of `{ path_id, requires: [...], description }`

### Learner state (optional per-user graph)

Minimal:
- `knows(concept_id, confidence)`
- `weak_on(concept_id, score)`
- `last_taught(concept_id, ts)`

RDF-ish:
```ttl
:User123 :knows :Limit .
:User123 :weakOn :Derivative .
```

JSON:
```json
{
  "user_id": "User123",
  "knows": {"limit": 0.9, "function": 0.8},
  "weak_on": {"derivative": 0.3},
  "recent": ["limit", "function"]
}
```

### Minimal “Transformer chapter” example (Turtle-ish)
```ttl
:Transformer :requires :SequenceModeling .
:SequenceModeling :requires :RNN .
:Transformer :requires :Attention .
:Attention :requires :DotProduct .
:DotProduct :requires :Vector .
```

### Versioning
Treat this schema as **data-contract**:
- version the dataset format (e.g. `concept_graph.schema_version = "1.0.0"`)
- keep `Concept.id` stable (it’s your primary key for caching and datasets)

