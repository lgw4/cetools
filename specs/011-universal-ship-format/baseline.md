# Pre-change quality-gate baseline (T001)

Recorded on branch `011-universal-ship-format` at commit `2b29fd2` before any
implementation work, so SC-005 ("every pre-existing test passes unmodified") can be
verified at the end (T053).

## Gate results

| Gate | Command | Result |
|------|---------|--------|
| Format | `uv run black --check .` | PASS — 121 files unchanged |
| Lint | `uv run flake8 src tests` | PASS — no findings |
| Tests | `uv run pytest` | PASS — **1176 passed**, coverage 99.07% (floor 85%) |
| Docs | `uv run python scripts/check_docs.py` | PASS — symbols resolve, README examples run, module map complete |

**Baseline passing test count: 1176.**

## Per-file counts for the files this feature touches

| Test file | Baseline count | Expected change |
|-----------|----------------|-----------------|
| `tests/test_cli.py` | 86 | modified (T022, T034, T045) |
| `tests/test_ship_tables.py` | 75 | modified (T002, T003, T008, T009) |
| `tests/test_ship_models.py` | 67 | modified (T004, T011) |
| `tests/test_ship_builder.py` | 66 | modified (T005) |
| `tests/test_ship_design.py` | 59 | modified (T032) |
| `tests/test_ship_generator.py` | 19 | unchanged |
| `tests/test_ship_sheet.py` | 17 | **deleted** (T031) |
| `tests/test_ship_prose.py` | — | new (T006) |
| `tests/test_ship_description.py` | — | new (T014–T021, T033, T037–T041, T044, T051) |

At T053 the total must be **1176 minus the 17 `test_ship_sheet.py` tests, plus the new
coverage added by this feature** — with no pre-existing assertion weakened or retargeted.
The only permitted edits to existing tests are the three named in T008, T009 and T011:
the `min_tl` → `tl` rename, the `CONFIG_MODIFIERS` → `CONFIGURATIONS` retarget, and the
two `Ship(...)` construction sites gaining `tech_level`.

## Addendum, recorded at the end of Phase 2

T008–T011 required more existing-test edits than the task list enumerated, all of the
same mechanical kind: a row dataclass that gains a required column breaks every
construction of it, not only the ones the tasks named. No assertion was weakened,
retargeted or removed — each site gained the new columns and kept its original
`==`/`approx` comparison.

| Site | Edit |
|---|---|
| `test_ship_tables.py` full-row equality assertions for `ElectronicsRow`, `MountRow`, `BayRow`, `ScreenRow` | gained `name`/`plural`/`tl`/`dm` |
| `test_ship_tables.py` SC-006 monkeypatch rows (`FittingRow` ×2, `BayRow`, `ScreenRow`, `AmmoRow`, `ArmorOptionRow`, `WeaponRow`) | gained the same columns |
| `test_ship_builder.py` SC-006 monkeypatch rows (`FittingRow` ×3) | gained `name`/`plural` |
| `test_ship_sheet.py` two `Ship(...)` constructions | gained `tech_level` (the file is deleted at T031 regardless) |
| `test_ship_tables.py::test_config_modifiers_match_srd` | renamed `test_configuration_cost_modifiers_match_srd`; same three modifier values asserted |

Verified by diffing collected test node IDs against `HEAD`: no pre-existing test
disappeared apart from that one rename.

**Phase 2 end state: 1383 passed**, coverage 99.15%; black, flake8 and `check_docs.py`
all green. `CONTEXT.md` line 128's `ArmorRow.min_tl` reference was corrected here rather
than at T049, because `check_docs.py` fails on the dangling symbol the moment T008 lands;
T049 still owns retiring the "ship sheet" vocabulary.

## T053 end state (SC-005 verified)

| Gate | Command | Result |
|------|---------|--------|
| Format | `uv run black .` | PASS — 123 files unchanged |
| Lint | `uv run flake8 src tests` | PASS — no findings |
| Tests | `uv run pytest` | PASS — **1586 passed**, coverage 99.15% (floor 85%) |
| Docs | `uv run python scripts/check_docs.py` | PASS |

Collected test node IDs were diffed against the baseline commit `2b29fd2`: **431 added, 21
removed**, and every removal is accounted for as a replaced rendering test.

| Removed | Count | Why |
|---|---|---|
| `tests/test_ship_sheet.py::*` | 17 | file deleted at T031 |
| `test_ship_tables.py::test_config_modifiers_match_srd` | 1 | renamed `test_configuration_cost_modifiers_match_srd` (same three modifiers asserted) |
| `test_cli.py::test_ship_build_prints_sheet_and_exits_0` | 1 | → `test_ship_build_prints_a_heading_and_one_paragraph_and_exits_0` |
| `test_cli.py::test_ship_generate_hull_reflected_in_sheet` | 1 | → `test_ship_generate_hull_reflected_in_description` |
| `test_cli.py::test_ship_generate_reports_seed_on_stderr_when_omitted` | 1 | → `test_ship_generate_reports_seed_on_stderr_and_never_in_the_paragraph` |

No pre-existing assertion about a computed ship value was weakened, retargeted or removed
(FR-032, SC-005).

## Coverage detail for `src/cetools/engine/ships/`

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| `__init__.py` | 6 | 0 | 100% |
| `builder.py` | 216 | 1 | 99% |
| `design.py` | 306 | 0 | 99% |
| `generator.py` | 192 | 2 | 98% |
| `models.py` | 261 | 2 | 99% |
| `sheet.py` | 64 | 1 | 98% |
| `tables.py` | 116 | 0 | 100% |
