# Cepheus Engine Tools — Project Specification

## Overview

This project provides a set of command-line utilities for players and referees of the Cepheus Engine tabletop roleplaying game ([Cepheus SRD](https://cepheus-srd.opengamingnetwork.com/)). The primary deliverable is a modular, well-tested CLI package that performs common game-related tasks (character creation, NPC generation, dice rolling helpers, ship/vehicle builders, encounter balancing, random tables, SRD lookup). The design will favour a clear CLI-first UX while remaining architecture-friendly so a RESTful API or web UI can be added later without major rework.

## Audience

- Players who want quick offline tools for character generation, rolls, and lookups.
- Referees (GMs) who need utilities for encounter and NPC generation, campaign management, and random tables.
- Integrators who may embed the functionality into web apps or services in the future.

## Goals

- Provide a small, discoverable CLI with composable commands and sensible defaults.
- Keep the core logic library-usable so commands are thin wrappers around a stable Python API.
- Persist user configuration locally (JSON/TOML) and support exporting generated artifacts (JSON/YAML/CSV).
- Ship with documentation, tests, and CI hooks to ensure quality.

## Non-Goals (initial)

- No full web UI or public hosted API on first release.
- No official mobile apps.

## Requirements Checklist

- [x] CLI utilities for players and referees
- [x] Core library separated from CLI commands
- [x] Local configurable persistence for user data and exports
- [x] Extensible design to enable future REST API / web frontend
- [x] Tests (unit + a few integration) and CI pipeline
- [x] Documentation and examples

## High-level Architecture / Contract

- Inputs: user commands (CLI args / config files), optional JSON/YAML artifact imports.
- Outputs: console output (human readable), machine outputs (JSON/YAML/CSV files), exit codes (0 success, >0 errors).
- Error modes: invalid input, missing resources (SRD lookup), disk IO errors, dependency failures.

Core contract for library functions:

- Accept native Python data structures and return well-typed Python objects (dataclasses).

- Provide deterministic outputs given seedable RNG inputs where randomness is involved.

## Major Features / Commands (initial MVP)

- cetools character create --template `template` [--name NAME] [--export json|yaml|csv]

Create a PC or NPC from SRD rules and templates.

- cetools roll `expression` [--seed SEED] [--adv/--dis]

Parse dice expressions (e.g., 2d6+3) and output detailed roll breakdown. The roll parser and executor MUST support Cepheus-style special rolls including D66. Support the following behaviors:

- `d66` or `D66`: roll two d6 and produce a composite result where the first die is the tens digit and the second die is the units digit (e.g., roll 3 and 5 -> result 35). The CLI output should show the individual die results and the composed value.
- `d66u` / `D66U` (optional flag/suffix): produce an unordered D66 where the two dice are sorted descending before composition (some tables use the unordered convention); implement this as an optional mode and document it in the help.
- Accept both lower- and upper-case `d66` forms and allow an explicit `d66!` or `d66u` variant if users want to force unordered/composed behavior.
The roll output should be consistent and seedable (support `--seed`) so scripts and tests can reproduce results. Ensure exports show both the roll breakdown and the final composed D66 value.

- cetools npc gen [--level N] [--template T] [--export json]

  Generate NPC stats, gear, and a short description.

- cetools world subsector create [--seed SEED] [--export json|yaml]

  Create a subsector or world (star system, world data) suitable for campaign placement. Support X/Y/Z seedable generation, population class, trade codes, TL, and basic planetary descriptors. Exportable for GM use.

- cetools encounter animal gen [--world WORLD] [--challenge CH] [--export json]

  Generate animal encounters appropriate to a world or subsector. Include species, behavior, encounter table roll (including D66 where appropriate), and loot/treasure if applicable.

- cetools encounter patron gen [--tone <friendly|neutral|hostile>] [--level N] [--export json]

  Generate patron NPCs or patron-encounters (patrons who hire or affect PCs): motivations, hooks, likely rewards, obligations, and patron relationship templates.

- cetools encounter balance --party `file|json` --difficulty <easy|avg|hard>

  Suggest encounters based on party composition.

- cetools srlookup `term` [--format json|text]

  Search local SRD index for game terms and output references.

Each command is a thin CLI wrapper that calls into the core Python library (package: `cetools.core`).

## Data Models

- Use `pydantic` for core models: Character, NPC, Item, Encounter, RollResult.
- Serialization: support JSON and YAML (via PyYAML) for exports and imports.
- Config: user config stored in `~/.config/cetools/config.toml` (or XDG equivalent). Use TOML for human friendliness.

### Notation and value formats

- All numeric game-world values displayed to players or referees (attributes, damage, hull points, ranges, etc.) MUST use the Cepheus SRD pseudo-hexadecimal notation where applicable. The CLI should accept both conventional decimal input and pseudo-hex input, but display and export values using the pseudo-hex format by default. Include a small helper in the core library to convert between decimal and pseudo-hex.

Examples:

- Decimal input: `12` -> displayed/exported as pseudo-hex (SRD style) where appropriate.
- Accept both `0xC`-style and SRD pseudo-hex variants as input where reasonable; normalize to the SRD pseudo-hex style for outputs.

Example Character JSON shape (simplified):

```json
{
  "name": "Asha",
  "attributes": {"STR": "A", "DEX": "C", "INT": "B"},
  "skills": {"Pilot": "2"},
  "gear": [ {"name":"Laser Pistol", "count": "1"} ]
}
```

## API / Extensibility Considerations

- Core library must expose pure-Python functions and classes usable from a CLI, tests, and an eventual web server.
- Provide a small HTTP adapter module later (e.g., `cetools.api.app`) that maps library calls to REST endpoints. Keep business logic out of HTTP handlers.
- Design for dependency injection where sensible (e.g., RNG, persistence backends).

Suggested REST endpoints (future):

- GET /v1/srlookup?q=`term`
- POST /v1/characters  (body JSON) -> create character
- POST /v1/rolls  (body {expression, seed}) -> roll result

## Storage and Artifact Handling

- Short-term: local file exports (JSON/YAML/CSV) and local cache of SRD index (JSON file under cache dir).
- Config under XDG paths: `XDG_CONFIG_HOME/cetools/config.toml`, `XDG_DATA_HOME/cetools/cache/srd-index.json`.
- Avoid embedding sensitive data. No remote storage in MVP.

## Input Validation and Errors

- Use `typer` for CLI argument parsing and validation (Typer is built on Click). Typer provides type-driven validation, autogenerated help, and a clean way to wire CLI commands to the core library's functions.
- Use structured exceptions in the core library and map them to user-facing messages in the CLI.
- Exit codes: 0 success, 2 invalid input, 3 resource not found, 4 IO error, 10 internal error.

## Testing Strategy

- Unit tests for core logic (dataclass invariants, generators, roll parser).
- Property-based tests for roll parser and RNG-dependent outputs (use hypothesis if desired but optional).
- Integration tests for CLI invocation (use pytest and click's CliRunner or subprocess smoke tests).

## Quality Gates

- Automated tests run in CI on push. Target coverage: reasonable for core modules (e.g., 70%+ initially).
- Formatting with `black` and linting with `flake8` (configured in `pyproject.toml`).

## Security and Privacy

- No network access required by default. If SRD remote lookups are implemented later, make them opt-in and cache responses.
- Do not log sensitive user information. Keep exported artifacts under user control.

## CLI UX and Internationalization

- Keep messages concise and clear. Support machine-output formats for automation.
- Internationalization is out-of-scope for MVP; design strings so they can be localized later.

## Deliverables (MVP)

1. `cetools` Python package with `cetools.core` library and `cetools.cli` entrypoints.
2. CLI commands: `character create`, `roll`, `npc gen`, `encounter balance`, `srlookup`, `encounter animal gen`, `encounter patron gen`, `world create`, `subsector create`.
3. Local config and SRD index caching.
4. Tests and CI configuration.
5. README with quickstart and examples.

## Milestones (suggested)

- Week 1: Project scaffolding, core models, simple roll parser, basic CLI skeleton.
- Week 2: Character and NPC generators, export/import, config handling.
- Week 3: Encounter balancing, SRD index and search, more tests.
- Week 4: Polish, docs, CI, packaging and release prep.

## Assumptions

- Python >= 3.11 (or 3.13 per repo instructions) is available in target environments.
- Users will run the CLI locally; network access is optional.

<!-- This file contains GitHub Copilot generated content. -->
