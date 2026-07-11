# my-syllabus — agent instructions

You are developing **my-syllabus**, a MyThingsLab My[X] tool.

**Inherited rules:** obey [`./HARNESS.md`](./HARNESS.md) in full — the vendored
MyThingsLab build-harness rules. Do not restate or override them. Anything not
covered here defers to `HARNESS.md`, then `my-things-core/docs/CONVENTIONS.md`.

## This tool

- **Purpose:** the learn-loop's **decompose** step. `decompose` reads a course
  program / syllabus document (via `mythings.corpus`) and turns it into an
  ordered list of masterable `mythings.mastery.Topic`s — the study sequence
  `my-professor` quizzes on and `due` ranks. Emits a machine-readable TOML topic
  list (what tools read) or a markdown outline (what a human reads).
- **The single Engine call:** one per invocation — "decompose this course program
  into an ordered list of masterable topics (prerequisites first), using only what
  the program names." Against `NoopEngine` it degrades to an empty list and a soft
  failure (exit 1), never an invented curriculum.
- **Invariants / rules:** exactly one Engine call per run. The program is read
  whole, not shortlisted — decomposition needs the entire document. Topics are
  never invented beyond what the program names; the list is order-preserving and
  slug-deduped. Output is deterministic given the reply. A `decompose` writes only
  to stdout or a local `--out` file (a personal topic list), never a repo PR; the
  durable study-repo publish path is a deliberate follow-up, not v0.
- **Backlog label:** `my-syllabus`
