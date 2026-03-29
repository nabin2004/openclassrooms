from manimator.contracts.scene_spec import SceneSpec


def format_params(params: dict) -> str:
    if not params:
        return ""
    return ", " + ", ".join(f"{k}={repr(v)}" for k, v in params.items())


async def generate_code(spec: SceneSpec) -> str:
    animation_imports = set()
    for anim in spec.animations:
        animation_imports.add(anim.type)
    
    all_imports = list(set(spec.imports + list(animation_imports)))
    imports = ", ".join(all_imports)

    # Object definitions
    object_lines = []
    for obj in spec.objects:
        params = format_params(obj.init_params)
        object_lines.append(f"{obj.name} = {obj.type}({params})")

    # Animation lines
    animation_lines = []
    for anim in spec.animations:
        params = format_params(anim.params)
        animation_lines.append(
            f"self.play({anim.type}({anim.target}{params}), run_time={anim.run_time})"
        )

    # Camera operations (basic support)
    camera_lines = []
    for op in spec.camera_ops:
        if op.type == "move_camera":
            args = []
            if op.phi is not None:
                args.append(f"phi={op.phi}")
            if op.theta is not None:
                args.append(f"theta={op.theta}")
            if op.zoom is not None:
                args.append(f"zoom={op.zoom}")
            camera_lines.append(f"self.move_camera({', '.join(args)})")

        elif op.type == "set_camera_orientation":
            args = []
            if op.phi is not None:
                args.append(f"phi={op.phi}")
            if op.theta is not None:
                args.append(f"theta={op.theta}")
            camera_lines.append(f"self.set_camera_orientation({', '.join(args)})")

        elif op.type == "begin_ambient_rotation":
            camera_lines.append("self.begin_ambient_camera_rotation()")

    # Combine everything
    body_lines = (
        object_lines +
        camera_lines +
        animation_lines
    )

    body = "\n        ".join(body_lines) if body_lines else "pass"

    return f"""from manim import {imports}

class {spec.class_name}({spec.scene_class.value}):
    def construct(self):
        {body}
"""