## Deployment options for the KG + TeachingPlan layer

This section covers:
- where the concept graph lives
- how to query it
- how to deploy it later when you have users

### Phase 0 (local, fastest)
**Storage**: checked-in JSON files (or a small SQLite file) in repo, versioned by git.

- Pros: simplest; works offline; perfect for reproducible IR + dataset generation.
- Cons: no multi-user writes; no SPARQL; limited concurrency.

Recommended approach:
- `manimator/data/concept_graph.json` (future)
- include `graph_version` in `TeachingPlan.provenance`

### Phase 1 (local graph library)
**Storage**: RDF in-memory using `rdflib` (or NetworkX).

- Pros: still simple; can serialize to Turtle; can later migrate to a SPARQL store.
- Cons: more dependencies; still mostly single-process.

### Phase 2 (hosted SPARQL endpoint)
**Storage**: a triple store (examples):
- Apache Jena Fuseki
- GraphDB
- Blazegraph (legacy but still used)

**API**:
- SPARQL endpoint for read queries
- optional write API if you store learner state centrally

Pros:
- multi-user; scalable; real semantic querying; inference support (store-dependent).
Cons:
- operational overhead; auth; deployment complexity.

### Learner state deployment
Options:
- store learner state as JSON in your app DB (Postgres/SQLite) and only use KG for concept graph
- store learner state as named graphs in the triple store (more “pure” semantic web)

### Docs deployment (your “wiki”)
You already have:
- GitHub Wiki pages for IR

Recommended:
- mirror this KG documentation into the same Wiki:
  - `Manimator-KG` (overview)
  - `Manimator-KG-Ontology`
  - `Manimator-TeachingPlan-IR`
  - `Manimator-KG-Deployment`

### Production checklist (later)
- Auth (who can read/write learner state)
- Versioning & migrations (graph schema and IR schema)
- Observability (log reasoning decisions + graph version + query latency)
- Caching policy (when IR can be reused, invalidation rules)

