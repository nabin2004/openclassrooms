# SKILL: Scene Writer
Stage 1 of the Manimator pipeline.

## Input
A raw user prompt describing a concept, topic, or idea to animate.

## Your Job
Transform the prompt into a structured scene script — a clear, ordered breakdown of what the animation will explain and show. This is the source of truth for every downstream stage.

## Output Contract
Produce a JSON block tagged ```scene-script that every downstream skill can parse.

```scene-script
{
  "title": "Short animation title",
  "total_duration_sec": 60,
  "audience": "general | technical | student",
  "scenes": [
    {
      "id": "s1",
      "title": "Scene title",
      "duration_sec": 12,
      "narration": "Exactly what the voiceover says. Written as natural spoken sentences.",
      "visual_intent": "What should appear on screen. Describe objects, motion, and transitions in plain English — not Manim code.",
      "key_concept": "The one idea this scene must land."
    }
  ]
}
```

## Rules

**Scene count**: 3–6 scenes for prompts under 2 minutes. Each scene = one idea. Never combine two concepts in a single scene.

**Duration**: Assign `duration_sec` so scenes sum to `total_duration_sec`. Default total: 60s for simple topics, 90s for multi-step concepts, 120s max.

**Narration**: Write as if speaking to a curious person, not reading a textbook. Contractions are fine. Avoid jargon unless the audience is `technical`. Each narration line should be completable in the scene's `duration_sec` at ~130 words/min.

**Visual intent**: Be concrete. Instead of "show a graph", write "a coordinate plane fades in, then a red curve traces from left to right as the narration explains the trend." The storyboard stage will use this to plan exact Manim objects.

**Key concept**: One sentence max. Forces each scene to have a single purpose.

**Transitions**: End each `visual_intent` with how the scene exits — fade out, hold for 1s, wipe to next.

## Self-check Before Outputting
- Do narration durations fit the scene's `duration_sec`?
- Is every scene's `key_concept` distinct from the others?
- Does the sequence build understanding — simpler scenes before complex ones?
- Is `visual_intent` specific enough that a storyboard artist could sketch it?

## Pass Forward
Output only the ```scene-script block plus a one-line summary: `"Scene script ready: {N} scenes, {total}s total."` No other prose.