from __future__ import annotations

import argparse
from pathlib import Path

from mythings.engine import build_engine_from_args

from mysyllabus.syllabus import (
    decompose,
    load_program,
    resolve_extractor,
    to_markdown,
    to_toml,
)

BACKLOG_LABEL = "my-syllabus"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mysyllabus",
        description="Decompose a course program into an ordered list of masterable topics.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    dec = sub.add_parser("decompose", help="turn a program document into an ordered topic list")
    dec.add_argument("--program", type=Path, action="append", required=True,
                     help="course program / syllabus file or directory (repeatable)")
    dec.add_argument("--engine", choices=("noop", "claude"), default="noop")
    dec.add_argument("--max-topics", type=int, default=40)
    dec.add_argument("--format", choices=("toml", "md"), default="toml",
                     help="toml is the machine-readable topic list tools read; md is for reading")
    dec.add_argument("--out", type=Path, help="write to this file instead of stdout")
    dec.add_argument("--cache", type=Path, help="cache extracted PDF text under this directory")

    args = parser.parse_args(argv)

    documents, _ = load_program(args.program, extractor=resolve_extractor(args.cache))
    if not documents:
        print("no program files found")
        return 1

    topics = decompose(documents, build_engine_from_args(args), max_topics=args.max_topics)
    rendered = to_toml(topics) if args.format == "toml" else to_markdown(topics)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        print(f"wrote {len(topics)} topic(s) to {args.out}")
    else:
        print(rendered, end="")

    # No topics is a soft failure: the program was read but nothing came back
    # (NoopEngine, or a document that isn't a program). Surfaced, not hidden.
    return 0 if topics else 1


if __name__ == "__main__":
    raise SystemExit(main())
