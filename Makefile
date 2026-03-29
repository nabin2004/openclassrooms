# Manimator Agent Testing Makefile
# Run individual agents for rigorous testing

.PHONY: help test-intent test-decomposer test-planner test-codegen test-validator test-repair test-render test-critic test-all clean

# Default target
help:
	@echo "Manimator Agent Testing Commands:"
	@echo ""
	@echo "Individual Agent Tests:"
	@echo "  make test-intent      - Test intent classifier agent"
	@echo "  make test-decomposer  - Test scene decomposer agent"
	@echo "  make test-planner     - Test scene planner agent"
	@echo "  make test-codegen     - Test code generator agent"
	@echo "  make test-validator   - Test validator agent"
	@echo "  make test-repair     - Test repair agent"
	@echo "  make test-render     - Test render agent (stub)"
	@echo "  make test-critic     - Test critic agent (stub)"
	@echo ""
	@echo "Pipeline Tests:"
	@echo "  make test-all        - Test all agents in sequence"
	@echo "  make test-pipeline   - Run full pipeline"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean           - Clean test outputs"
	@echo "  make setup           - Setup test environment"

# Setup test environment
setup:
	@echo "Setting up test environment..."
	mkdir -p test_outputs
	mkdir -p logs
	@echo "Environment ready"

# Test Intent Classifier
test-intent:
	@echo "Testing Intent Classifier Agent..."
	python manimator/agents/intent_classifier.py > logs/test_intent.log 2>&1
	@echo "Intent test completed. Check logs/test_intent.log"

# Test Scene Decomposer  
test-decomposer:
	@echo "Testing Scene Decomposer Agent..."
	python manimator/agents/scene_decomposer.py > logs/test_decomposer.log 2>&1
	@echo "Decomposer test completed. Check logs/test_decomposer.log"

# Test Scene Planner
test-planner:
	@echo "Testing Scene Planner Agent..."
	python test_planner.py > logs/test_planner.log 2>&1
	@echo "Planner test completed. Check logs/test_planner.log"

# Test Code Generator
test-codegen:
	@echo "Testing Code Generator Agent..."
	python test_codegen.py > logs/test_codegen.log 2>&1
	@echo "Codegen test completed. Check logs/test_codegen.log"

# Test Validator
test-validator:
	@echo "Testing Validator Agent..."
	python test_validator.py > logs/test_validator.log 2>&1
	@echo "Validator test completed. Check logs/test_validator.log"

# Test Repair Agent
test-repair:
	@echo "Testing Repair Agent..."
	python test_repair.py > logs/test_repair.log 2>&1
	@echo "Repair test completed. Check logs/test_repair.log"

# Test Render Agent (Stub)
test-render:
	@echo "Testing Render Agent (Stub)..."
	python test_render.py > logs/test_render.log 2>&1
	@echo "Render test completed. Check logs/test_render.log"

# Test Critic Agent (Stub)
test-critic:
	@echo "Testing Critic Agent (Stub)..."
	python test_critic.py > logs/test_critic.log 2>&1
	@echo "Critic test completed. Check logs/test_critic.log"

# Test All Agents in Sequence
test-all: setup test-intent test-decomposer test-planner test-codegen test-validator test-repair test-render test-critic
	@echo ""
	@echo "All agent tests completed!"
	@echo "Check individual log files in logs/ directory:"
	@ls -la logs/

# Run Full Pipeline
test-pipeline:
	@echo "Running full pipeline..."
	python manimator/main.py
	@echo "Pipeline test completed. Check outputs/ directory for results."

# Clean test outputs
clean:
	@echo "Cleaning test outputs..."
	rm -rf test_outputs/
	rm -rf logs/
	rm -rf outputs/
	@echo "Clean completed."

# Quick test - run all agents with minimal output
quick-test: setup
	@echo "Running quick agent tests..."
	@make test-intent > /dev/null 2>&1 && echo "✅ Intent: PASS" || echo "❌ Intent: FAIL"
	@make test-decomposer > /dev/null 2>&1 && echo "✅ Decomposer: PASS" || echo "❌ Decomposer: FAIL"
	@make test-planner > /dev/null 2>&1 && echo "✅ Planner: PASS" || echo "❌ Planner: FAIL"
	@make test-codegen > /dev/null 2>&1 && echo "✅ Codegen: PASS" || echo "❌ Codegen: FAIL"
	@make test-validator > /dev/null 2>&1 && echo "✅ Validator: PASS" || echo "❌ Validator: FAIL"
	@make test-repair > /dev/null 2>&1 && echo "✅ Repair: PASS" || echo "❌ Repair: FAIL"
	@make test-render > /dev/null 2>&1 && echo "✅ Render: PASS" || echo "❌ Render: FAIL"
	@make test-critic > /dev/null 2>&1 && echo "✅ Critic: PASS" || echo "❌ Critic: FAIL"
	@echo ""
	@echo "Quick test completed. Run individual tests for detailed logs."
