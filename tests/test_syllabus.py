from __future__ import annotations

from pathlib import Path

from mythings.corpus import ingest
from mythings.engine import EngineRequest, EngineResult, NoopEngine

from mysyllabus.syllabus import (
    decompose,
    parse_topics,
    slug,
    to_markdown,
    to_toml,
)

_PROGRAM = (
    "Unsupervised Learning — course program.\n"
    "Module 1: Foundations. Probability review; latent-variable models.\n"
    "Module 2: Clustering. k-means; Gaussian mixture models and the EM algorithm.\n"
    "Module 3: Dimensionality reduction. PCA; factor analysis."
)


class ScriptedEngine:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[EngineRequest] = []

    def run(self, request: EngineRequest) -> EngineResult:
        self.calls.append(request)
        return EngineResult(text=self.reply, data={})


def _docs():
    return ingest([Path("program.txt")], extractor=lambda _p: _PROGRAM)


_REPLY = (
    '{"topics": ['
    '{"title": "Latent-variable models", "unit": "Foundations"},'
    '{"title": "k-means", "unit": "Clustering"},'
    '{"title": "Gaussian mixture models", "unit": "Clustering"},'
    '{"title": "PCA", "unit": "Dimensionality reduction"}]}'
)


def test_decompose_parses_ordered_topics_with_units() -> None:
    engine = ScriptedEngine(_REPLY)
    topics = decompose(_docs(), engine)
    assert len(engine.calls) == 1
    assert [t.title for t in topics] == [
        "Latent-variable models", "k-means", "Gaussian mixture models", "PCA",
    ]
    assert [t.slug for t in topics][:2] == ["latent-variable-models", "k-means"]
    assert topics[1].unit == "Clustering"


def test_parse_strips_code_fences() -> None:
    topics = parse_topics(f"```json\n{_REPLY}\n```", max_topics=40)
    assert [t.title for t in topics][0] == "Latent-variable models"


def test_parse_dedupes_preserving_order() -> None:
    reply = '{"topics": [{"title": "PCA"}, {"title": "pca"}, {"title": "ICA"}]}'
    topics = parse_topics(reply, max_topics=40)
    assert [t.slug for t in topics] == ["pca", "ica"]


def test_max_topics_caps_the_list() -> None:
    topics = parse_topics(_REPLY, max_topics=2)
    assert [t.title for t in topics] == ["Latent-variable models", "k-means"]


def test_noop_engine_yields_no_topics() -> None:
    assert decompose(_docs(), NoopEngine()) == []


def test_insufficient_reply_yields_no_topics() -> None:
    assert parse_topics("INSUFFICIENT", max_topics=40) == []


def test_to_toml_round_trips_via_tomllib() -> None:
    import tomllib

    topics = parse_topics(_REPLY, max_topics=40)
    parsed = tomllib.loads(to_toml(topics))
    assert [t["slug"] for t in parsed["topic"]] == [slug(t.title) for t in topics]
    assert parsed["topic"][1]["unit"] == "Clustering"


def test_to_markdown_groups_by_unit() -> None:
    md = to_markdown(parse_topics(_REPLY, max_topics=40))
    assert "## Clustering" in md
    assert "**k-means**" in md
