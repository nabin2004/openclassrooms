#!/usr/bin/env python3
"""Test the validator agent individually"""

import asyncio
from manimator.agents.validator import validate_code
from manimator.contracts.scene_spec import SceneSpec, SceneClass, Budget, MobjectSpec, AnimationSpec

async def test_validator():
    code = '''
from manim import Scene, Axes, Dot, Text

class TestScene(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 10], y_range=[0, 10])
        dot = Dot(point=[5, 5, 0])
        self.play(Create(axes), run_time=1.0)
        self.play(Create(dot), run_time=1.0)
'''
    
    spec = SceneSpec(
        scene_id=0,
        class_name='TestScene',
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        imports=['Scene', 'Axes', 'Dot'],
        objects=[
            MobjectSpec(name='axes', type='Axes', init_params={'x_range': [0, 10], 'y_range': [0, 10]}),
            MobjectSpec(name='dot', type='Dot', init_params={'point': [5, 5, 0]})
        ],
        animations=[
            AnimationSpec(type='Create', target='axes', params={}, run_time=1.0),
            AnimationSpec(type='Create', target='dot', params={}, run_time=1.0)
        ]
    )
    print(f'Input code length: {len(code)} characters')
    result = await validate_code(code, spec)
    print(f'Validation result: {result.model_dump()}')
    return result

if __name__ == "__main__":
    asyncio.run(test_validator())
