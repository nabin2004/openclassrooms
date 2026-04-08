## Reasoning / query patterns (v0)

Start with deterministic logic (graph traversal + simple rules). Add SPARQL later if needed.

### Primary queries

#### 1) Missing prerequisites for a target concept
Input:
- target concept `T`
- learner `knows` set

Algorithm:
1. Compute `Prereqs(T)` as transitive closure over `requires` edges.
2. Return `Prereqs(T) - knows`.

Output:
- list of missing concept ids (optionally topologically ordered)

#### 2) Weak prerequisites
Input:
- learner `weak_on` scores
- `Prereqs(T)`

Return:
- the subset of prerequisites that are weak below threshold (e.g. < 0.6)

#### 3) Choose a path (multi-path concepts)
If a concept has multiple valid prerequisite “paths”, choose based on:
- learner knows calculus → pick calculus path
- learner weak in calculus → choose geometric/intuition path

### Rule examples (human-written, code-implemented)

- **Rule: implied knowledge**
  - If learner knows `derivative`, assume they know `function` with high confidence.
- **Rule: avoid repetition**
  - If a concept was taught in the last N minutes, don’t re-teach unless it is weak.
- **Rule: depth selection**
  - missing + core prerequisite → `depth=brief` or `full` depending on `difficulty` and learner weakness.

### Output: TeachingPlan
The reasoner should produce `TeachingPlan` IR:
- `missing_prerequisites`
- `weak_concepts`
- `learning_path` (ordered)
- `provenance` (graph version, rule set version)

### When to add SPARQL
SPARQL becomes worth it when:
- multiple graph sources need federation
- you want ad-hoc analytical queries (coverage, prerequisite cycles, curriculum gaps)
- you want to host a shared graph for many clients

