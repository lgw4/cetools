# Implementation Plan: Ship Names

**Branch**: `012-ship-names` | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-ship-names/spec.md`

## Summary

Randomly generated ships currently render as "Unnamed Ship". This feature gives every one of them
a curated name drawn from mythology and folklore, written science fiction, and science fiction
film and television.

A new `engine/ships/names.py` holds the whole feature: a `ShipName` frozen dataclass pairing a
name with its `Tradition` and, for fiction-tradition entries, the `BasisKind` plus reference that
qualifies it under FR-016; an ordered `SHIP_NAMES` tuple of ~160 such entries; and
`generate_ship_name(rolls)`, one `rolls.choose` and nothing more. The catalogue is content, not
logic — adding a name is a one-line data edit.

The change to existing code is deliberately two lines wide. `generate_ship` draws a name as the
**last** `Rolls` call on each of its two paths and passes it to the `ShipDesign` it already
constructs. That placement is the whole determinism argument: `RandomRolls` wraps a single
`random.Random` stream, so a draw inserted anywhere but the end would shift every later draw and
change the hull, drives and armament a seed produces. Drawing last leaves the stream prefix
untouched, which is what makes naming *purely additive* (FR-010a) rather than merely
reproducible. To prove it rather than assert it, `baseline/designs.json` was captured at commit
`d387b70` before any implementation, holding the dumped designs for 100 pre-feature seeds; the
SC-008 test clears the name from each regenerated design and compares to that record.

Nothing else needs building. `ShipDesign.name` already exists, `render_description` already
prints it, and `dump_design`/`load_design` already round-trip it, so FR-012 through FR-015 hold
the moment the field is populated — and `build_ship` never assigns a name, so building from a
file stays deterministic and an author's own name is never overwritten. The CLI does not change
at all.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: None new. Typer (CLI, untouched); stdlib `dataclasses` and `enum` only.
No name-generation, markov or corpus library — FR-003 forbids assembling names from fragments,
so the catalogue is a literal.

**Storage**: N/A. The catalogue is an in-module tuple, not a loaded data file (see
[research.md Part B](./research.md#part-b--where-the-catalogue-lives)). TOML design files are
unchanged in role and format.

**Testing**: pytest with coverage (suite fails below 85% on `src/cetools`). `names.py` is tested
directly through `ScriptedRolls` for selection and through catalogue-wide property assertions for
the FR-008/FR-009/FR-016b invariants; `generate_ship` naming is tested on both paths;
`CliRunner` covers `ship generate` output and the generate → export → build round trip; SC-008 is
tested against the pre-captured `baseline/designs.json`.

**Target Platform**: Cross-platform CLI (macOS/Linux/Windows), Python library.

**Project Type**: Single project — engine library plus Typer CLI (existing layout).

**Performance Goals**: One uniform pick over a 160-element tuple per ship; immeasurable against
the 0.1 s per-ship budget feature 010 set.

**Constraints**:

- Engine code MUST NOT import from `cli/`.
- The name draw MUST be the last `Rolls` call on every path of `generate_ship`, so no other
  seeded outcome shifts (FR-010a, SC-008). This is the feature's load-bearing invariant.
- Selection MUST go through the `Rolls` seam — no `random` call, no seed access, no hashing
  (FR-011).
- Names MUST be catalogue entries, never assembled from fragments (FR-003).
- Entries MUST be ASCII and MUST pass the existing `_validate_author_prose` check, since they are
  interpolated verbatim into the description's single unwrapped paragraph (FR-018).
- `build_ship` MUST remain free of naming (FR-015); no computed ship value may change.

**Scale/Scope**: One new engine module (~200 lines, mostly data), one new `RollName` member, two
changed lines in `generator.py`, three new exports, one new test file. ~160 catalogue entries.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. SRD-Fidelity | ✅ PASS *(not engaged)* | The SRD publishes no ship-name table and no naming rule ([research.md Part F](./research.md#part-f--srd-fidelity)), so there is no rule to be faithful to and none to bend. This feature adds no mechanic and changes no computed value — tonnage, cost, crew, tech level and build time are untouched. No deviation recorded. |
| II. Library-First | ✅ PASS | Everything lives in `src/cetools/engine/ships/names.py`. `generate_ship_name` is importable and callable with no CLI, and is exported from `cetools.engine.ships` alongside `generate_ship`. The module imports only `cetools.engine.rolls` — not `models`, not `tables`, not `cli`. |
| III. CLI Interface | ✅ PASS | **Zero CLI changes.** `cli/ship.py` is not edited: no new option, argument, exit code or stream. Only the content of `generate`'s output differs, because the engine now populates a field the renderer already printed. No game logic enters CLI code. |
| IV. Test-First | ✅ PASS | Red-green-refactor throughout. The catalogue-invariant tests (size, per-tradition floors, the 50% cap, uniqueness, ASCII, basis presence) are written against an empty or partial catalogue and fail first; `generate_ship_name`'s selection test is written before the function; the SC-008 additivity test is written against the already-captured baseline before `generator.py` is touched, and fails only if the draw lands in the wrong place. |
| V. Data-Driven Extensibility | ✅ PASS | The catalogue is a tuple of frozen dataclass rows, exactly as `tables.py` encodes SRD rows. Adding a name is a one-line data edit with zero engine change, and — because the tests assert *floors* (≥150, ≥20 per tradition, ≤50%) rather than exact counts — zero test edit. `Tradition` and `BasisKind` are closed enums so FR-016b's audit is a membership test rather than free-text inspection. |

No violations. **Complexity Tracking is empty by design.**

### Notes on two decisions a reviewer will want justified

**Why a new module rather than `tables.py`.** `tables.py` is scoped by its own docstring to SRD
Chapter 8 tables, every row traceable to a printed table. Ship names appear nowhere in the SRD.
Mixing invented content into the SRD-fidelity module would blur the one boundary Principle I
depends on. `engine/names.py` and `engine/worlds/naming.py` set the precedent for a per-domain
naming module.

**Why no name option on `generate_ship` or the CLI.** The spec's Assumptions rule it out, and a
referee who wants a specific name already has a path: export the design and set the name there.
Adding a parameter for a use case the spec placed out of scope is the speculative abstraction the
constitution's simplicity posture forbids.

## Project Structure

### Documentation (this feature)

```text
specs/012-ship-names/
├── plan.md                       # This file
├── spec.md                       # Feature specification
├── research.md                   # Phase 0 output
├── data-model.md                 # Phase 1 output
├── quickstart.md                 # Phase 1 output
├── contracts/
│   └── name-catalogue.md         # Phase 1 output: library + CLI contract
├── baseline/
│   └── designs.json              # 100 pre-feature designs (seeds 0-49, both paths) @ d387b70
└── tasks.md                      # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   ├── rolls.py                  # MODIFIED: + RollName.SHIP_NAME
│   └── ships/
│       ├── __init__.py           # MODIFIED: + 4 exports
│       ├── names.py              # NEW: Tradition, BasisKind, ShipName,
│       │                         #      SHIP_NAMES, generate_ship_name
│       ├── generator.py          # MODIFIED: name drawn last on both paths
│       ├── models.py             # unchanged (ShipDesign.name already exists)
│       ├── description.py        # unchanged (already renders design.name)
│       ├── design.py             # unchanged (already round-trips name)
│       ├── builder.py            # unchanged (never assigns a name)
│       └── tables.py             # unchanged (SRD data only)
└── cli/
    └── ship.py                   # unchanged

