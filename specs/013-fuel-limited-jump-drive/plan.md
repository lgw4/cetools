# Implementation Plan: Fuel-Limited Jump Drive Rating

**Branch**: `013-fuel-limited-jump-drive` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-fuel-limited-jump-drive/spec.md`

## Summary

Random ship generation buys the jump drive before it knows what fuel is left, so 5.5% of seeds
produce a starship whose tankage cannot complete a single jump at its advertised rating — a Jump-6
drive delivering, per its own description, "zero Jump-6 jumps".

The fix is one new pure function in `engine/ships/generator.py` and a reordering of four lines
around it. Compute the tonnage budget remaining after the mandatory systems *before* paying for the
jump drive; then pick the highest-rated drive, rated no higher than the one drawn, whose own tonnage
plus one full jump of fuel fits that budget — always taking the lightest letter at any given rating.
Freed tonnage flows on to fuel, fittings and cargo. No draw is added or moved, so the seam that
makes a seed reproducible is untouched.

`builder.py` is not modified. The correction is generation *policy*, not an SRD rule, so a
hand-authored short-legged design still builds exactly as written (FR-012).

Two findings from Phase 0 shape the plan beyond the spec:

- **FR-014 is unreachable.** Enumerating the full cross product of hull x maneuver code x power code
  — every combination a draw could ever produce — yields zero starved hulls, a stronger result than
  the spec's 2000-seed sample. The branch is still implemented, but it is tested against the fit
  helper directly rather than hunted for through `generate_ship` (research.md Part E).
- **The feature-012 baseline guard must be replaced, not repaired.** FR-004's lightest-drive rule
  moves 54% of seeds, not the 5.5% the downgrade alone would move. The pinned-design proxy is
  swapped for a test that asserts the invariant it stood for directly: `SHIP_NAME` is the last draw
  of every path (research.md Parts D and G).

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: None new. Standard library only (`math`); the feature adds no dependency
to `pyproject.toml`.

**Storage**: N/A — no persistence. The TOML design schema is unchanged, so designs written before
this feature still load and round-trip.

**Testing**: pytest, with coverage enforced at 85% on `src/cetools`. New tests extend
`tests/test_ship_generator.py`, `tests/test_ship_tables.py`, `tests/test_ship_description.py` and
`tests/test_ship_builder.py`.

**Target Platform**: Cross-platform CLI and importable library; no platform-specific code.

**Project Type**: Single project — engine library (`src/cetools/engine/`) plus a thin CLI delivery
layer (`src/cetools/cli/`).

**Performance Goals**: Unchanged. `generate_ship` must stay under 0.1 s per call (existing
`test_a_single_generation_completes_in_under_a_tenth_of_a_second`). The fit search scans at most 24
drive letters with no allocation of consequence — immeasurable against the existing cost.

**Constraints**:

- Consume no additional `Rolls` draw, in any branch (FR-008). This is the binding constraint: a
  single inserted draw shifts every later draw and silently changes what a seed produces.
- Never raise on any legal input; the fit is a total function (FR-014, contract C6).
- Never modify `builder.py` — an authored design must be unaffected (FR-012).
- Never change the small-craft path (FR-010, SC-005).

**Scale/Scope**: One new module-private function (~15 lines), a reordering of ~6 lines in
`generate_ship`, one retired test replaced by two stronger ones, and doc updates. Validated over a
2000-seed sweep and the full 2,404-combination drive cross product.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
| --- | --- | --- |
| **I. SRD-Fidelity** | PASS | No rule, table or terminology changes. Jump fuel stays at 0.1 x hull x rating and drive legality stays as tabulated; both are read, never edited. "Prefer the lightest drive at a rating" is generator policy — the SRD does not say how a referee picks a drive for a random ship. No deviation to record (research.md Part H). |
| **II. Library-First** | PASS | The entire change lives in `src/cetools/engine/ships/generator.py`. No CLI import, no I/O, no clock, no environment read. `generate_ship` remains directly importable and callable. |
| **III. CLI Interface** | PASS | `src/cetools/cli/ship.py` is not touched. Command syntax, flags and exit codes are unchanged; only the prose the engine hands back differs. |
| **IV. Test-First** | PASS | Every task in the Phase 2 breakdown is written test-first. The red state is already demonstrated and measured: the survey script reports 111 short-fuelled ships and exits 1 today (quickstart.md Scenario 0). |
| **V. Data-Driven Extensibility** | PASS, with a strengthening | The search reads `DRIVE_COSTS` and `DRIVE_PERFORMANCE` generically and hardcodes no letter, hull or rating. It could have relied on the tables' letter ordering; instead it selects the lightest drive by explicit comparison, and a new table test pins the two ordering invariants so an SRD row that broke them would fail loudly rather than silently mis-select (research.md Part C). |

**Complexity**: No new abstraction, no new module, no new type, no new dependency. One private
function in the file that already owns component selection. The `Complexity Tracking` table below is
empty because there is nothing to justify.

**Post-Phase-1 re-check**: PASS, unchanged. The Phase 1 design confirmed rather than expanded the
scope — `data-model.md` introduces no persisted type, and `contracts/jump-drive-fit.md` records that
no public signature moves. The one design decision that could have grown the surface (adding a
`RecordingRolls` adapter to `engine/rolls.py`) was resolved *against* the engine: the wrapper serves
one test and no production caller, so it lives in `tests/`, per the Constitution's "no abstractions
until a second concrete use case exists" (research.md Part G).

## Project Structure

### Documentation (this feature)

```text
specs/013-fuel-limited-jump-drive/
├── plan.md                      # This file
├── spec.md                      # Feature specification (input)
├── research.md                  # Phase 0 output
├── data-model.md                # Phase 1 output
├── quickstart.md                # Phase 1 output
├── contracts/
│   └── jump-drive-fit.md        # Phase 1 output
├── scripts/
│   └── survey_drive_fit.py      # SC-001..SC-006 measurement instrument
├── baseline/                    # all three created during implementation
│   ├── pre_change_sweep.json    # T002 — pre-change standard-hull + small-craft capture (SC-005, SC-007)
│   ├── authored_designs.json    # T003 — pre-change build of all six authored examples (SC-010)
│   └── designs.json             # T027 — re-pinned seed-to-ship anchor for *future* features
└── tasks.md                     # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   └── ships/
│       ├── generator.py         # MODIFIED — _fit_jump_drive() + allocation reorder
│       ├── names.py             # MODIFIED — docstring: baseline guard reference
│       ├── builder.py           # UNCHANGED — authored designs must not move (FR-012)
│       ├── tables.py            # UNCHANGED — read, never edited
│       ├── description.py       # UNCHANGED — presentation only; its arithmetic is correct
│       ├── models.py            # UNCHANGED — no schema change
│       └── prose.py             # UNCHANGED
└── cli/
    └── ship.py                  # UNCHANGED

