from manimator.contracts.scene_spec import SceneSpec


async def generate_code(spec: SceneSpec) -> str:
    # STUB: returns minimal valid Manim code
    return f"""from manim import {", ".join(spec.imports)}

class {spec.class_name}({spec.scene_class.value}):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
"""