# SKILL: Storyboard Planner
Stage 2 of the Manimator pipeline.

## Input
The ```scene-script block from Stage 1 (scene writer).

## Your Job
Translate each scene's `visual_intent` into a precise layout plan — what Manim objects exist, where they sit, and how they move. You are the bridge between plain-English intent and actual Manim code.

## Output Contract
Produce a JSON block tagged ```storyboard.

```storyboard
{
  "scenes": [
    {
      "id": "s1",
      "canvas": "16:9",
      "background_color": "#1a1a2e",
      "objects": [
        {
          "id": "obj1",
          "type": "MathTex | Text | Circle | Square | Arrow | NumberPlane | etc.",
          "content": "LaTeX string or label text if applicable",
          "initial_position": "CENTER | UP*2 | LEFT*3 + DOWN | [x, y, z]",
          "scale": 1.0,
          "color": "#HEX or Manim color constant"
        }
      ],
      "animation_sequence": [
        {
          "step": 1,
          "action": "Write | FadeIn | Create | Transform | MoveToTarget | etc.",
          "targets": ["obj1"],
          "duration": 1.5,
          "timing_note": "starts at t=0s, runs while narrator says '...'"
        }
      ],
      "camera": "static | pan_right | zoom_in | zoom_out",
      "exit": "FadeOut all | hold 1s | wipe"
    }
  ]
}
```

## Layout Rules

**Safe zone**: Manim's default frame is 14.2 wide × 8 units tall. Keep all objects within x ∈ [-6, 6], y ∈ [-3.5, 3.5]. Title text sits at y=3, footer at y=-3.2.

**Grouping**: If multiple objects move together, note them as a group. The coder will use `VGroup`.

**Positioning vocabulary**: Use Manim direction constants — `UP`, `DOWN`, `LEFT`, `RIGHT`, `UL`, `UR`, `DL`, `DR`, `ORIGIN`. Combine with scalars: `UP*2 + LEFT*3`.

**Text sizing**: Body text scale 0.6–0.8. Title scale 0.9–1.1. Math expressions scale 0.7–1.0 depending on complexity.

**Color palette**: Prefer high-contrast colors on dark backgrounds. Suggested: `#FFD700` (gold) for emphasis, `#00BFFF` (electric blue) for math, `#FF6B6B` (coral) for warnings, `WHITE` for body text.

**Animation pacing**: Match `duration` values to the scene's `duration_sec`. Total animation step durations should not exceed the scene's budget. Leave 0.5s at the end for the exit.

**Complexity ceiling**: Max 6–8 objects visible at once. If the scene needs more, stagger — fade old objects out before introducing new ones.

## Self-check Before Outputting
- Do all object positions fall within the safe zone?
- Do animation step durations sum to ≤ scene `duration_sec`?
- Is every object referenced in `animation_sequence` defined in `objects`?
- Does the exit action match what the scene script specified?

## Pass Forward
Output only the ```storyboard block plus: `"Storyboard ready: {N} scenes planned."` No other prose.