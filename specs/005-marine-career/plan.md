# Implementation Plan: Marine Career

**Branch**: `005-marine-career` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-marine-career/spec.md`

## Summary

Add the Marine career to cetools by defining a new `Career` dataclass instance
(`MARINE_CAREER`) in the engine, registering it in the career registry under the key
`"marine"`, and correcting `DRAFT_TABLE` index 1 (roll 2) from the "navy" placeholder to
`"marine"` — all without touching engine or CLI logic. The CLI's existing normalization,
"did you mean" suggestion, and registry-derived help text already work unchanged (Constitution
§III/§V), so this feature is pure data addition plus targeted test updates, including four
pre-existing tests that used the literal string `"marine"` as their unrecognized-career
placeholder (now `"merchant"`, per spec Clarifications).

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: typer (CLI), dataclasses (stdlib)

**Storage**: N/A

**Testing**: pytest with `--cov`, minimum 85% coverage

**Target Platform**: macOS/Linux CLI

**Project Type**: Library (`src/cetools/engine/`) + CLI (`src/cetools/cli/`, unchanged)

**Performance Goals**: N/A (interactive single-character generation)

**Constraints**: Coverage ≥ 85%; zero changes to engine generation logic (Constitution §V);
zero changes to CLI logic (no new normalization/help-text code needed — registry-derived
mechanisms already handle a fourth career)

**Scale/Scope**: One new career data module, one registry edit, test additions/updates across
three existing test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| §I SRD-Fidelity | PASS | All tables in FR-002–FR-005 match SRD exactly, cross-checked against `NAVY_CAREER`/`SCOUT_CAREER` conventions (e.g. `"Explorer's Society"` spelling). No deviations. |
| §II Library-First | PASS | `MARINE_CAREER` lives in `engine/careers/marine.py`; no game logic enters CLI code. |
| §III CLI Interface | PASS | Zero CLI changes required — `_CANONICAL_CAREERS`, the "did you mean" logic, and error formatting are all registry-derived and already generic. |
| §IV Test-First | MANDATORY | All new/changed tests must go red before `marine.py`/`registry.py` are written; full suite green before PR. |
| §V Data-Driven Extensibility | PASS | Adding Marine requires only a new `Career` instance and one registry key plus one `DRAFT_TABLE` entry — zero engine changes. |

**Complexity Tracking**: No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-marine-career/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── career-registry.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/cetools/
├── engine/
│   └── careers/
│       ├── base.py          # unchanged — Career + RankEntry dataclasses
│       ├── navy.py          # unchanged
│       ├── scout.py         # unchanged
│       ├── aerospace.py     # unchanged
│       ├── marine.py        # NEW — MARINE_CAREER instance
│       └── registry.py      # EDIT — add marine key, fix DRAFT_TABLE index 1
└── cli/
    └── character.py         # unchanged — registry-derived logic handles Marine automatically

tests/
├── test_marine_career.py    # NEW — field-level validation of MARINE_CAREER
├── test_careers.py          # EDIT — registry/draft-table assertions for the marine key
├── test_cli.py              # EDIT — "marine"→"merchant" placeholder (FR-012); add Marine to
│                             #        canonical-name and valid-careers-list assertions
└── test_generator.py        # EDIT — "marine"→"merchant" placeholder (FR-012)
```

**Structure Decision**: Single-project layout (Option 1), consistent with features 001–004.
`engine/careers/marine.py` is an exact peer of `navy.py`, `scout.py`, and `aerospace.py`. No CLI
directory changes are needed, unlike feature 003 (Aerospace), which introduced the
normalization/help-text/did-you-mean mechanisms this feature reuses unchanged.

## Complexity Tracking

*No violations — table intentionally omitted.*

## Implementation Notes

### Draft table correction

The current `DRAFT_TABLE` in `registry.py` is:

```python
("aerospace system defense", "navy", "navy", "navy", "scout", "navy")
```

