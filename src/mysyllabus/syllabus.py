from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from mythings.corpus import (
    Chunk,
    Document,
    Extractor,
    cached_extractor,
    chunk,
    extract,
    ingest,
)
from mythings.engine import Engine, EngineRequest
from mythings.mastery import Topic

TOOL = "mysyllabus"

# Shared corpus-loading shape with my-glossary / my-professor.
TEXT_SUFFIXES = frozenset({".md", ".txt", ".rst", ".tex"})
CORPUS_SUFFIXES = TEXT_SUFFIXES | {".pdf"}

# A program is read whole, not shortlisted — decomposition needs the entire
# document, not the excerpts matching a query. Cap the prompt so a stray huge
# file can't blow up one Engine call; a real course program is a few pages.
MAX_PROGRAM_CHARS = 12000

_FENCE_RE = re.compile(r"^```[a-zA-Z0-9]*\n?|\n?```$")
_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def program_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(p for p in sorted(path.rglob("*")) if p.suffix.lower() in CORPUS_SUFFIXES)
        elif path.is_file():
            files.append(path)
    return files


def load_program(
    paths: Iterable[Path],
    *,
    target_chars: int = 1200,
    extractor: Extractor = extract,
) -> tuple[list[Document], list[Chunk]]:
    documents = ingest(program_files(paths), extractor=extractor)
    chunks = [c for doc in documents for c in chunk(doc, target_chars=target_chars)]
    return documents, chunks


def resolve_extractor(cache_dir: Path | None) -> Extractor:
    return extract if cache_dir is None else cached_extractor(cache_dir)


def program_text(documents: Iterable[Document], *, limit: int = MAX_PROGRAM_CHARS) -> str:
    joined = "\n\n".join(doc.text for doc in documents)
    return joined[:limit]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "topic"


def _load_json(text: str) -> dict | None:
    # The ClaudeCLIEngine sometimes wraps JSON replies in ```json fences (a known
    # core bug); strip them, then fall back to the first {...} block, before
    # degrading honestly. (Copied in my-professor too — a candidate for a core
    # mythings.engine helper once the fence bug lands its real fix.)
    stripped = _FENCE_RE.sub("", text.strip()).strip()
    if not stripped:
        return None
    candidates = [stripped]
    match = _OBJECT_RE.search(stripped)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


SYSTEM = (
    "You decompose a university course program into an ordered list of masterable "
    "study topics, using only what the program states. Order them the way a student "
    "should learn them (prerequisites first). Keep each topic small enough to quiz on "
    "in one sitting. Use only topics the program actually names; do not invent scope. "
    'Reply as JSON: {"topics": [{"title": "...", "unit": "..."}, ...]} and nothing else, '
    'where "unit" is the section or module the topic belongs to (or "" if the program '
    "has no sections). If the document is not a course program, reply with exactly: "
    "INSUFFICIENT"
)


def build_prompt(text: str) -> str:
    return f"Course program:\n\n{text}\n\nOrdered study topics, as JSON:"


def parse_topics(text: str, *, max_topics: int) -> list[Topic]:
    parsed = _load_json(text)
    if not parsed:
        return []
    seen: set[str] = set()
    topics: list[Topic] = []
    for item in parsed.get("topics", []):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        key = slug(title)
        if key in seen:  # order-preserving dedupe
            continue
        seen.add(key)
        unit = str(item.get("unit", "")).strip() or None
        topics.append(Topic(slug=key, title=title, unit=unit))
        if len(topics) >= max_topics:
            break
    return topics


def decompose(
    documents: Iterable[Document],
    engine: Engine,
    *,
    max_topics: int = 40,
) -> list[Topic]:
    text = program_text(documents)
    if not text.strip():
        return []
    reply = engine.run(EngineRequest(prompt=build_prompt(text), system=SYSTEM))
    return parse_topics(reply.text, max_topics=max_topics)


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def to_toml(topics: Iterable[Topic]) -> str:
    # A human-editable, order-preserving topic list — the durable curriculum
    # artifact my-professor / my-flashcards read the study set from.
    blocks = []
    for topic in topics:
        lines = ["[[topic]]", f'slug = "{_toml_escape(topic.slug)}"',
                 f'title = "{_toml_escape(topic.title)}"']
        if topic.unit:
            lines.append(f'unit = "{_toml_escape(topic.unit)}"')
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def to_markdown(topics: list[Topic]) -> str:
    if not topics:
        return "_No topics: the Engine did not decompose this program._\n"
    lines: list[str] = []
    current_unit = object()  # sentinel so a real None unit still prints once
    for i, topic in enumerate(topics, 1):
        if topic.unit != current_unit:
            current_unit = topic.unit
            if topic.unit:
                lines += ["", f"## {topic.unit}", ""]
        lines.append(f"{i}. **{topic.title}** (`{topic.slug}`)")
    return "\n".join(lines).lstrip("\n") + "\n"
