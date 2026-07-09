# Psionics Eligibility Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a flat `2D6 ≥ 8` eligibility prerequisite in front of the psionics roll so that only ~42% of characters are ever tested for Psi.

**Architecture:** The gate lives entirely inside `roll_psionics` (Approach A) as the first dice draw. On failure it returns `(0, {})` — shape-identical to the existing non-psionic path — so the `Character` model, generator wiring, and formatter are untouched. Only `roll_psionics`, its tests, two doc lines, and the roll sequences of existing psionics tests change.

**Tech Stack:** Python 3, `uv`, pytest (with coverage gate), Black, flake8, isort.

## Global Constraints

- The eligibility check is a **flat, unmodified `2D6 ≥ 8`** — no DMs of any kind.
- On gate failure, `roll_psionics` returns `(0, {})` and performs **no** Psi roll and **no** talent rolls (short-circuit).
- On gate success, all existing mechanics are unchanged: `Psi = 2D6 − terms_served` (floored at 0), viability at `Psi ≥ 1`, then the ordered talent training loop.
- Roll order inside `roll_psionics` becomes **gate roll → Psi roll → talent rolls**; the gate roll is now the first draw the function consumes.
- No `Character` model, `generator.py` wiring, or `formatter.py` output changes.
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before finishing; coverage on `src/cetools` must stay ≥ 85%.
- Commit messages use Conventional Commits.

---

## File Structure

- `src/cetools/engine/psionics.py` — add `_ELIGIBILITY_TARGET` constant and the gate branch at the top of `roll_psionics`; update the docstring. Sole behavioral change.
- `tests/test_psionics.py` — add gate tests; prepend a passing gate roll to the four existing sequences.
- `tests/test_generator.py` — rework `test_mishap_ended_character_still_rolls_psionics` into a deterministic gate-*pass* case (dishonorable mishap, explicit passing gate → nonzero Psi) and add a gate-*fail* case (`test_gate_failure_yields_non_psionic_character`). See the post-implementation correction note in Task 2.
- `README.md` — one paragraph edit: "every character rolls Psi" is no longer true.

---

### Task 1: Add the eligibility gate to `roll_psionics`

**Files:**
- Modify: `src/cetools/engine/psionics.py:13-34`
- Test: `tests/test_psionics.py`

**Interfaces:**
- Consumes: `DiceRoller.roll(sides, count)` (existing), `characteristic_modifier` (existing).
- Produces: `roll_psionics(terms_served: int, roller: DiceRoller) -> tuple[int, dict[str, int]]` — **unchanged signature**. New behavior: returns `(0, {})` when the first `roller.roll(6, count=2)` draw is `< 8`.

- [ ] **Step 1: Write the failing gate tests**

Add these three tests to `tests/test_psionics.py` (keep the existing `from ... import` lines at the top):

```python
def test_eligibility_gate_failure_skips_all_rolls() -> None:
    # Gate roll 7 (< 8) fails: return (0, {}) immediately. The high follow-up
    # values (which would otherwise yield Psi 12 and learned talents) must never
    # be consumed, proving the gate short-circuits before the Psi roll.
    psi, talents = roll_psionics(
        terms_served=0, roller=SequenceRoller([7, 12, 12, 12, 12, 12, 12])
    )
    assert psi == 0
    assert talents == {}


def test_eligibility_gate_boundary_eight_passes() -> None:
    # Gate roll exactly 8 passes; the next draw (9) is the Psi roll: 9 - 3 = 6.
    psi, _ = roll_psionics(terms_served=3, roller=SequenceRoller([8, 9], default=2))
    assert psi == 6


def test_eligibility_gate_boundary_seven_fails() -> None:
    # Gate roll 7 fails even though the next draw (12) would give a high Psi.
    psi, talents = roll_psionics(terms_served=3, roller=SequenceRoller([7, 12], default=2))
    assert psi == 0
    assert talents == {}
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `uv run pytest tests/test_psionics.py::test_eligibility_gate_failure_skips_all_rolls tests/test_psionics.py::test_eligibility_gate_boundary_eight_passes tests/test_psionics.py::test_eligibility_gate_boundary_seven_fails -v --no-cov`

Expected: FAIL. Against the current (gateless) code the first draw is treated as the Psi roll, so e.g. `test_eligibility_gate_failure_skips_all_rolls` gets `Psi = max(0, 7 - 0) = 7` with learned talents instead of `(0, {})`.

- [ ] **Step 3: Add the gate to `roll_psionics`**

In `src/cetools/engine/psionics.py`, add a constant next to `_TRAINING_TARGET`:

```python
_TRAINING_TARGET = 8
_ELIGIBILITY_TARGET = 8
```

Then change the top of `roll_psionics` so the gate is the first draw and update the docstring. The function body becomes:

```python
def roll_psionics(terms_served: int, roller: DiceRoller) -> tuple[int, dict[str, int]]:
    """Roll Psi strength and learn talents.

    A cetools house rule gates testing: the character must first pass a flat,
    unmodified ``2D6 >= 8`` eligibility check. On failure this returns
    ``(0, {})`` with no Psi or talent rolls. On success, Psi = 2D6 - terms_served,
    floored at 0. A character is psionic when Psi >= 1; only then are talents
    attempted. Each talent is a check
    ``2D6 + PsiDM + talentDM - (previous attempts) >= 8``; successes are granted
    at level 0. Talents are attempted highest-DM-first.
    """
    if roller.roll(6, count=2) < _ELIGIBILITY_TARGET:
        return 0, {}

    psi_strength = max(0, roller.roll(6, count=2) - terms_served)
    talents: dict[str, int] = {}
    if psi_strength < 1:
        return psi_strength, talents

    psi_dm = characteristic_modifier(psi_strength)
    for attempt_index, (name, talent_dm) in enumerate(_TALENTS):
        total = roller.roll(6, count=2) + psi_dm + talent_dm - attempt_index
        if total >= _TRAINING_TARGET:
            talents[name] = 0
    return psi_strength, talents
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `uv run pytest tests/test_psionics.py::test_eligibility_gate_failure_skips_all_rolls tests/test_psionics.py::test_eligibility_gate_boundary_eight_passes tests/test_psionics.py::test_eligibility_gate_boundary_seven_fails -v --no-cov`

