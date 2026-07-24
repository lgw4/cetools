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
