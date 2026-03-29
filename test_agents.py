#!/usr/bin/env python3
"""
Interactive Agent Testing Script for Manimator
Run individual agents with custom inputs for rigorous testing
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from manimator.agents.intent_classifier import classify_intent
from manimator.agents.scene_decomposer import decompose_scenes
from manimator.agents.planner import plan_scene
from manimator.agents.codegen import generate_code
from manimator.agents.validator import validate_code
from manimator.agents.repair import repair_code
from manimator.agents.critic import critique_render
from manimator.pipeline.graph import node_render, node_finalize

from manimator.contracts.intent import IntentResult, ConceptType, Modality
from manimator.contracts.scene_plan import SceneEntry, SceneClass, Budget
from manimator.contracts.scene_spec import SceneSpec, MobjectSpec, AnimationSpec
from manimator.contracts.validation import ValidationResult, ErrorType


class AgentTester:
    def __init__(self):
        self.results = {}
    
    async def test_intent_classifier(self, query: str = None):
        """Test the intent classifier agent"""
        if query is None:
            query = "Explain linear regression visually with a scatter plot and a line of best fit."
        
        print(f"\n🔍 Testing Intent Classifier")
        print(f"Input: {query}")
        
        try:
            result = await classify_intent(query)
            print(f"✅ Success: {result.model_dump()}")
            self.results['intent'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['intent'] = None
            return None
    
    async def test_scene_decomposer(self, intent: IntentResult = None):
        """Test the scene decomposer agent"""
        if intent is None:
            intent = IntentResult(
                in_scope=True,
                raw_query="Explain linear regression visually with a scatter plot and a line of best fit.",
                concept_type=ConceptType.MATH,
                modality=Modality.GRAPH,
                complexity=2
            )
        
        print(f"\n🎬 Testing Scene Decomposer")
        print(f"Input: {intent.model_dump()}")
        
        try:
            result = await decompose_scenes(intent)
            print(f"✅ Success: {result.model_dump()}")
            self.results['decomposer'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['decomposer'] = None
            return None
    
    async def test_planner(self, scene: SceneEntry = None):
        """Test the scene planner agent"""
        if scene is None:
            scene = SceneEntry(
                id=0,
                title="Introduction to Scatter Plot",
                scene_class=SceneClass.SCENE,
                budget=Budget.LOW,
                prerequisite_ids=[]
            )
        
        print(f"\n📋 Testing Scene Planner")
        print(f"Input: {scene.model_dump()}")
        
        try:
            result = await plan_scene(scene)
            print(f"✅ Success: {result.model_dump()}")
            self.results['planner'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['planner'] = None
            return None
    
    async def test_code_generator(self, spec: SceneSpec = None):
        """Test the code generator agent"""
        if spec is None:
            spec = SceneSpec(
                scene_id=0,
                class_name="TestScene",
                scene_class=SceneClass.SCENE,
                budget=Budget.LOW,
                imports=["Scene", "Axes", "Dot", "Text"],
                objects=[
                    MobjectSpec(name="axes", type="Axes", init_params={"x_range": [0, 10], "y_range": [0, 10]}),
                    MobjectSpec(name="dot", type="Dot", init_params={"point": [5, 5, 0]})
                ],
                animations=[
                    AnimationSpec(type="Create", target="axes", params={}, run_time=1.0),
                    AnimationSpec(type="Create", target="dot", params={}, run_time=1.0)
                ]
            )
        
        print(f"\n💻 Testing Code Generator")
        print(f"Input: {spec.model_dump()}")
        
        try:
            result = await generate_code(spec)
            print(f"✅ Success:\n{result}")
            self.results['codegen'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['codegen'] = None
            return None
    
    async def test_validator(self, code: str = None, spec: SceneSpec = None):
        """Test the validator agent"""
        if code is None:
            code = '''
from manim import Scene, Axes, Dot, Text

class TestScene(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 10], y_range=[0, 10])
        dot = Dot(point=[5, 5, 0])
        self.play(Create(axes), run_time=1.0)
        self.play(Create(dot), run_time=1.0)
'''
        
        if spec is None:
            spec = SceneSpec(
                scene_id=0,
                class_name="TestScene",
                scene_class=SceneClass.SCENE,
                budget=Budget.LOW,
                imports=["Scene", "Axes", "Dot"],
                objects=[],
                animations=[]
            )
        
        print(f"\n✅ Testing Validator")
        print(f"Code length: {len(code)} characters")
        
        try:
            result = await validate_code(code, spec)
            print(f"✅ Success: {result.model_dump()}")
            self.results['validator'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['validator'] = None
            return None
    
    async def test_repair(self, validation_result: ValidationResult = None):
        """Test the repair agent"""
        if validation_result is None:
            broken_code = '''
from manim import Scene, Axes, Dot

class TestScene(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 10], y_range=[0, 10])
        dot = Dot(point=[5, 5, 0])
        self.play(Create(NonExistentObject), run_time=1.0)
        self.play(Create(dot), run_time=1.0)
'''
            
            validation_result = ValidationResult(
                passed=False,
                scene_id=0,
                failing_code=broken_code,
                error_type=ErrorType.NAME_ERROR,
                error_message="name 'NonExistentObject' is not defined",
                error_line=6,
                retry_count=0
            )
        
        print(f"\n🔧 Testing Repair Agent")
        print(f"Input: {validation_result.model_dump()}")
        
        try:
            result = await repair_code(validation_result)
            print(f"✅ Success:\n{result}")
            self.results['repair'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['repair'] = None
            return None
    
    async def test_render(self, state=None):
        """Test the render agent"""
        if state is None:
            from manimator.pipeline.state import PipelineState
            state = PipelineState()
            state.scene_specs = [
                SceneSpec(
                    scene_id=0,
                    class_name="TestScene1",
                    scene_class=SceneClass.SCENE,
                    budget=Budget.LOW,
                    imports=["Scene", "Circle"],
                    objects=[],
                    animations=[]
                )
            ]
            state.generated_codes = {
                0: '''from manim import Scene, Circle

class TestScene1(Scene):
    def construct(self):
        circle = Circle(radius=1, color=BLUE)
        self.play(Create(circle), run_time=1.0)
'''
            }
        
        print(f"\n🎥 Testing Render Agent")
        print(f"Scenes to render: {len(state.scene_specs)}")
        
        try:
            result = await node_render(state)
            print(f"✅ Success: {result}")
            self.results['render'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['render'] = None
            return None
    
    async def test_critic(self, scene_ids=None, paths=None):
        """Test the critic agent"""
        if scene_ids is None:
            scene_ids = [0, 1, 2]
        if paths is None:
            paths = ["test_outputs/scene_0.mp4", "test_outputs/scene_1.mp4", "test_outputs/scene_2.mp4"]
        
        print(f"\n👁️ Testing Critic Agent")
        print(f"Scenes: {scene_ids}")
        print(f"Paths: {paths}")
        
        try:
            result = await critique_render(scene_ids, paths)
            print(f"✅ Success: {result.model_dump()}")
            self.results['critic'] = result
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            self.results['critic'] = None
            return None
    
    async def test_full_pipeline(self):
        """Test the complete pipeline with sample data"""
        print("\n🔄 Testing Full Pipeline")
        
        # Step 1: Intent
        intent = await self.test_intent_classifier()
        if not intent:
            return False
        
        # Step 2: Decomposer
        scene_plan = await self.test_scene_decomposer(intent)
        if not scene_plan:
            return False
        
        # Step 3: Planner
        specs = []
        for scene in scene_plan.scenes:
            spec = await self.test_planner(scene)
            if spec:
                specs.append(spec)
        
        if not specs:
            return False
        
        # Step 4: Codegen
        codes = {}
        for spec in specs:
            code = await self.test_code_generator(spec)
            if code:
                codes[spec.scene_id] = code
        
        if not codes:
            return False
        
        # Step 5: Validate
        validation_results = {}
        for scene_id, code in codes.items():
            spec = next(s for s in specs if s.scene_id == scene_id)
            result = await self.test_validator(code, spec)
            if result:
                validation_results[scene_id] = result
        
        if not validation_results:
            return False
        
        print(f"\n🎉 Full pipeline test completed successfully!")
        return True
    
    def save_results(self, filename="test_results.json"):
        """Save test results to file"""
        import json
        serializable_results = {}
        for key, value in self.results.items():
            if hasattr(value, 'model_dump'):
                serializable_results[key] = value.model_dump()
            elif isinstance(value, str):
                serializable_results[key] = value
            else:
                serializable_results[key] = str(value)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test individual Manimator agents")
    parser.add_argument("--agent", choices=["intent", "decomposer", "planner", "codegen", "validator", "repair", "render", "critic", "pipeline"], 
                       help="Specific agent to test")
    parser.add_argument("--query", type=str, help="Custom query for intent classifier")
    parser.add_argument("--save", action="store_true", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    tester = AgentTester()
    
    if args.agent == "intent":
        await tester.test_intent_classifier(args.query)
    elif args.agent == "decomposer":
        await tester.test_scene_decomposer()
    elif args.agent == "planner":
        await tester.test_planner()
    elif args.agent == "codegen":
        await tester.test_code_generator()
    elif args.agent == "validator":
        await tester.test_validator()
    elif args.agent == "repair":
        await tester.test_repair()
    elif args.agent == "render":
        await tester.test_render()
    elif args.agent == "critic":
        await tester.test_critic()
    elif args.agent == "pipeline":
        await tester.test_full_pipeline()
    
    if args.save:
        tester.save_results()


if __name__ == "__main__":
    asyncio.run(main())