Expected: PASS (3 passed).

- [ ] **Step 5: Update the four existing psionics tests to prepend a passing gate roll**

The gate is now the first draw, so each existing sequence needs a passing gate value (`8`) prepended. Replace the four existing test bodies in `tests/test_psionics.py` with:

```python
def test_psi_strength_is_two_d6_minus_terms() -> None:
    # Gate roll 8 passes; Psi roll (9) minus 3 terms = 6.
    psi, _ = roll_psionics(terms_served=3, roller=SequenceRoller([8, 9], default=2))
    assert psi == 6


def test_psi_strength_floors_at_zero_and_skips_training() -> None:
    # Gate roll 8 passes; Psi roll 7 - 10 = -3, floored to 0. The high follow-up
    # values (12) must never be consumed, proving no talent checks are attempted
    # when Psi < 1.
    psi, talents = roll_psionics(
        terms_served=10, roller=SequenceRoller([8, 7, 12, 12, 12, 12, 12])
    )
    assert psi == 0
    assert talents == {}


def test_training_order_and_cumulative_penalty() -> None:
    # Gate roll 8 passes. Psi roll 7, terms 0 -> Psi 7 (PsiDM 0). Then five talent
    # checks each roll 8:
    #   Telepathy(+4, attempt 0): 8+4-0=12 >= 8  -> learned
    #   Clairvoyance(+3, attempt 1): 8+3-1=10 >= 8 -> learned
    #   Telekinesis(+2, attempt 2): 8+2-2=8 >= 8   -> learned
    #   Awareness(+1, attempt 3): 8+1-3=6 < 8      -> not learned
    #   Teleportation(+0, attempt 4): 8+0-4=4 < 8  -> not learned
    psi, talents = roll_psionics(
        terms_served=0, roller=SequenceRoller([8, 7, 8, 8, 8, 8, 8])
    )
    assert psi == 7
    assert talents == {"Telepathy": 0, "Clairvoyance": 0, "Telekinesis": 0}


def test_learned_talents_are_level_zero() -> None:
    _, talents = roll_psionics(
        terms_served=0, roller=SequenceRoller([8, 7, 8, 8, 8, 8, 8])
    )
    assert all(level == 0 for level in talents.values())
```

- [ ] **Step 6: Run the full psionics test file**

Run: `uv run pytest tests/test_psionics.py -v --no-cov`

Expected: PASS (all 7 tests: 4 updated + 3 new).

- [ ] **Step 7: Commit**

```bash
git add src/cetools/engine/psionics.py tests/test_psionics.py
git commit -m "feat: gate psionics testing behind a flat 2D6 8+ eligibility check"
```

---

### Task 2: Reconcile the generator comment and README, then run the full quality gate

**Files:**
- Modify: `tests/test_generator.py` (`test_mishap_ended_character_still_rolls_psionics`, plus a new `test_gate_failure_yields_non_psionic_character`)
- Modify: `README.md:96`

**Interfaces:**
- Consumes: `roll_psionics` with the new gate behavior from Task 1.
- Produces: two deterministic generator-level psionics cases (gate pass and gate fail) plus the README house-rule paragraph.

> **Post-implementation correction (this plan was wrong here).** The plan as first
> written assumed `test_mishap_ended_character_still_rolls_psionics` "still passes
> as-is" and only needed a comment tweak, with assertion
> `psi_strength == max(0, 1 - terms_served)`. That is **incorrect**: a term-1 mishap
> leaves `terms_served == 0`, so after Task 1's gate the default gate draw (`1`)
> fails and forces `psi_strength == 0`, while the assertion's right-hand side
> evaluates to `1` — the test would assert `0 == 1`. During execution the test was
> reworked (below) into a stronger, deterministic pair, and a gate-*failure*
> generator case was added. `test_generated_character_has_psionics`
> (`ConstantRoller(9)`, gate passes at 9) is genuinely unchanged.

