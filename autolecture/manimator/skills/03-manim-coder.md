# SKILL: Manim Code Generator
Stage 3 of the Manimator pipeline.

## Input
The ```scene-script (Stage 1) and ```storyboard (Stage 2) blocks.

## Your Job
Write production-ready Manim (Community Edition) Python code that implements the storyboard exactly. One Python file, one `Scene` class per scene, runnable with `manim -pql output.py SceneName`.

## Output Contract
Output a single fenced JSON block tagged ```manim-code. No extra prose.

```manim-code
{
    "file_name": "animation.py",
    "class_names": ["Scene1_Title", "Scene2_Concept"],
    "primary_class": "Scene1_Title",
    "code": "from manim import *\n\nclass Scene1_Title(Scene):\n    def construct(self):\n        ...\n\nclass Scene2_Concept(Scene):\n    def construct(self):\n        ...\n"
}
```

After outputting the payload, call the `compile_manim_payload` tool with the same JSON payload string.
Return the tool response verbatim as the handoff artifact for downstream stages.

## Code Conventions (intermediate level)

**File structure**:
```python
from manim import *

# Optional config — only if non-default needed
config.background_color = "#1a1a2e"

class SceneN_ShortName(Scene):
    def construct(self):
        # --- Objects ---
        # --- Animations ---
        # --- Exit ---
```

**Naming**: Class names follow `Scene{N}_{CamelCaseName}`. Match the storyboard `id`.

**Timing**: Use `self.wait(n)` to hold. Use `run_time=` on every animation — never rely on default. Match durations from the storyboard.

**VGroups**: Group related objects. Apply transforms to the group, not individual members, when they move together.

**Text vs MathTex**:
- Plain text → `Text("...", font_size=36)`
- LaTeX math → `MathTex(r"...")`
- Mixed → `Tex(r"some text $E=mc^2$ more text")`

**Positioning**:
```python
obj.move_to(UP * 2 + LEFT * 3)   # absolute position
obj.next_to(other, DOWN, buff=0.3) # relative
obj.to_edge(UP, buff=0.5)          # edge-anchored
```

**Common animation patterns**:
```python
# Fade in
self.play(FadeIn(obj), run_time=1)

# Write text or math
self.play(Write(obj), run_time=1.5)

# Draw shape outline then fill
self.play(Create(shape), run_time=1)

# Transform one object into another
self.play(Transform(obj_a, obj_b), run_time=1)

# Animate a value changing (e.g. number counter)
tracker = ValueTracker(0)
label = always_redraw(lambda: DecimalNumber(tracker.get_value()))
self.play(tracker.animate.set_value(100), run_time=2)

# Move object
self.play(obj.animate.shift(RIGHT * 2), run_time=1)

# Simultaneous animations
self.play(FadeIn(a), Write(b), run_time=1.5)
```

**Arrows**:
```python
arr = Arrow(start=LEFT * 2, end=RIGHT * 2, color=WHITE)
# or between objects:
arr = Arrow(obj_a.get_right(), obj_b.get_left(), buff=0.1)
```

**NumberPlane / Axes**:
```python
plane = NumberPlane(x_range=[-5, 5], y_range=[-3, 3])
axes = Axes(x_range=[0, 10, 1], y_range=[0, 100, 10],
            axis_config={"include_tip": True})
graph = axes.plot(lambda x: x**2, color=YELLOW)
```

**Color**: Use hex strings (`"#FF6B6B"`) or Manim constants (`RED`, `BLUE`, `YELLOW`, `WHITE`, `GRAY`, `GREEN`, `GOLD`).

**Exit pattern** — end every scene with:
```python
self.play(FadeOut(*self.mobjects), run_time=0.8)
```

## What NOT to Do
- Never use deprecated `ShowCreation` — use `Create`
- Never use `self.add()` as a substitute for animating — always `self.play()`
- Never hardcode pixel positions — always use Manim's unit system
- Never import anything outside `manim` unless it is `numpy as np`
- Don't leave unused variables (linters will flag, confuses the error handler)

## Self-check Before Outputting
- Does every class have a `construct` method?
- Does every object get added via `self.play()` or `self.add()` before being transformed?
- Do all `run_time` values match the storyboard durations?
- Does each scene end with a FadeOut or hold as specified?
- Is the file runnable with `manim -pql file.py ClassName` for each class?

## Pass Forward
Output the ```manim-code payload, then call `compile_manim_payload`.
If compilation succeeds, pass forward the returned `video_paths` and `compiled_classes`.
If compilation fails, pass forward the full error log to Stage 4 for repair.