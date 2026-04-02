# SKILL: Voiceover / Narration Sync
Stage 5 of the Manimator pipeline.

## Input
- The ```scene-script from Stage 1 (contains `narration` and `duration_sec` per scene)
- The final Python code from Stage 3 (or Stage 4 if errors were fixed)

## Your Job
Produce two things:
1. A narration transcript file (`.txt`) — clean, cue-marked, ready for TTS or a human voice actor
2. Timing annotations injected into the Manim code as comments — so `self.wait()` calls align with speech

## Output Contract

### Narration file (```narration-script)
```narration-script
# MANIMATOR NARRATION SCRIPT
# Title: {animation title}
# Total duration: {total}s
# Generated for: TTS / Voice Actor

---

[SCENE 1 — {scene title}] [{duration}s]

{narration text, broken into breath groups of ~10 words per line}

[PAUSE 0.5s]

---

[SCENE 2 — {scene title}] [{duration}s]

{narration text}

---
```

### Annotated Manim code (```python-synced)
Return the full Python file with timing comments added. Do not change any logic — only add `# [NARRATION: ...]` and `# t={n}s` comments, and adjust `self.wait()` values to match narration pacing.

Format:
```python
# t=0s [NARRATION: "Imagine a simple coordinate plane..."]
self.play(Create(plane), run_time=2.5)
self.wait(0.5)  # breath pause after "coordinate plane"

# t=3s [NARRATION: "Now watch as the curve traces out..."]
self.play(Create(graph), run_time=3.0)
self.wait(1.0)  # hold for emphasis
```

## Narration Formatting Rules

**Breath groups**: Split long narration sentences at natural pause points — commas, conjunctions (and, but, so), or after 10–12 words. Each group gets its own line. This guides TTS pacing and helps voice actors breathe naturally.

**Pace calculation**: 130 words/minute is a comfortable explanatory pace.
- Formula: `words ÷ 130 × 60 = seconds`
- If narration words × (60/130) > scene `duration_sec`, flag it: `# WARNING: narration may run long — trim or extend duration`

**Pauses**: Insert `[PAUSE Xs]` at scene transitions and after key concepts land. Typical: 0.5s within a scene, 1.0–1.5s between scenes.

**Emphasis markers**: Wrap words that should be stressed: `*emphasized word*`. Voice actors will stress them; TTS systems that support SSML can use this.

**Scene headers**: Always include scene title and duration so the voice actor or TTS system knows the time budget.

## Timing Sync Rules

**Animation-first principle**: Visual animations should *start* 0.3–0.5s before the narration reaches the relevant phrase. Viewers need to see the object before hearing about it.

**Wait calibration**: After each `self.play()` block, calculate how many seconds of narration cover that visual, then set `self.wait()` to fill the gap:
```
wait_time = narration_seconds_for_this_block - animation_run_time
self.wait(max(0.2, wait_time))  # never wait less than 0.2s
```

**Scene boundary**: The last `self.wait()` before FadeOut should be long enough for the final narration phrase to complete. Minimum 0.8s.

**Flag mismatches**: If a scene's total `run_time + wait` doesn't match its `duration_sec`, add a comment:
```python
# TIMING NOTE: scene budget = 12s, current total = 10.5s — add 1.5s of wait or extend an animation
```

## Self-check Before Outputting
- Does each narration block fit within its scene's `duration_sec` at 130 wpm?
- Are all `[PAUSE]` markers placed at natural speech breaks?
- Are `self.wait()` values updated in the synced code?
- Is the narration file clean enough to paste directly into a TTS tool?

## Pass Forward
Output the ```narration-script block, then the ```python-synced block.
End with: `"Narration sync complete. Ready to render."` — this is the final handoff signal.