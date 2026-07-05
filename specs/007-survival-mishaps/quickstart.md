# Quickstart: Validating Survival Mishaps

These scenarios prove the feature end-to-end. All are runnable against the plan's
design without needing referee/session context (this rule is always-on per the
spec's Assumptions). Run `uv sync` first if you haven't (see `AGENTS.md`).

## 1. A failed survival roll produces a character, never a failure (P1 / SC-001)

```python
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate_character
from cetools.engine.models import Character
from tests.conftest import SequenceRoller

# generate_character consumes 6 rolls for characteristics + 1 for the
# qualification check before the survival check is ever reached — pad
# exactly that many passing values first, then the low roll that fails
# survival (mirrors tests/test_generator.py::test_survival_fail_returns_generation_failure).
roller = SequenceRoller([10] * 7 + [2], default=6)
result = generate_character(NAVY_CAREER, roller=roller)

assert isinstance(result, Character)          # never GenerationFailure for survival
assert result.mishap is not None
assert result.age == 20                        # 18 + 2 (half term), not 22
```

Expected: a complete `Character`, not a `GenerationFailure`. Repeat for each of
the six `SURVIVAL_MISHAPS_TABLE` rows by controlling the mishap-table roll (the
1D6 immediately following the failed survival check) to hit each `roll` value
1–6, and confirm `result.mishap.roll` / `discharge_type` / `imprisoned` /
`injury_reductions` / `injury_crisis` match `data-model.md`'s table for that row.
For every row except outcome 5, confirm `result.age == 20` (18 + 2). For outcome 5
specifically (`imprisoned=True`), confirm `result.age == 24` (18 + 2 + 4 — the
extra imprisonment years, per `research.md` D9).

## 2. Mishap details are visible on the printed record (P2 / SC-002)

```python
from cetools.formatter import format_character

print(format_character(result))
```

Expected: output includes a trailing `Mishap: ...` line (see
`contracts/mishap-output.md`) describing discharge type, injury (if any), and debt
(if any) — sufficient to answer "what happened" without reading `mishap` fields
directly.

## 3. Benefits/pension match the outcome (P3 / SC-003)

Using `generate_career_character` (which forces qualification so a long career is
reachable), drive a roller to: (a) complete 5+ terms normally, then (b) fail
survival on a later term with each mishap outcome, and check:

| Outcome | Expected `benefits` | Expected `pension` | Expected `debt` |
|---|---|---|---|
| 1 (injured) | prior terms' rolls only | preserved (if ≥5 prior terms) | 0, or crisis amount if a stat hit 0 |
| 2 (honorable) | prior terms' rolls only | preserved | 0 |
| 3 (honorable, legal battle) | prior terms' rolls only | preserved | 10,000 |
| 4 (dishonorable) | `[]` | `None` | 0 |
| 5 (dishonorable, imprisoned) | `[]` | `None` | 0 |
| 6 (medical, injury) | prior terms' rolls only | preserved | 0, or crisis amount |

Also confirm the mustering-out roll count equals `terms_served` (prior completed
terms only) in every row — the mishap term itself must never contribute a roll.

## 4. Injury crisis never kills (FR-009 edge case)

Force an Injury table roll that reduces a physical characteristic to 0 (e.g. a
character with Strength 1 hit by Injury row 2's 1D6 with a roll of 6). Confirm:
`characteristics["Strength"] == 1` (restored, not 0), `result.mishap.injury_crisis
is True`, and `result.debt` is a multiple of 10,000 between 10,000 and 60,000.

## 5. Statistical distribution across outcomes (SC-004)

```python
from collections import Counter
from cetools.engine.dice import RandomDiceRoller
# ... generate 10,000 characters forced to fail survival on term 1, e.g. via a
# roller wrapper that always fails the survival check but rolls the mishap table
# with RandomDiceRoller ...
counts = Counter(c.mishap.roll for c in characters)
for roll in range(1, 7):
    assert 1500 <= counts[roll] <= 1834  # 1667 +/- 10%
```

This is the acceptance test for SC-004 and should be written as a real (if slower)
test in `tests/test_mishaps.py`, using `RandomDiceRoller` for the mishap/injury rolls
specifically while forcing the survival check itself to fail deterministically.

## 6. CLI end-to-end

```bash
uv run cetools character generate --career navy
```

Run repeatedly (or with a seeded/deterministic roller in a test) until a mishap
occurs; confirm exit code `0` (success — mishaps are not CLI failures) and that
stdout includes the `Mishap:` line from step 2.

## 7. Uniform application across entry points (FR-011)

Repeat scenario 1 through `draft_character()` (draft table) as well as
`generate_career_character()` (direct/qualified career generation) — both must
route through the same `generate_character` mishap-resolution path and never
return `GenerationFailure` for a survival-roll failure.
