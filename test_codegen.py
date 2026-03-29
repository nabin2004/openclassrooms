#!/usr/bin/env python3
"""Test the code generator agent individually"""

import asyncio
from manimator.agents.codegen import generate_code
from manimator.contracts.scene_spec import SceneSpec, SceneClass, Budget, MobjectSpec, AnimationSpec

async def test_codegen():
    spec = SceneSpec(
        scene_id=0,
        class_name='TestScene',
        scene_class=SceneClass.SCENE,
        budget=Budget.LOW,
        imports=['Scene', 'Axes', 'Dot', 'Text'],
        objects=[
            MobjectSpec(name='axes', type='Axes', init_params={'x_range': [0, 10], 'y_range': [0, 10]}),
            MobjectSpec(name='dot', type='Dot', init_params={'point': [5, 5, 0]})
        ],
        animations=[
            AnimationSpec(type='Create', target='axes', params={}, run_time=1.0),
            AnimationSpec(type='Create', target='dot', params={}, run_time=1.0)
        ]
    )
    print(f'Input spec: {spec.model_dump()}')
    result = await generate_code(spec)
    print('Generated code:')
    print(result)
    return result

if __name__ == "__main__":
    asyncio.run(test_codegen())
