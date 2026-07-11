# my-syllabus

[![CI](https://github.com/MyThingsLab/my-syllabus/actions/workflows/ci.yml/badge.svg)](https://github.com/MyThingsLab/my-syllabus/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/MyThingsLab/my-syllabus/branch/main/graph/badge.svg)](https://codecov.io/gh/MyThingsLab/my-syllabus) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

The learn-loop's **decompose** step. Point it at a course program or syllabus and
it produces an ordered list of masterable topics — the study sequence
[`my-professor`](../my-professor) quizzes on and `myprofessor due` ranks.

It reads the program via the [MyThingsLab](../my-things-core) `mythings.corpus`
seam and emits `mythings.mastery.Topic`s, so the whole study cluster shares one
notion of "a topic".

## Usage

```bash
# Decompose a program into a machine-readable topic list (TOML)
mysyllabus decompose --program ~/Desktop/ul-course-program.pdf --engine claude \
  --out .mythings/topics.toml

# Or a human-readable outline grouped by module
mysyllabus decompose --program ~/Desktop/ul-course-program.pdf --engine claude --format md
```

`--engine noop` (default) makes zero Engine calls and returns no topics (a soft
failure, exit 1) — use `--engine claude` for a real decomposition. `--program` is
repeatable and accepts files or directories (`.pdf`, `.md`, `.txt`, `.rst`,
`.tex`); `--cache` memoises PDF text extraction; `--max-topics` caps the list.

## How it works

One Engine call: "decompose this program into an ordered list of masterable
topics, prerequisites first, using only what the program names." The program is
read **whole** (not shortlisted — decomposition needs the entire document). The
reply is parsed deterministically into order-preserving, slug-deduped `Topic`s;
topics are never invented beyond what the program states. A `decompose` writes
only to stdout or a local `--out` file — never a repo PR. (Publishing the topic
list to the shared `study` repo is a deliberate follow-up.)

The TOML output is the durable, human-editable topic list the rest of the cluster
reads the study set from; the markdown output is for reading.

## Install (development)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ../my-things-core -e ".[dev]"
pytest
```

## License

MIT — see [`LICENSE`](LICENSE).
