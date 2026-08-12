---
title: Carve the MVP into features
status: resolved
type: grilling
blocked-by: [rules-data-schema, library-cli-architecture]
---

## Question

Slice the MVP (dice/task engine, random NPC character generator, data
loading, CLI, PyPI packaging/release) into feature-sized pieces, each
ready for `/grill-me` and `/speckit-specify`, with an agreed order.
Settle here the fog item on chargen breadth (which careers and optional
rules are in) since it determines whether chargen is one feature or
several. Resolving this decision reaches the map's destination.

## Resolution

Resolved 2026-08-11 via grilling. Chargen breadth settled first: the
MVP NPC generator covers **all SRD careers** (~24) and includes
**aging**; psionics and anagathics are out of MVP scope (recorded on the
map's Out of scope list).

The MVP carves into **five features**, in dependency order:

1. **dice-task-engine**: seeded RNG core, 2d6 throws, DMs, task checks
   against `tasks.toml`, the `cetools roll` subcommand with JSON and
   human output, plus initial project scaffolding (pyproject, package
   skeleton, test harness).
2. **rules-data-loading**: TOML loader with schema validation and the
   compact-string grammar ("INT 4+", "STR +1", "Pilot 2") from
   [Rules data schema](rules-data-schema.md), validated at load time.
3. **npc-generator**: career-term loop, skill acquisition, aging,
   mustering out, the character data model, sheet and JSON rendering in
   the library, and the `cetools npc` subcommand; ships with 3-4 seed
   careers to prove the engine.
4. **career-data**: author all remaining SRD careers as TOML data
   files, each validated against the grammar and generator.
5. **packaging-release**: distribution metadata, GPL-3.0 plus OGL
   1.0a/Section 15 bundling and OGC designation, the CSL compatibility
   statement, changelog, and the first CalVer release to PyPI.

Each feature now exits the map through `/grill-me` then
`/speckit-specify`; as each `specs/<NNN>-<name>/` directory is created,
link it here:

- dice-task-engine: (not yet specified)
- rules-data-loading: (not yet specified)
- npc-generator: (not yet specified)
- career-data: (not yet specified)
- packaging-release: (not yet specified)

With this resolution the map's destination is reached: no open
decisions remain.
