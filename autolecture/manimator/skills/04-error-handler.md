# SKILL: Error Handler / Debugger
Stage 4 of the Manimator pipeline — triggered only when Manim throws an error.

## Input
- The Python code from Stage 3
- The full error traceback (stderr output from running `manim`)

## Your Job
Diagnose the error, fix the code, and return a corrected file. Do not rewrite scenes that rendered successfully — only touch the broken parts.

## Error Taxonomy & Fixes

### 1. AttributeError / NameError
**Symptom**: `AttributeError: 'Text' object has no attribute '...'` or `NameError: name 'X' is not defined`
**Cause**: Wrong method name, deprecated API, or missing import.
**Fix pattern**:
- `ShowCreation` → `Create`
- `GrowFromCenter` → `GrowFromCenter` (still valid) or `FadeIn(scale=0.5)`
- `get_center()` on a non-Mobject → ensure object is a Mobject subclass
- Missing constant → check it's in `from manim import *`

### 2. LaTeX / MathTex compile error
**Symptom**: `LaTeX Error:` or `! Undefined control sequence`
**Cause**: Invalid LaTeX in a `MathTex` or `Tex` string.
**Fix pattern**:
- Escape backslashes: use raw strings `r"\frac{a}{b}"` — never `"\\frac{a}{b}"`
- Unknown command: replace with equivalent (`\mathbb{R}` needs `amsmath` — use `\mathbf{R}` as fallback or add `r"\usepackage{amsmath}"` to MathTex template)
- Empty string in `MathTex("")` → replace with `Text(" ")`

### 3. TypeError on animation
**Symptom**: `TypeError: play() argument ... must be Animation`
**Cause**: Passing a Mobject directly to `self.play()` instead of wrapping it in an animation.
**Fix**: `self.play(obj)` → `self.play(FadeIn(obj))`

### 4. Out-of-frame objects
**Symptom**: Animation runs but objects are invisible or clipped.
**Cause**: Positions outside the safe zone (x ∈ [-6,6], y ∈ [-3.5,3.5]) or scale too large.
**Fix**: Recalculate positions. Use `.scale_to_fit_width(n)` to constrain large objects.

### 5. Transform between mismatched types
**Symptom**: `TypeError` or visual glitch on `Transform`
**Cause**: Transforming `Text` into `MathTex` or different object types.
**Fix**: Use `ReplacementTransform` for type changes. `Transform` only for same-type morphing.

### 6. VGroup position errors
**Symptom**: Group moves to wrong location after `arrange()` or `next_to()`
**Cause**: `arrange()` positions relative to group center; calling `move_to` before `arrange` is overridden.
**Fix**: Always call `arrange()` before `move_to()` or `next_to()`.

### 7. Wait / timing mismatch
**Symptom**: Animation feels rushed or cut off.
**Cause**: Missing `self.wait()` or `run_time` too short.
**Fix**: Add explicit `self.wait(0.5)` between animation blocks. Increase `run_time` to match narration pacing.

### 8. Import / module error
**Symptom**: `ModuleNotFoundError` or `ImportError`
**Cause**: Using a library not available in Manim's environment.
**Fix**: Only `from manim import *` and `import numpy as np` are allowed. Remove all other imports and rewrite logic using only these.

## Debugging Process

1. Read the traceback — find the **file, line number, and error type**.
2. Identify which scene class is broken (look for the class name in the traceback).
3. Apply the fix from the taxonomy above. If the error is not in the taxonomy, reason from first principles about what the error message means.
4. Only modify the broken scene. Copy all other scene classes unchanged.
5. Re-run mentally: does the fix introduce any new issues?

## Output Contract

Output the full corrected Python file (all scenes, not just the fixed one). Prefix with a comment block:

```python
# FIX APPLIED: [one-line description of what was wrong and what changed]
# Scenes modified: [list class names]
# Scenes unchanged: [list class names]

from manim import *
...
```

Then on a new line after the code block: `"Fix applied. Re-run: manim -pql file.py {ClassName}"` — listing only the fixed class names.

## If the Error is Unfixable
If after analysis the error requires a fundamental restructuring (e.g. the storyboard requested an animation type that doesn't exist in Manim CE), output:
```
ESCALATE: [describe the problem]
SUGGESTION: [describe an alternative approach the storyboard planner should adopt]
```
This signals the orchestrator to loop back to Stage 2.