- [ ] **Step 1: Rework the mishap psionics test into a deterministic gate-pass case**

`test_mishap_ended_character_still_rolls_psionics` must prove psionics genuinely runs after a mishap — a `psi_strength == 0` assertion would not (a skipped step also yields 0). Force a term-1 **dishonorable** mishap (benefits stripped) with a fully-explicit roller that supplies a passing gate roll (`8`) and a Psi roll (`9`). Replace the whole function with:

```python
def test_mishap_ended_character_still_rolls_psionics() -> None:
    # A dishonorable discharge strips benefits, yet psionics is still rolled on
    # the sole return path. This roller forces a term-1 dishonorable mishap
    # (survival fail -> mishap roll 4), then supplies a passing gate roll
    # (8 >= 8) and a Psi roll of 9: psi_strength = max(0, 9 - 0) = 9. Proves the
    # eligibility gate and Psi roll run regardless of how the career ended — a
    # skipped psionics step would leave psi_strength 0 and fail this test.
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 4, 6, 6, 8, 9], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert result.mishap.discharge_type == "dishonorable"
    assert result.benefits == []
    assert result.psi_strength == 9
    assert result.talents == {"Telepathy": 0, "Clairvoyance": 0}
```

- [ ] **Step 1b: Add a deterministic gate-*failure* generator case**

Add this test immediately after the one above (a minimal pair — identical roller except the final gate draw is `7` instead of `8`):

```python
def test_gate_failure_yields_non_psionic_character() -> None:
    # Minimal pair with test_mishap_ended_character_still_rolls_psionics: identical
    # roller except the gate roll is 7 (< 8) instead of 8, so the eligibility gate
    # fails end-to-end and the character is non-psionic (psi 0, no talents) even
    # though generation ran through the psionics step.
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 4, 6, 6, 7], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.psi_strength == 0
    assert result.talents == {}
```

- [ ] **Step 2: Run the generator test file to confirm it is green**

Run: `uv run pytest tests/test_generator.py -v --no-cov`

Expected: PASS (no failures; the reworked gate-pass test, the new gate-fail test, and the unchanged `test_generated_character_has_psionics` all hold).

- [ ] **Step 3: Update the README psionics paragraph**

In `README.md`, replace the paragraph at line 96 (begins "Every character rolls a Psi characteristic...") with:

```markdown
Characters are tested for psionics under a cetools house rule layered on the optional [SRD psionics rule](https://evolvedexperiment.github.io/cepheus-srd/): a character must first pass a flat `2D6 ≥ 8` eligibility check to be tested at all (roughly 42% do), which keeps psionic characters a genuine minority. Characters who fail the check, or who roll `Psi` 0, show the bare UPP as before; psionic characters (`Psi ≥ 1`) append it as a hyphenated pseudo-hex suffix, e.g. `5A3B93-6`. Any talents learned during training appear on an optional `Psionics:` line, alphabetical, each at level 0. Psionic training's cash cost and time are abstracted away — mustering-out cash and age are unaffected.
```

- [ ] **Step 4: Run the full quality gate**

Run: `uv run black . && uv run flake8 src tests && uv run pytest`

Expected: Black reports files unchanged or reformats cleanly; flake8 reports no errors; pytest passes with `src/cetools` coverage ≥ 85%.

- [ ] **Step 5: Commit**

```bash
git add tests/test_generator.py README.md
git commit -m "docs: document psionics eligibility gate house rule"
```

---

## Self-Review

**Spec coverage:**
- Flat `2D6 ≥ 8` gate, no DMs → Task 1, Step 3 (`_ELIGIBILITY_TARGET`, unmodified `roller.roll(6, count=2)`). ✓
- Gate failure returns `(0, {})` with no Psi/talent rolls → Task 1, Steps 1 & 3. ✓
- Gate success runs unchanged mechanics → Task 1, Step 3 (rest of function untouched) + updated existing tests, Step 5. ✓
- Roll order gate → Psi → talents → Task 1, Step 3. ✓
- No model/generator/formatter *behavior* change → confirmed: only `psionics.py` behavior changes. Generator *tests* were updated (one reworked, one added) to cover the gate-pass and gate-fail paths end-to-end (Task 2, Steps 1–1b). ✓
- Boundary (8 passes, 7 fails) → Task 1, Step 1 (two boundary tests). ✓
- Existing `SequenceRoller` tests get a passing gate roll prepended → Task 1, Step 5. ✓
- Coverage ≥ 85% → Task 2, Step 4. ✓
- House rule documented → design doc (committed) + README (Task 2, Step 3). ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"/vague steps — every code and command step is concrete. ✓

**Type consistency:** `roll_psionics` signature and return type `tuple[int, dict[str, int]]` are identical before and after; `_ELIGIBILITY_TARGET` and `_TRAINING_TARGET` are module-level ints; `SequenceRoller(values, default)` matches `tests/conftest.py`. ✓
