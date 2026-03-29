#!/usr/bin/env python3
"""Test the render agent individually"""

import asyncio
from manimator.pipeline.graph import node_render
from manimator.pipeline.state import PipelineState
from manimator.contracts.scene_spec import SceneSpec, SceneClass, Budget, MobjectSpec, AnimationSpec

async def test_render():
    # Mock state with generated codes
    state = PipelineState()
    state.scene_specs = [
        SceneSpec(
            scene_id=0,
            class_name='TestScene1',
            scene_class=SceneClass.SCENE,
            budget=Budget.LOW,
            imports=['Scene', 'Circle'],
            objects=[
                MobjectSpec(name='circle', type='Circle', init_params={'radius': 1, 'color': 'BLUE'})
            ],
            animations=[
                AnimationSpec(type='Create', target='circle', params={}, run_time=1.0)
            ]
        ),
        SceneSpec(
            scene_id=1,
            class_name='TestScene2',
            scene_class=SceneClass.SCENE,
            budget=Budget.LOW,
            imports=['Scene', 'Square'],
            objects=[
                MobjectSpec(name='square', type='Square', init_params={'side_length': 2, 'color': 'RED'})
            ],
            animations=[
                AnimationSpec(type='Create', target='square', params={}, run_time=1.0)
            ]
        )
    ]
    state.generated_codes = {
        0: '''from manim import Scene, Circle

class TestScene1(Scene):
    def construct(self):
        circle = Circle(radius=1, color=BLUE)
        self.play(Create(circle), run_time=1.0)
''',
        1: '''from manim import Scene, Square

class TestScene2(Scene):
    def construct(self):
        square = Square(side_length=2, color=RED)
        self.play(Create(square), run_time=1.0)
'''
    }
    print('Testing render with mock state...')
    result = await node_render(state)
    print(f'Render result: {result}')
    return result

if __name__ == "__main__":
    asyncio.run(test_render())