tests/
├── test_ship_names.py            # NEW: catalogue invariants + selection
├── test_ship_generator.py        # MODIFIED: naming on both paths, SC-008 baseline
├── test_ship_description.py      # MODIFIED: generated ships never render "Unnamed Ship"
└── test_cli.py                   # MODIFIED: generate names it, build still does not

CONTRIBUTING.md                   # MODIFIED: module map gains ships/names.py
README.md                         # MODIFIED: starship section notes generated ships are named
```

**Structure Decision**: The existing single-project layout, unchanged. Game content and logic sit
in `src/cetools/engine/ships/`; the CLI in `src/cetools/cli/` is untouched; tests mirror the
package in `tests/`. The one new module follows the naming-module precedent already set by
`engine/names.py` (characters) and `engine/worlds/naming.py` (worlds).

## Implementation Sequence

The order matters, because the additivity guarantee must be provable before the code that could
break it is written.

1. **Baseline** — already captured. `baseline/designs.json`, 100 designs at `d387b70`.
2. **`RollName.SHIP_NAME`** — one enum member.
3. **Types and an empty-ish catalogue** — `Tradition`, `BasisKind`, `ShipName`, plus the
   invariant tests, which fail on size and per-tradition floors.
4. **`generate_ship_name`** — one `rolls.choose`, tested through `ScriptedRolls`.
5. **Catalogue content** — three passes, one per tradition, each entry's basis recorded as it is
   added. This is the bulk of the work and the only part that is research rather than code.
6. **`generate_ship` naming** — the two-line change, gated by the SC-008 baseline test.
7. **Description, CLI and round-trip tests** — confirming FR-012 through FR-015 hold with no
   further code.
8. **Docs and the four-command quality gate.**

## Risks

| Risk | Mitigation |
|------|------------|
| A future contributor inserts a new draw mid-path, silently changing every seed's ship | The `baseline/designs.json` regression test fails loudly and names the seed. Documented in `names.py` and `generator.py` docstrings. |
| The 42-entry floor for written SF proves hard under FR-016 | Sampled during Phase 0 across nine authors and found comfortably sufficient ([research.md C3](./research.md#c3--feasibility-check)). If a tradition falls short, the floor that must hold is FR-008's 20, not the 42 target. |
| A catalogue entry is mis-sourced | Every fiction entry records its basis kind and reference; the test proves the fields are *present and well-formed*, and the reference makes the claim reviewable by a human in one line rather than by re-research. |
| Catalogue growth breaks tests | Tests assert floors and caps, never exact counts. |

## Complexity Tracking

No Constitution Check violations. Nothing to justify.
