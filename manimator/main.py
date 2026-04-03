import sys
from pathlib import Path

# Path configuration: making the project root discoverable
CURRENT_FILE = Path(__file__).resolve()
MANIMATOR_DIR = CURRENT_FILE.parent
PROJECT_ROOT = MANIMATOR_DIR.parent

# When executed as `python manimator/main.py`, sys.path[0] points to
# the `manimator` directory. Remove it to avoid shadowing stdlib modules
# like `logging` with `manimator/logging`.
if sys.path and Path(sys.path[0]).resolve() == MANIMATOR_DIR:
    sys.path.pop(0)

# 1. Environment variables
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from manimator.pipeline.graph import pipeline

async def main():
    """Main entry point to start the Manimator animation pipeline."""
    print("--- Manimator Animation Engine ---")
    print(f"Directory: {MANIMATOR_DIR}")
    print(f"Project:   {PROJECT_ROOT}")
    
    # Default query (can be extended to CLI args later)
    query = """
Create a university-level lecture video titled: “Linear Regression: A Visual and Intuitive Understanding”.

The lecture should match the teaching style of top-tier institutions like Stanford University or MIT, combining deep intuition with mathematical rigor.

Structure and Content:

1. Opening (Hook + Motivation)

Start with a real-world problem (e.g., predicting house prices or exam scores).
Pose the key question: how can we model relationships between variables?
Keep it visual from the first 10 seconds.

2. Visual Introduction

Show a scatter plot of data points.
Gradually introduce the idea of fitting a line through the points.
Avoid equations at first—focus purely on intuition.

3. Building the Model

Introduce the concept of a line: slope and intercept.
Animate how changing slope and intercept affects the line.
Visually demonstrate underfitting vs. good fit vs. overfitting (even if briefly).

4. Error and Loss (Core Intuition)

Highlight vertical distances (residuals) from points to the line.
Animate squared errors (turn distances into squares visually).
Build intuition for why we minimize squared error.

5. Optimization

Show how the “best” line minimizes total error.
Animate iterative improvement (line adjusting step-by-step).
Optionally hint at gradient descent visually (no heavy math yet).

6. Introduce the Equation

Transition to the mathematical form:
y = mx + b
Then extend to:
y = w₁x + b
Explain each term visually (weights, bias).

7. Intuition Meets Math

Connect visuals (line fitting) with math (loss minimization).
Briefly show the cost function surface (3D visualization if possible).

8. Practical Insight

Show what happens with noisy data.
Briefly mention assumptions (linearity, independence, etc.).
Include one real-world example walkthrough.

9. Summary

Recap visually: data → line → error → optimization.
End with a clean mental model of what linear regression is doing.
Style Guidelines:
Clean, minimalist visuals (similar to 3Blue1Brown style).
Smooth animations with clear transitions.
Use color coding consistently (data points, line, errors).
Avoid clutter—each frame should teach one idea.
Narration should be calm, precise, and intellectually engaging.
Tone:
Assume the audience is intelligent but new to the concept.
Avoid oversimplification, but don’t jump into heavy math too early.
Prioritize intuition first, then formalism.
Output:
Length: 8–15 minutes
Include voiceover narration + synchronized animations
Ensure every concept is visually demonstrated, not just spoken
"""
    print(f"Processing: \"{query}\"\n")
    
    # Run the compiled LangGraph pipeline
    input_state = {"raw_query": query}
    pipeline_updates = {}
    
    try:
        async for event in pipeline.astream(input_state):
            for node, state in event.items():
                print(f"==> Step Completed: {node}")
                if isinstance(state, dict):
                    pipeline_updates.update(state)
                
        print("\n Animation generation pipeline complete.")

        full_transcript = pipeline_updates.get("full_transcript")
        if full_transcript:
            print("\n--- Transcript (for TTS) ---")
            print(full_transcript)
            transcript_path = pipeline_updates.get("transcript_path")
            if transcript_path:
                print(f"\nTranscript saved to: {transcript_path}")

        narrated = pipeline_updates.get("narrated_paths")
        if narrated:
            print("\n--- Narrated scene videos (voice synced to duration) ---")
            for sid in sorted(narrated.keys()):
                print(f"  scene {sid}: {narrated[sid]}")

    except Exception as e:
        print(f"\n Pipeline failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Execution interrupted by user.")
