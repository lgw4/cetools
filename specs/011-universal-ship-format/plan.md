# Implementation Plan: Universal Ship Description Format

**Branch**: `011-universal-ship-format` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-universal-ship-format/spec.md`

## Summary

Replace the label-per-line ship sheet with the SRD's Universal Ship Description Format: a
`TL<n> <name>` heading line, a blank line, and one prose paragraph whose sixteen sentence slots
run in the SRD's prescribed order. A new `engine/ships/description.py` holds one builder per
slot, each returning `str | None` so equipment the ship lacks drops out whole and the
paragraph stays grammatical; a slot normally yields one sentence, and the weapons slot yields
one more per ammunition group, so a paragraph carrying ammunition runs past sixteen sentences
while still having sixteen slots; a new `engine/ships/prose.py` holds the number, plural, list and
article primitives the SRD's style demands, with no ship knowledge, so FR-022 through FR-025 are
testable without building a ship. `engine/ships/sheet.py` and `render_sheet` are deleted, per
FR-002 and the feature 006 precedent.

The renderer spells no component itself: every nameable row in `tables.py` gains its SRD prose
`name` (and an explicit `plural` where it follows a count), so adding an SRD row is a data-only
edit. The same tables gain the SRD's `tl` column wherever the source tabulates one, and
`build_ship` derives `Ship.tech_level` as the highest among the fitted components — overridable
by a new optional `tech_level` on the design, which joins a new optional `purpose`. No computed
value changes: this feature is presentation plus two input fields.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: None new. Typer (CLI only, unchanged); stdlib `dataclasses` and
`tomllib` for the engine. No inflection, templating or i18n library — plurals are explicit data
columns, not derived (see [research.md Part E](./research.md#part-e--display-names-in-the-rules-data)).

**Storage**: N/A. `render_description` is pure; TOML design files are user inputs and optional
outputs, unchanged in role.

**Testing**: pytest with coverage (suite fails below 85% on `src/cetools`). `prose.py` is
table-driven unit tested directly; `description.py` is tested against paragraphs built from the
checked-in example designs and from fixtures pinned to each spec edge case; `CliRunner` drives
the two CLI commands; the SC-003 determinism check renders an equal pair of ships and compares
bytes.

**Target Platform**: Cross-platform CLI (macOS/Linux/Windows), Python library.

**Project Type**: Single project — engine library plus Typer CLI (existing layout).

**Performance Goals**: Rendering a description is string assembly over a bounded component set;
effectively instant, well under the 0.1 s per-ship budget feature 010 set.

**Constraints**: Engine code MUST NOT import from `cli/`. `render_description` MUST be a pure,
total function of the `Ship` alone — no seed, clock, locale or ambient state — and MUST be
byte-identical for equal ships (FR-003, SC-003). No computed ship value may change (FR-032), so
every existing builder, generator, TOML and cost test must pass unmodified (SC-005). Component
wording MUST come from the component's data row (FR-031, SC-007). No tech level may be invented
where the SRD tabulates none (FR-028a).

**Scale/Scope**: Bounded — one paragraph of at most ~20 sentences per ship, over the fixed
component catalog.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. SRD-Fidelity | ✅ PASS *(two recorded deviations)* | The USDF template and all 20 Chapter 9 worked examples were read verbatim and are quoted in [research.md](./research.md) Parts A and B. Every table was read column by column to establish which categories carry a tech level and which do not (Part D); none was invented. Where the template and the worked examples disagree, the examples win, per the spec's Assumptions. Two deliberate deviations are recorded below. |
| II. Library-First | ✅ PASS | All rendering in `src/cetools/engine/ships/`; `render_description` is importable and callable with no CLI. `prose.py` and `tables.py` import nothing from the package; `description.py` imports only `models`, `tables` and `prose`. Engine has zero `cli/` imports. |
| III. CLI Interface | ✅ PASS | `cli/ship.py` changes by one symbol — it calls `render_description` instead of `render_sheet`. Argument parsing, `--toml`, `--out`, seed-on-stderr and exit codes (0 success, 1 user-facing failure on stderr) are untouched. No game logic enters CLI code. |
| IV. Test-First | ✅ PASS | Red-green-refactor throughout. `prose.py` gets table-driven tests per FR-022/022a/023/024/025 before implementation; each of the sixteen sentence-slot builders gets its assertion and each spec edge case its fixture before `description.py` exists; the tech-level derivation is tested through `build_ship` before the column additions land. `tests/test_ship_sheet.py` is replaced by `tests/test_ship_description.py` and `tests/test_ship_prose.py`. |
| V. Data-Driven Extensibility | ✅ PASS | This feature *increases* data-drivenness: the outgoing sheet hardcoded component wording (`f"{fit.kind} x{fit.quantity}"`, `f"{fit.type.value} {fit.percent}%"`); the new renderer reads `name`/`plural`/`tl`/`dm` columns instead. Hangars are identified by `tons_per_vehicle_ton is not None` and fuel processors by `unrefined_fuel_per_ton`, never by key comparison, so a new SRD row of either kind stays a data-only edit (SC-007). Crew position spellings and their print order move into a `CREW_POSITIONS` table. |

### Deliberate deviations (Principle I)

**1. Counts above ten are digits, departing from the SRD in the 11–99 band.**
The SRD writes "twelve staterooms" in one vessel and "25 staterooms" in another, "fifty
hardpoints" and "a crew of 18" — no consistent rule can be extracted, so FR-022 fixes the
boundary at ten and knowingly departs from some examples above it. Recorded in
[research.md Part C](./research.md#part-c--number-and-text-style) and in the spec's own
Assumptions.

*Resolved, no longer a deviation*: FR-022a originally said tonnage is *always* digits, against
every Chapter 9 example's "two tons allocated to fire control". Put to the user during
planning, the SRD-faithful reading was chosen, and **the spec has since been amended** —
FR-022a is narrowed to the hull displacement and the rated values, and new FR-022b puts
tonnage in running prose under the count rule. Spec and SRD now agree.

**2. A small craft's computer sentence says "cockpit", against the SRD's own examples.**
FR-027 requires it. The SRD's small-craft writeups print "Adjacent to the bridge is a computer
Model 1" in the same paragraph as "There is a one-man cockpit", which is a slip in the source —
the small-craft rules replace the bridge with a cockpit. Reproducing the slip would emit a
paragraph that contradicts itself. Recorded in
[research.md Part F](./research.md#part-f--values-the-description-states-that-the-builder-already-computes).

### Two SRD contradictions resolved (Principle I: documented, not house-ruled)

- **Fire-control tonnage** is reported as the ship's hardpoint count, which is what all 20
  examples print — including ships with unused hardpoints. cetools folds a turret's fire control
  into the turret's own ton, so no `LineItem` sum reproduces the figure, and adding one would
  change computed tonnage (forbidden by FR-032). Presentation only.
- **Emergency low berths** are not offered as passenger capacity. Chapter 8 states they "will
  not carry passengers"; Chapter 9 prints "four emergency low passengers". This is a rules
  conflict, not a phrasing one, so the worked-examples-win assumption does not apply and the
  rule governs — as the spec's own edge case ("must not offer capacity the ship does not have")
  independently requires.

**Complexity**: two new engine modules (`description.py`, `prose.py`) where one would do, and a
renamed public function. Both justified in Complexity Tracking below.

**Result**: PASS — no unjustified violations. The two deviations are recorded with rationale as
Principle I requires, and the FR-022a narrowing they once called for has since landed in the
spec (FR-022a as amended, plus the new FR-022b).

**Post-Phase-1 re-check**: PASS. The design added no dependency, no delivery-layer coupling and
no hardcoded component wording; every Phase 1 decision made the renderer *more* data-driven, not
less. The import-direction invariants in
[contracts/engine-api.md](./contracts/engine-api.md) keep Principle II mechanical.

## Project Structure

### Documentation (this feature)

```text
specs/011-universal-ship-format/
├── plan.md                        # This file
├── spec.md                        # Feature specification (clarified)
├── research.md                    # Phase 0: SRD template + examples digest, decisions
├── data-model.md                  # Phase 1: new fields, table columns, rendering pipeline
├── quickstart.md                  # Phase 1: runnable validation guide
├── contracts/
│   ├── description-format.md      # The sentence-by-sentence output contract
│   ├── engine-api.md              # Public-surface delta (render_description, Ship, ShipDesign)
│   └── design-schema.md           # TOML schema delta (purpose, tech_level)
├── examples/                      # New fixture design(s) exercising purpose + tech_level
└── tasks.md                       # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/cetools/
├── cli/
│   └── ship.py             # MODIFIED: call render_description instead of render_sheet
└── engine/
    └── ships/
        ├── __init__.py     # MODIFIED: export render_description; drop render_sheet
        ├── tables.py       # MODIFIED: name/plural/tl/dm columns; CONFIGURATIONS, CREW_POSITIONS
        ├── models.py       # MODIFIED: ShipDesign.purpose, ShipDesign.tech_level, Ship.tech_level
        ├── builder.py      # MODIFIED: derive Ship.tech_level (no costing/tonnage change)
        ├── design.py       # MODIFIED: parse and dump purpose + tech_level (lossless round trip)
        ├── generator.py    # (unchanged)
        ├── prose.py        # NEW: number words, plurals, list joining, articles, float formatting
        ├── description.py  # NEW: render_description(ship) -> USDF heading + paragraph
        └── sheet.py        # DELETED: replaced by description.py

