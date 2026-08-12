---
title: Rules data schema
status: resolved
type: prototype
blocked-by: [srd-licensing]
---

## Question

What format and schema shape should the shipped rules data files take?
Pick the format (JSON, TOML, YAML, or other) and sketch the schema for
at least one career table and the core task/dice parameters, concretely
enough to react to. The schema must serve the dice engine and the random
NPC generator now, and world generation later, without redesign. Blocked
by licensing because the answer there may constrain whether table text
can ship verbatim or must be paraphrased/restructured.

## Resolution

Resolved 2026-08-11 by prototyping candidate schemas and choosing among
them with the user. Decided:

- **Format: TOML**, read by stdlib `tomllib` on Python 3.13+ (satisfies
  the constitution's Simplicity principle; no runtime dependency).
  Comments are allowed, so every shipped data file opens with its OGC
  designation inline, per the Licensing & Distribution Constraints.
  YAML was rejected for requiring PyYAML; JSON for hand-editing
  ergonomics.
- **Table entries are compact strings** ("STR +1", "INT 4+",
  "Gun Combat", "Pilot 2") parsed by a small engine grammar, validated
  at load time and covered by TDD. Data files read like the SRD's own
  tables and stay house-rule-friendly; the parsing complexity lives in
  code, once. The fully structured alternative (explicit
  kind/name/amount objects) was rejected as too noisy to hand-edit.
- **Layout: one file per career** (`careers/merchants.toml`, ...),
  plus shared domain files (e.g. `tasks.toml`, later `skills.toml`).
  Small diffs, per-file OGC boundaries, easy selective house-rule
  overrides.

Prototype artifacts (illustrative values, not yet SRD-faithful):
[merchants.toml](rules-data-schema-prototype/merchants.toml) (career
schema: qualification/survival/position/promotion checks, skill tables,
ranks, mustering out) and
[tasks.toml](rules-data-schema-prototype/tasks.toml) (2d6 task
parameters, characteristic DMs, difficulty DMs). Authoring the real,
SRD-faithful data and the grammar's formal definition happens inside the
features carved by
[Carve the MVP into features](carve-mvp-features.md).
