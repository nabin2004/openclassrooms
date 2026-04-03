# Manimator Agent Testing Makefile
# Run individual agents for rigorous testing

.PHONY: help sync-tts test-intent test-decomposer test-planner test-codegen test-validator test-repair test-render test-critic test-all clean

UV ?= uv
UV_RUN ?= $(UV) run

# Default target
help:
	@echo "Manimator Agent Testing Commands:"
	@echo ""
	@echo "Environment:"
	@echo "  make sync            - Sync dependencies for all uv workspace packages"
	@echo "  make sync-tts        - Sync manimator with KittenTTS optional extra (+ ffmpeg on PATH)"
	@echo "  make lock            - Refresh uv.lock"
	@echo "  make sync-frozen     - Sync exactly from uv.lock"
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

# Sync all dependencies for all workspace packages
sync:
	@echo "Syncing uv workspace dependencies..."
	$(UV) sync --all-packages

sync-tts:
	@echo "Syncing manimator with TTS (KittenTTS) extra..."
	$(UV) sync --package manimator --extra tts

# Refresh lock file for the workspace
lock:
	@echo "Updating uv lockfile..."
	$(UV) lock

# Create environment exactly from lock file
sync-frozen:
	@echo "Syncing from lockfile (frozen)..."
	$(UV) sync --all-packages --frozen

# Test Intent Classifier
test-intent:
	@echo "Testing Intent Classifier Agent..."
	$(UV_RUN) python manimator/agents/intent_classifier.py > logs/test_intent.log 2>&1
	@echo "Intent test completed. Check logs/test_intent.log"

# Test Scene Decomposer  
test-decomposer:
	@echo "Testing Scene Decomposer Agent..."
	$(UV_RUN) python manimator/agents/scene_decomposer.py > logs/test_decomposer.log 2>&1
	@echo "Decomposer test completed. Check logs/test_decomposer.log"

# Test Scene Planner
test-planner:
	@echo "Testing Scene Planner Agent..."
	$(UV_RUN) python test_planner.py > logs/test_planner.log 2>&1
	@echo "Planner test completed. Check logs/test_planner.log"

# Test Code Generator
test-codegen:
	@echo "Testing Code Generator Agent..."
	$(UV_RUN) python test_codegen.py > logs/test_codegen.log 2>&1
	@echo "Codegen test completed. Check logs/test_codegen.log"

# Test Validator
test-validator:
	@echo "Testing Validator Agent..."
	$(UV_RUN) python test_validator.py > logs/test_validator.log 2>&1
	@echo "Validator test completed. Check logs/test_validator.log"

# Test Repair Agent
test-repair:
	@echo "Testing Repair Agent..."
	$(UV_RUN) python test_repair.py > logs/test_repair.log 2>&1
	@echo "Repair test completed. Check logs/test_repair.log"

# Test Render Agent (Stub)
test-render:
	@echo "Testing Render Agent (Stub)..."
	$(UV_RUN) python test_render.py > logs/test_render.log 2>&1
	@echo "Render test completed. Check logs/test_render.log"

# Test Critic Agent (Stub)
test-critic:
	@echo "Testing Critic Agent (Stub)..."
	$(UV_RUN) python test_critic.py > logs/test_critic.log 2>&1
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
	$(UV_RUN) python -m manimator.main
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
	@$(MAKE) test-intent > /dev/null 2>&1 && echo "✅ Intent: PASS" || echo "❌ Intent: FAIL"
	@$(MAKE) test-decomposer > /dev/null 2>&1 && echo "✅ Decomposer: PASS" || echo "❌ Decomposer: FAIL"
	@$(MAKE) test-planner > /dev/null 2>&1 && echo "✅ Planner: PASS" || echo "❌ Planner: FAIL"
	@$(MAKE) test-codegen > /dev/null 2>&1 && echo "✅ Codegen: PASS" || echo "❌ Codegen: FAIL"
	@$(MAKE) test-validator > /dev/null 2>&1 && echo "✅ Validator: PASS" || echo "❌ Validator: FAIL"
	@$(MAKE) test-repair > /dev/null 2>&1 && echo "✅ Repair: PASS" || echo "❌ Repair: FAIL"
	@$(MAKE) test-render > /dev/null 2>&1 && echo "✅ Render: PASS" || echo "❌ Render: FAIL"
	@$(MAKE) test-critic > /dev/null 2>&1 && echo "✅ Critic: PASS" || echo "❌ Critic: FAIL"
	@echo ""
	@echo "Quick test completed. Run individual tests for detailed logs."
