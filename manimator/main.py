import sys
from pathlib import Path

# Fix sys.path *before* importing asyncio (which imports logging). Otherwise
# `python manimator/main.py` puts this package directory on sys.path[0] and
# `import logging` resolves to manimator/logging/ instead of the stdlib.
CURRENT_FILE = Path(__file__).resolve()
MANIMATOR_DIR = CURRENT_FILE.parent
PROJECT_ROOT = MANIMATOR_DIR.parent

if sys.path and Path(sys.path[0]).resolve() == MANIMATOR_DIR:
    sys.path.pop(0)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import asyncio

# Dotenv is applied in manimator/__init__.py (repo .env + manimator/.env).
from manimator.pipeline.graph import pipeline

DEFAULT_QUERY = """Teach me about Transformer architecture in detail"""


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the Manimator LangGraph pipeline.")
    p.add_argument(
        "-q",
        "--query",
        help="Topic or lecture brief (otherwise uses the built-in default prompt).",
    )
    p.add_argument(
        "--query-file",
        type=Path,
        help="Read the pipeline query from a UTF-8 text file.",
    )
    return p.parse_args()


async def main() -> None:
    """Main entry point to start the Manimator animation pipeline."""
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, OSError):
        pass

    args = _parse_args()
    if args.query_file is not None:
        query = args.query_file.read_text(encoding="utf-8")
    elif args.query is not None:
        query = args.query
    else:
        query = DEFAULT_QUERY

    print("--- Manimator Animation Engine ---")
    print(f"Directory: {MANIMATOR_DIR}")
    print(f"Project:   {PROJECT_ROOT}")
    preview = query.strip().replace("\n", " ")[:120]
    print(f"Processing query ({len(query)} chars): {preview}...\n")

    # Run the compiled LangGraph pipeline
    input_state = {"raw_query": query}
    pipeline_updates: dict = {}

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
            print("\n--- Narrated scene videos (natural animation pace + TTS) ---")
            for sid in sorted(narrated.keys()):
                print(f"  scene {sid}: {narrated[sid]}")

        delivery_dir = pipeline_updates.get("delivery_dir")
        final_video = pipeline_updates.get("output_video_path")
        if delivery_dir:
            print(f"\n--- Delivery package ---\nFolder: {delivery_dir}")
            print("(Contains transcript.txt; final.mp4 is all scenes concatenated when renders exist.)")
        if final_video:
            print(f"Combined video: {final_video}")

    except Exception as e:
        print(f"\n Pipeline failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Execution interrupted by user.")
