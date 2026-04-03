# Agent Testing Guide

This directory provides comprehensive tools for testing individual Manimator agents.

## Quick Start

### Using Makefile (Recommended)

```bash
# Sync dependencies once per environment update
make sync

# Test individual agents
make test-intent        # Test intent classifier
make test-decomposer    # Test scene decomposer  
make test-planner       # Test scene planner
make test-codegen       # Test code generator
make test-validator     # Test validator
make test-repair       # Test repair agent
make test-render        # Test render agent
make test-critic        # Test critic agent

# Test all agents
make test-all           # Test all agents sequentially
make quick-test         # Quick pass/fail test of all agents

# Run full pipeline
make test-pipeline      # Run complete pipeline

# Utilities
make setup             # Setup test environment
make clean             # Clean test outputs
make help              # Show all commands
```

### Using Interactive Test Script

```bash
# Test specific agent with custom input
uv run python test_agents.py --agent intent --query "Explain neural networks visually"

# Test other agents
uv run python test_agents.py --agent decomposer
uv run python test_agents.py --agent planner
uv run python test_agents.py --agent codegen
uv run python test_agents.py --agent validator
uv run python test_agents.py --agent repair
uv run python test_agents.py --agent render
uv run python test_agents.py --agent critic

# Test full pipeline
uv run python test_agents.py --agent pipeline

# Save results to JSON
uv run python test_agents.py --agent intent --save
```

## Agent Testing Details

### 1. Intent Classifier (`make test-intent`)
- **Input**: Text query
- **Output**: IntentResult (concept type, modality, complexity)
- **Test Case**: "Explain linear regression visually with a scatter plot and a line of best fit."
- **Log**: `logs/test_intent.log`

### 2. Scene Decomposer (`make test-decomposer`)
- **Input**: IntentResult from classifier
- **Output**: ScenePlan (list of scenes with budgets)
- **Test Case**: Math/Graph/Complexity 2 intent
- **Log**: `logs/test_decomposer.log`

### 3. Scene Planner (`make test-planner`)
- **Input**: SceneEntry (single scene)
- **Output**: SceneSpec (detailed animation plan)
- **Test Case**: "Introduction to Scatter Plot" with low budget
- **Log**: `logs/test_planner.log`

### 4. Code Generator (`make test-codegen`)
- **Input**: SceneSpec from planner
- **Output**: Python Manim code
- **Test Case**: Scene with axes and dot animations
- **Log**: `logs/test_codegen.log`

### 5. Validator (`make test-validator`)
- **Input**: Generated code + SceneSpec
- **Output**: ValidationResult (pass/fail + error details)
- **Test Case**: Valid Manim scene code
- **Log**: `logs/test_validator.log`

### 6. Repair Agent (`make test-repair`)
- **Input**: ValidationResult with errors
- **Output**: Repaired Python code
- **Test Case**: Code with undefined variable error
- **Log**: `logs/test_repair.log`

### 7. Render Agent (`make test-render`)
- **Input**: Generated codes for all scenes
- **Output**: Video file paths
- **Test Case**: 2 mock scenes
- **Log**: `logs/test_render.log`

### 8. Critic Agent (`make test-critic`)
- **Input**: Scene IDs + video paths
- **Output**: CriticResult (quality scores)
- **Test Case**: 3 mock video paths
- **Log**: `logs/test_critic.log`

## Development Workflow

### Rigorous Testing
1. **Unit Testing**: Test each agent individually
   ```bash
   make test-all
   ```

2. **Integration Testing**: Test agent interactions
   ```bash
   uv run python test_agents.py --agent pipeline
   ```

3. **Pipeline Testing**: Full end-to-end test
   ```bash
   make test-pipeline
   ```

### Debugging Failed Tests
- Check individual log files in `logs/` directory
- Use `uv run python test_agents.py --agent <name> --save` to get JSON output
- Compare expected vs actual outputs

### Continuous Testing
```bash
# Watch for changes and re-test
watch make test-all

# Or test specific agent during development
watch make test-codegen
```

## File Structure

```
OpenClassrooms/
├── Makefile              # Primary testing interface
├── test_agents.py        # Interactive testing script
├── AGENT_TESTING.md     # This guide
├── logs/                # Test output logs
├── test_outputs/         # Test render outputs
└── outputs/             # Pipeline outputs
```

## Tips for Effective Testing

1. **Start Small**: Test agents individually before integration
2. **Use Custom Inputs**: Modify test cases in `test_agents.py`
3. **Check Logs**: Each test writes detailed logs
4. **Save Results**: Use `--save` flag for JSON output
5. **Clean Between Tests**: Use `make clean` to reset state
6. **Iterate**: Fix issues and re-test immediately

## Example Development Session

```bash
# Setup environment
make sync
make setup

# Test agent you're working on
make test-codegen

# Check logs
cat logs/test_codegen.log

# Run quick test to verify no regressions
make quick-test

# Test full pipeline
make test-pipeline

# Clean up
make clean
```

This testing framework enables rigorous, isolated testing of each agent for enhanced development experience.
