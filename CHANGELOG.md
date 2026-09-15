# Changelog

## [Unreleased]
### Added/Changed
- MySyllabus v0: decompose a course program (via mythings.corpus, read whole) into ordered mythings.mastery.Topic list; one Engine call; TOML/markdown out; local stdout/--out, no PR; fence-stripping JSON parse; order-preserving slug-dedupe. 13 tests, 94% cov.
- Mechanical migration to mythings.testing: inline ScriptedEngine replaced by the shared one (drop-in).
