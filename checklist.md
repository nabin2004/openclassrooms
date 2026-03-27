# Project Checklist

## Already Implemented
- [x] Initial schema design discussion and requirements gathering
- [x] Identified 5 key contracts and their critical fields
- [x] Documented schema invariants and rationale for:
  - [x] `retry_count` / `replan_count` pattern
  - [x] Importance of `critic_feedback`
  - [x] Necessity of `original_spec` in repair agent
  - [x] Use of `failed_scene_ids` in critic result

## Next Tasks

### Schema & Model Implementation
- [ ] Write detailed schema definitions for all 5 contracts
- [ ] Implement Pydantic models for each contract
  - [ ] Encode field types and constraints
  - [ ] Add custom validators for invariants (e.g., `critic_feedback` logic)

### Validation & Enforcement
- [ ] Integrate schema validation at every component entry point
- [ ] Ensure all incoming data is validated using Pydantic models

### Testing
- [ ] Write unit tests for each Pydantic model
  - [ ] Test valid and invalid cases, especially edge cases for invariants

### Documentation
- [ ] Document each schema and its enforcement logic
- [ ] Provide usage examples and error handling guidelines