tests/
├── test_ship_generator.py       # MODIFIED — fit-search, sweep, draw-order and FR-014 tests
├── test_ship_tables.py          # MODIFIED — drive-table ordering invariants
├── test_ship_description.py     # MODIFIED — no generated starship reports zero jumps
└── test_ship_builder.py         # MODIFIED — authored designs unmoved (FR-012, SC-010)

README.md                        # MODIFIED — generator section: the one-jump guarantee
CONTEXT.md                       # MODIFIED — generator vocabulary: fuel-limited drive selection
```

**Structure Decision**: The existing single-project layout is kept unchanged. This feature is a
defect fix inside one existing engine module, so it adds no directory and no module. The `scripts/`
and `baseline/` directories under `specs/013-fuel-limited-jump-drive/` follow the precedent set by
`specs/012-ship-names/baseline/` — feature-scoped artifacts that support the tests without entering
the package.

## Implementation Approach

Three sequenced pieces. Full contracts in
[contracts/jump-drive-fit.md](./contracts/jump-drive-fit.md); allocation order in
[data-model.md](./data-model.md).

### 1. The fit search — `generator._fit_jump_drive(hull_tons, drawn_code, budget) -> str`

A pure function over the tables. Reduce the hull's legal drives rated at or below the drawn one to
the lightest letter per distinct rating (FR-004, applied unconditionally); return the highest-rated
of those whose `jump_tons + 0.1 * hull_tons * rating` fits the budget (FR-003); fall back to the
lowest-rated candidate when none fits (FR-014). Total by construction — the drawn code is itself a
candidate, so the fallback always has an answer.

Contract postconditions C1–C8 are the acceptance criteria for this function's tests.

### 2. The allocation reorder in `generate_ship`

Split today's single `remaining` into a pre-drive `budget` and a post-drive `remaining`, calling the
fit between them. The `jump_distance` arithmetic that follows is kept **verbatim**: under FR-003 it
now resolves to the full rating, and under FR-014 it degrades to partial fuel with no special case —
which is precisely the fallback's specified behaviour. The `max(0.0, ...)` clamp stays as the FR-013
safety net.

`_select_drive_codes` is not touched. It still draws jump, maneuver and power codes in that order,
so FR-008 holds by construction rather than by inspection. The power plant is deliberately not
re-derived: its legality constraint is a floor, and lowering the jump rating only relaxes it
(research.md Part F).

### 3. The draw-order guard

Retire `test_naming_is_purely_additive_against_the_pre_feature_baseline`, which this feature
legitimately invalidates, and replace it with two things:

- a `RecordingRolls` wrapper defined in `tests/`, asserting over a seed sweep on both paths that
  `RollName.SHIP_NAME` is the final draw and is drawn exactly once — the invariant itself rather
  than a proxy for it;
- a re-pinned `specs/013-fuel-limited-jump-drive/baseline/designs.json`, generated at this feature's
  implementation commit, keeping a byte-for-byte seed-to-ship anchor for *future* features.

`specs/012-ship-names/baseline/designs.json` stays in the repository as history; the docstring
references to it in `names.py` and `generator.py` are updated to point at the new guard, and
`scripts/check_docs.py` must stay green across those edits.

## Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| An accidental extra draw silently changes every seed's output | The fit function takes no `Rolls` parameter, so it cannot draw (contract C7). The `RecordingRolls` draw-order test catches an insertion anywhere else. |
| The 54% output shift masks a real regression | SC-007 is asserted per seed, not in aggregate: every ship that was already fully fuelled must keep its rating, hull, maneuver drive and power plant, and any drive-letter change must be to a strictly lighter drive at the same rating. |
| FR-014 ships in the sweep are counted as passes | The survey script and the sweep tests classify a starved hull explicitly and report it on its own line, per SC-001. Expected zero; a non-zero count fails loudly rather than being absorbed. |
| Coverage falls below 85% because FR-014 is unreachable through generation | The fallback is tested against `_fit_jump_drive` directly with a synthetic budget (quickstart.md Scenario 5), so the branch is covered without a reachable seed. |
| A future SRD table edit breaks the ordering the search assumes | The search selects the lightest drive by explicit comparison, not by letter order, and a new `test_ship_tables.py` invariant test pins both orderings. |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All five principles pass; no complexity to justify.
