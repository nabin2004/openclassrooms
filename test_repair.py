#!/usr/bin/env python3
"""Test the repair agent individually"""

import asyncio
from manimator.agents.repair import repair_code
from manimator.contracts.validation import ValidationResult, ErrorType
from manimator.contracts.scene_spec import SceneSpec, SceneClass, Budget, MobjectSpec, AnimationSpec

async def test_repair():
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
        retry_count=0,
        original_spec=SceneSpec(
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
    )
    print(f'Input validation: {validation_result.model_dump()}')
    result = await repair_code(validation_result)
    print('Repaired code:')
    print(result)
    return result

if __name__ == "__main__":
    asyncio.run(test_repair())
