"""Generate queries.jsonl for batch runs (e.g. 2k rows from topics × templates)."""

from __future__ import annotations

import argparse
import json
import random
from itertools import product
from pathlib import Path

from manimator.batch.seed_topics import TOPICS as DEFAULT_TOPICS

TEMPLATES: list[str] = [
    "Explain {topic} for a short educational animation.",
    "Create a Manim-friendly lesson outline for {topic}.",
    "Teach {topic} visually in under three minutes of narration.",
    "Illustrate {topic} step by step for beginners.",
    "Give an intuition-first explanation of {topic} with simple diagrams.",
    "Compare and contrast key ideas around {topic} for students.",
    "Walk through a minimal worked example of {topic}.",
    "Highlight common misconceptions about {topic}.",
    "Show the core algorithm or idea behind {topic}.",
    "Explain why {topic} matters in modern CS or ML.",
    "Break {topic} into three concrete visual scenes.",
    "Animate the main data flow for {topic}.",
    "Use a timeline or stages to teach {topic}.",
    "Explain {topic} with a real-world analogy first.",
    "Summarize prerequisites needed before learning {topic}.",
    "What are the main equations or pseudocode for {topic}?",
    "How would you test understanding of {topic} after the lesson?",
    "Relate {topic} to adjacent topics a student may already know.",
    "Provide a compact glossary for terms in {topic}.",
    "End with a recap checklist for {topic}.",
]


def _load_topics(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_TOPICS)
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
    out = [ln for ln in lines if ln and not ln.startswith("#")]
    if not out:
        raise SystemExit(f"No topics found in {path}")
    return out


def _build_unique_queries(topics: list[str]) -> list[str]:
    raw = [tmpl.format(topic=t) for t, tmpl in product(topics, TEMPLATES)]
    return list(dict.fromkeys(raw))


def generate_queries_jsonl(
    *,
    output: Path,
    count: int,
    topics_file: Path | None,
    shuffle: bool,
    seed: int | None,
) -> int:
    topics = _load_topics(topics_file)
    unique = _build_unique_queries(topics)
    if not unique:
        raise SystemExit("Internal error: empty query list.")
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(unique)

    output.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(output, "w", encoding="utf-8") as f:
        for i in range(count):
            if i < len(unique):
                raw_query = unique[i]
            else:
                base = unique[i % len(unique)]
                pack = i // len(unique)
                raw_query = f"{base} [variant_{pack}]"
            rec = {"row_id": str(i), "raw_query": raw_query}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser(
        description="Build queries.jsonl for manimator.batch.runner (default ~132 topics × 20 templates)."
    )
    p.add_argument("--output", type=Path, required=True, help="Output JSONL path.")
    p.add_argument("--count", type=int, default=2000, help="Number of lines to emit (default 2000).")
    p.add_argument(
        "--topics-file",
        type=Path,
        default=None,
        help="UTF-8 text file: one topic per line (# comments and blank lines ignored).",
    )
    p.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle unique queries before taking the first --count.",
    )
    p.add_argument("--seed", type=int, default=None, help="RNG seed when using --shuffle.")
    args = p.parse_args()
    n = generate_queries_jsonl(
        output=args.output,
        count=max(1, int(args.count)),
        topics_file=args.topics_file,
        shuffle=bool(args.shuffle),
        seed=args.seed,
    )
    print(json.dumps({"written": n, "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