`draft_character()` indexes it as `DRAFT_TABLE[roll - 1]` for a 1D6 roll, so index 1 is roll
result 2 — the Marine slot per FR-008. Index 1 must change from `"navy"` to `"marine"`. Indices
2 and 5 (rolls 3 and 6 — Maritime System Defense and Surface System Defense) remain `"navy"`
placeholders per spec Assumptions; this feature touches only index 1.

The existing test `test_draft_table_other_entries_are_navy` in `test_careers.py` asserts that
every index except 0 and 4 is `"navy"` — it must be updated to also exclude index 1 (now
`"marine"`).

### Placeholder-test resolution (FR-012, superseding original clarification)

Four pre-existing tests used the literal string `"marine"` as an unrecognized/unimplemented
career placeholder. Planning discovered that the spec's original replacement,
`"surface system defense"`, scores 0.766–0.826 similarity against the already-registered
`"aerospace system defense"` under `difflib.get_close_matches(cutoff=0.6)` (shared
`"... system defense"` suffix), which flips the CLI into its "did you mean" near-miss path
instead of the "no close match" path that `test_career_unknown_stderr_message_exact` asserts
exactly. Per user decision (2026-07-01), the placeholder is `"merchant"` instead (~0.3
similarity to all four registered keys — see spec Clarifications, second entry, and updated
FR-012). Three of the four tests use this value in all-lowercase form (`"merchant"`); the
fourth — `test_career_unknown_original_value_in_message` — uses the capitalized `"Merchant"`
instead, since it specifically verifies the CLI echoes the original, unnormalized casing of the
input rather than the normalized form (see FR-012):

- `tests/test_cli.py`: `test_career_unknown_exits_1` (`"merchant"`),
  `test_career_unknown_stderr_message_exact` (`"merchant"`),
  `test_career_unknown_original_value_in_message` (`"Merchant"`)
- `tests/test_generator.py`: `test_draft_character_unimplemented_career_returns_failure`
  (`"merchant"`)

Two additional pre-existing tests not covered by FR-012 hardcode the sorted canonical-name list
and must be updated to include `"Marine"` (alphabetically between "Aerospace System Defense" and
"Navy"):

- `tests/test_cli.py::test_career_unknown_stderr_message_exact` — expected string becomes
  `"Unknown career 'merchant'. Valid careers: Aerospace System Defense, Marine, Navy, Scout"`
- `tests/test_cli.py::test_career_no_match_valid_careers_format` — expected string becomes
  `"Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, Marine, Navy, Scout"`

No CLI code changes are needed for either — `_CANONICAL_CAREERS` in `character.py` is derived
from `CAREER_REGISTRY.values()` at import time (FR-009), so it picks up Marine automatically.

### Rank bonus-skill retention through commission (FR-013)

`_grant_rank_bonus()` (`generator.py`) is called once at career entry for rank 0
(`generator.py:191-192`) and again for each rank reached via commission or advancement
(`generator.py:239`, `generator.py:246`). Skills accumulate in a `dict[str, int]` that is never
cleared between calls, so a Marine character commissioned to rank 1 (Lieutenant) keeps the rank
0 Zero-G-1 bonus skill gained at career entry — the same mechanism already exercised by Navy's
rank 0 `"Zero-G"` and Scout's rank 0 `"Piloting"`. No engine change is needed; FR-013 documents
this existing behavior so User Story 2's acceptance scenario (rank 0 "always has" Zero-G-1)
remains unambiguous once commissioning is factored in.

### Registry key and material benefit spelling

`"marine"` (lowercase, no hyphen) follows the existing key convention (`"navy"`, `"scout"`,
`"aerospace system defense"`). The `--career` flag's existing
`.strip().lower().replace("-", " ")` normalization resolves `"Marine"`, `"marine"`,
`"MARINE"`, and `"marine"`-with-hyphens-if-any to this key unchanged (FR-007) — no CLI edit
needed. Per FR-005, `material_benefits[6]` uses `"Explorer's Society"` (matching
`SCOUT_CAREER.material_benefits[4]`), not the `"Explorers' Society"` variant.