tests/
├── test_ship_prose.py        # NEW: FR-022/022a/023/024/025 rules, table-driven
├── test_ship_description.py  # NEW: all 16 sentences, omission, grouping, every edge case
├── test_ship_sheet.py        # DELETED: replaced
├── test_ship_tables.py       # MODIFIED: name/plural/tl invariants; CREW_POSITIONS ↔ Crew fields
├── test_ship_models.py       # MODIFIED: purpose/tech_level shape validation
├── test_ship_builder.py      # MODIFIED: tech-level derivation, override, no-TL categories
├── test_ship_design.py       # MODIFIED: round trip with the two new keys
└── test_cli.py               # MODIFIED: both commands print a heading + paragraph

README.md                     # MODIFIED: replace the sample sheet with the sample description
CONTRIBUTING.md               # MODIFIED: module map — sheet.py → description.py, prose.py
CONTEXT.md                    # MODIFIED: ship-description vocabulary; retire "ship sheet";
                              #   and retire the now-false claim that armor and computer tech
                              #   levels are "checked nowhere, since v1 has no tech-level
                              #   model" — this feature builds that model. check_docs.py
                              #   cannot catch a prose claim that has merely gone stale.
```

**Structure Decision**: The existing `engine/ships/` package is kept as-is and gains two
modules. `description.py` sits exactly where `sheet.py` did in the dependency graph — the sole
reader of `Ship` for presentation, imported by nothing in the engine — so no import direction
changes. `prose.py` sits below it with no package dependencies at all.

The docs edits are not optional bookkeeping: `scripts/check_docs.py` fails if a backticked
symbol in README, CONTEXT, CONTRIBUTING or an ADR no longer exists, and README's ship section
currently shows a full sheet as a `console` block. Renaming `render_sheet` therefore requires
the docs to move in the same change — which is the gate working as designed.

## Complexity Tracking

| Choice | Why Needed | Simpler Alternative Rejected Because |
|--------|------------|-------------------------------------|
| Separate `prose.py` alongside `description.py` | FR-022, FR-022a, FR-023, FR-024 and FR-025 are number-and-grammar rules independent of any ship, and they carry most of this feature's edge cases (crew of one, zero cargo, fractional cost, three-item joins). A module with no ship knowledge makes them unit-testable without constructing a `Ship`. | Private helpers inside `description.py` are reachable only through a whole rendered paragraph, so a plural or rounding bug surfaces as "the paragraph is wrong" instead of naming the rule it broke — and Principle IV wants the failing test to point at the defect. |
| Explicit `plural` columns instead of deriving plurals | The SRD's plurals are not uniformly regular ("armory" → "armories", "laboratory" → "laboratories"), so a `+ "s"` rule is logic a new SRD row can silently break — defeating SC-007, which says adding a row must produce correct wording with no logic change. | A suffix rule is one line but wrong for two existing rows; an inflection library is a new runtime dependency for a bounded, fully-known catalog. |
| Renaming `render_sheet` → `render_description` and deleting `sheet.py` | FR-002 makes USDF *the* output, following feature 006 where the Universal Character Format replaced the per-characteristic output. "Sheet" would name a prose paragraph, and CONTEXT.md's "ship sheet" vocabulary would then mean two things. | Keeping the old name is a smaller diff but leaves the codebase's own vocabulary lying; keeping both renderers doubles the SC-003 determinism surface and the test matrix for a second format nothing asks for. |
| `Ship.tech_level` computed by `build_ship` rather than by the renderer | Tech level is a computed ship value like crew, cost and hull points, and FR-028a's derivation is a rule worth testing without rendering prose. Keeping it out of the renderer also keeps `description.py` free of table walking. | Deriving it inside `render_description` would put an SRD rule in the presentation layer, and FR-028's designer override would have to be re-read from `design` at render time — the derivation would then be untestable except through a paragraph. |
| Two special `FittingRow` columns (`counted_in_tons`, `unrefined_fuel_per_ton`) | The SRD prints "five tons of fuel processors (processes 100 tons … per day)" and "two tons of luxuries" against "four detention cells", and FR-017 names the fuel-processor throughput explicitly — so neither column is speculative. Each drives one generic renderer branch, mirroring the `tons_per_vehicle_ton` idiom already in `FittingRow`. | A per-kind branch in the renderer violates FR-031; inferring "counted in tons" from `tons == 1.0` is coincidental and breaks the moment the SRD adds a one-ton countable fitting. |

*The two Principle I deviations are recorded in Constitution Check above, not here; the table
above records structural choices only.*
