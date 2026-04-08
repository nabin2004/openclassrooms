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
import logging
import uuid

# Dotenv is applied in manimator/__init__.py (repo .env + manimator/.env).
from amoeba.observability import get_logger as get_amoeba_logger
from amoeba.observability import log_structured, set_trace_id
from manimator.pipeline.graph import pipeline
from manimator.logging import configure_logging, get_logger, log_exception
from manimator.exceptions import ManimatorError

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
    p.add_argument(
        "--log-level",
        default=None,
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Overrides MANIMATOR_LOG_LEVEL.",
    )
    p.add_argument(
        "--log-json",
        action="store_true",
        help="Emit JSON logs. Overrides MANIMATOR_LOG_JSON.",
    )
    p.add_argument(
        "--log-file",
        default=None,
        help="Write logs to this file in addition to stderr. Overrides MANIMATOR_LOG_FILE.",
    )
    p.add_argument(
        "--run-id",
        default=None,
        help="Optional run id for correlating logs (defaults to a UUID).",
    )
    return p.parse_args()


async def main() -> None:
    """Main entry point to start the Manimator animation pipeline."""
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, OSError):
        pass

    args = _parse_args()
    run_id = args.run_id or uuid.uuid4().hex

    configure_logging(level=args.log_level, json_logs=bool(args.log_json), log_file=args.log_file)
    log = get_logger("manimator.main", run_id=run_id)
    set_trace_id(run_id)
    log_structured(get_amoeba_logger(), logging.INFO, "manimator.run.start", run_id=run_id)

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
    input_state = {"raw_query": query, "run_id": run_id}
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
        log_structured(
            get_amoeba_logger(),
            logging.INFO,
            "manimator.run.completed",
            run_id=run_id,
            delivery_dir=pipeline_updates.get("delivery_dir"),
            output_video_path=pipeline_updates.get("output_video_path"),
        )

    except ManimatorError as e:
        log.error("Pipeline failed: %s", e)
        if e.details:
            log.debug("Error details: %s", e.details)
        log_structured(get_amoeba_logger(), logging.ERROR, "manimator.run.failed", run_id=run_id, error=str(e))
        raise
    except Exception as e:
        log_exception(log, "Pipeline crashed with an unexpected error.", exc=e, level=logging.ERROR)
        log_structured(get_amoeba_logger(), logging.ERROR, "manimator.run.crashed", run_id=run_id, error=str(e))
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Execution interrupted by user.")
    except ManimatorError:
        raise SystemExit(2)
    except Exception:
        raise SystemExit(1)
