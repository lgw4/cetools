# Quickstart: Validating Fuel-Limited Jump Drive Rating

**Feature**: `013-fuel-limited-jump-drive` | **Date**: 2026-07-26

Runnable scenarios that prove the feature end to end. Each maps to a user story or success
criterion in [spec.md](./spec.md). Behavioural details live in
[contracts/jump-drive-fit.md](./contracts/jump-drive-fit.md); allocation order lives in
[data-model.md](./data-model.md).

## Prerequisites

```bash
uv sync
```

Run everything below from the repository root.

---

## Scenario 0 — Confirm the defect first (red)

The whole feature is a bug fix, so start by watching it fail. The survey script is the
measurement instrument for every success criterion.

```bash
uv run python specs/013-fuel-limited-jump-drive/scripts/survey_drive_fit.py
```

**Expected before the fix** (exit status 1):

```text
jump_tons strictly increasing in letter order: True
rating non-decreasing in letter order, every hull: True
starved (hull, maneuver, power) combos over the full cross product: 0

--- 2000 seeds, standard hull ---
SC-001/002 short-fuelled (expect 0):         111
SC-001 FR-014 starved hulls (expect 0):      0
SC-003 negative cargo (expect 0):            0
SC-004 'zero Jump-n' in prose (expect 0):    111
FR-004 drive not lightest at rating (0):     1087
SC-006 non-reproducible seeds (expect 0):    0
SC-005 small craft reproducible over 2000 seeds: True

FAIL
```

**Expected after the fix** (exit status 0): every counted line reads `0`, and the last line reads
`PASS`. The `1087` on the FR-004 line is the population that rule normalizes — see research.md Part
D for why it is more than half the sweep.

SC-007 is not on this list. It compares each seed against the *pre-change* generator, which the
script cannot see; it is asserted by the pytest sweep against `baseline/pre_change_sweep.json`.

---

## Scenario 1 — Every generated starship can make at least one jump

Covers **US1**, FR-001, FR-002, FR-003, SC-001, SC-002.

```bash
uv run pytest tests/test_ship_generator.py -k "jump" -v --no-cov
```

**Expected**: every test passes. The sweep tests assert, for each seed, that
`ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating` and that
`ship.assumed_jump_distance == ship.jump_rating`, counting any FR-014 starved-hull ship separately
rather than as a pass.

Spot-check the spec's Overview scenario by hand. That ship is a 100-ton hull carrying maneuver
drive A and power plant C, which leaves 72 tons for the jump drive and its fuel; it must mount a
Jump-4 drive, not a Jump-6 one. (The 56 tons its description reports is fuel *tankage*, 50 of jump
fuel plus 6 of power-plant fuel, not the drive budget.)

```bash
uv run python -c "
from cetools.engine.rolls import RandomRolls
from cetools.engine.ships.generator import generate_ship
for seed in range(50):
    s = generate_ship(RandomRolls.seeded(seed), hull_size=100)
    assert s.assumed_jump_distance == s.jump_rating, (seed, s.design.jump_code)
print('100-ton hulls: every drive is fully fuelled')
"
```

---

## Scenario 2 — The description reports an honest, non-zero jump range

Covers **US2**, FR-007, SC-004.

```bash
uv run pytest tests/test_ship_description.py tests/test_ship_generator.py -k "description or prose or zero" -v --no-cov
```

Then read one for yourself:

```bash
uv run cetools ship generate --seed 42
```

**Expected**: the fuel sentence reads "... supports the power plant for two weeks and *one* Jump-N
jump", never "zero". The drive letter in the drives sentence, the `Jump-N` in the performance
clause, and the jump count in the fuel sentence all agree.

---

## Scenario 3 — Determinism, small craft and authored designs are undisturbed

Covers **US3**, FR-009 through FR-012, SC-005, SC-006.

```bash
uv run pytest tests/test_ship_generator.py tests/test_ship_builder.py tests/test_ship_design.py -v --no-cov
```

**Expected**: all pass, including

- the same seed generating an equal `Ship` twice (FR-009, SC-006);
- small-craft output reproducible and unchanged (FR-010, SC-005);
- an authored design with an explicit short `jump_distance` building exactly as written, never
  silently corrected (FR-012);
- all six of the repository's authored example designs building to `Ship` values field-equal to
  their pre-change builds (SC-010) — the five under `specs/010-starship-generator/examples/` and
  `specs/011-universal-ship-format/examples/subsidized-merchant.toml`.

Confirm the authored-design boundary directly — the Beowulf's figures must not move:

```bash
uv run python -c "
from cetools.engine.ships import build_ship, load_design
s = build_ship(load_design('specs/010-starship-generator/examples/free-trader.toml'))
print(s.total_cost, s.cargo_tons, s.crew.total)   # 29.772 135 5
"
```

---

## Scenario 4 — The draw order is still intact

Covers FR-008, and re-establishes feature 012's guard (research.md Part G).

```bash
uv run pytest tests/test_ship_generator.py -k "sc008" -v --no-cov
```

**Expected**: passes. The recording-`Rolls` test asserts that `RollName.SHIP_NAME` is the final
draw of every generation, drawn exactly once, on both the starship and small-craft paths. This
replaces the feature-012 pinned-design comparison, which this feature legitimately invalidates for
54% of seeds; it tests the invariant directly instead of by proxy.

---

## Scenario 5 — The FR-014 starved-hull fallback

Covers FR-014. **Not reachable through `generate_ship`** — no combination of hull, maneuver code
and power code in the current tables starves a hull (research.md Part E, and the survey script's
`starved ... : 0` line). It is therefore exercised against the fit helper directly:

```bash
uv run pytest tests/test_ship_generator.py -k "starved or fallback" -v --no-cov
```

**Expected**: passes. The test calls `_fit_jump_drive` with a budget too small for any legal drive
and asserts the lowest-rated legal drive comes back, no exception is raised, and the resulting
design still builds within its hull (FR-013).

---

## Full quality gate

Before opening the PR, the four commands from AGENTS.md, plus the survey:

```bash
uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
uv run python specs/013-fuel-limited-jump-drive/scripts/survey_drive_fit.py
```

**Expected**: Black clean, flake8 silent, pytest green with `src/cetools` coverage at or above 85%,
`check_docs.py` clean (README and CONTEXT.md wording for the generator must move with the
behaviour), and the survey exiting 0 with `PASS`.
