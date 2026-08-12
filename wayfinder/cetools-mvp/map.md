# Cepheus Engine tools: MVP

## Destination

The MVP is scoped and carved into feature-sized pieces, each ready for
`/grill-me` and `/speckit-specify`. MVP scope: a library-first Python
package (with CLI) providing the core 2d6 dice/task engine and a fully
random, NPC-oriented character generator for referee prep, published to
PyPI.

## Notes

- Domain: the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/),
  a 2d6 sci-fi OGL system in the classic Traveller lineage.
- Primary audience: referees preparing for sessions. Player-facing
  interactivity is not an MVP concern.
- Standing preferences settled while charting:
  - Library-first: all functionality lives in the library; the CLI is a
    thin consumer. A web UI is a possible future consumer, not part of
    this map.
  - Rules content (career tables, etc.) lives in data files shipped with
    the package; engine code interprets them.
  - All generation is reproducible from a seed, from day one.
- When writing Python, consult matching `fluent-python:*` skills.
- The Spec Kit constitution was ratified at 2026.08.1 on 2026-08-11; read
  `.specify/memory/constitution.md` before resolving any decision.

## Decisions so far

<!-- one line per resolved decision; zoom the link for detail -->

- [SRD licensing and redistribution obligations](decisions/srd-licensing.md):
  OGL 1.0a; verbatim tables may ship as data files if the package
  bundles the OGL text, the full Section 15 chain, and an OGC
  designation; "Cepheus Engine" is Product Identity, so keep it out of
  the package name and shipped data.
- [PyPI package name](decisions/pypi-package-name.md): `cetools` is
  available on PyPI (as are `cepheus-tools` and `cepheustools`); no
  existing Cepheus/Traveller PyPI package collides.
- [Ratify the constitution](decisions/ratify-constitution.md):
  constitution 2026.08.1 ratified with six principles (library-first, CLI
  text I/O, non-negotiable TDD, seeded generation, data-driven rules,
  simplicity); GPL-3.0 code alongside OGL data, CalVer `YYYY.0M.INC1`,
  Python 3.13+.
- [Rules data schema](decisions/rules-data-schema.md): TOML read by
  stdlib `tomllib`, one file per career plus shared domain files,
  compact-string table entries ("STR +1", "INT 4+") parsed by a small
  validated engine grammar; prototype files linked from the resolution.
- [Library and CLI architecture](decisions/library-cli-architecture.md):
  one `cetools` distribution (same name for PyPI, import, and command);
  typer-based CLI with verb subcommands, justified as a typed,
  declarative CLI layer; all rendering (JSON and human text) lives in
  the library; every generator subcommand takes `--seed` and echoes the
  seed used.
- [Carve the MVP into features](decisions/carve-mvp-features.md): five
  features in dependency order (dice-task-engine, rules-data-loading,
  npc-generator, career-data, packaging-release); the NPC generator
  covers all SRD careers with aging included. **Destination reached: no
  open decisions remain.** Each feature now proceeds via `/grill-me`
  and `/speckit-specify`; spec directories are linked from the carve
  resolution as they are created.

## Not yet specified

<!-- empty: the destination is reached; all fog cleared -->
## Out of scope

- World/subsector generation: explicitly deferred to post-MVP; the first
  follow-on effort after this map completes.
- Trade & commerce tools: not selected as an MVP candidate.
- Interactive lifepath character generation (player-facing): MVP chargen
  is fully random.
- Psionics and anagathics: excluded from the MVP NPC generator while
  carving; candidates for a post-MVP data/engine addition.
- Web UI: a possible future consumer of the library, not part of this
  effort.
