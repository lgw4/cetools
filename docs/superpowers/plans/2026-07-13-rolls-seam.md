# Rolls Seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the engine's randomness seam up from `DiceRoller.roll(sides, count)` to the domain — a named `check` / `two_d6` / `d6` / `choose` interface — so that tests address rolls by intent rather than by position in a die sequence.

**Architecture:** A new module `src/cetools/engine/rolls.py` holds the `Rolls` protocol, the `RollName` enum, and (in phase B) the two adapters. All four engine modules (`generator`, `mishaps`, `psionics`, `names`) call the seam; nothing else in the engine touches `random`. See `CONTEXT.md` for the domain terms this plan uses.

**Tech Stack:** Python 3, `uv`, pytest (with coverage gate), Black, flake8, isort.

## Why this exists

Today `DiceRoller.roll(sides, count)` is one line of implementation behind a two-parameter interface — and that is not the whole interface. Every caller and every test also has to know the engine's **roll order**, an unwritten contract that is what actually breaks. Hence:

```python
roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 4, 6, 6, 11, 9], default=6)
```

38 of these in `tests/test_generator.py` alone. Insert one roll anywhere in the engine and they all shift.

Three other symptoms fall out of the same cause:

- The check rule `2D6 + DM >= target` is reimplemented in three modules (`generator._check`, `psionics` twice).
- Uniform choice is faked by rolling a die with as many faces as the list has entries — `roller.roll(len(careers))` is a d24; `roller.roll(len(FIRST_NAMES))` is a d12.
- `_check` is this module trying to be born, trapped as a private in `generator.py`.

## Global Constraints

- **Phase A changes no rules.** The shim consumes dice in exactly the same order and arity as today, so the existing end-to-end tests pass **unchanged**. That green run is the proof, and it is the whole point of splitting the work in two.
- The caller computes its own DM. The seam knows about chance, not about characteristics.
- Every roll site is named with a `RollName` member. No bare strings.
- `ScriptedRolls`: a scalar means always; a list is consumed in order and then **falls back to the per-verb default**; `CHARACTERISTIC` takes a list in `STAT_NAMES` order.
- Candidate #3 (the generator's nine private-symbol test imports) is **out of scope**. Mixing it in would muddy the "tests unchanged" proof.
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before finishing; coverage on `src/cetools` must stay ≥ 85%.
- Commit messages use Conventional Commits.

## The 21 roll names

Derived from the 24 roll sites in the engine. This enum is the index of every random decision the rules make.

| verb | names |
| --- | --- |
| `check` | `QUALIFICATION`, `SURVIVAL`, `COMMISSION`, `ADVANCEMENT`, `PSI_GATE`, `PSI_TALENT` |
| `two_d6` | `CHARACTERISTIC`, `AGING`, `REENLISTMENT`, `PSI_STRENGTH` |
| `d6` | `SKILL_TABLE`, `SKILL_ENTRY`, `CASH_BENEFIT`, `MATERIAL_BENEFIT`, `SHIP_SHARES`, `DRAFT`, `MISHAP`, `INJURY`, `INJURY_AMOUNT`, `INJURY_DEBT` |
| `choose` | `CAREER`, `BACKGROUND_SKILL`, `INJURY_STAT`, `FIRST_NAME`, `LAST_NAME` |

Two sites share `ADVANCEMENT` (the post-commission path and the standing-rank path) and two share `INJURY` (it is `min` of two rolls). Both are correct: the list semantics handle repeated names.

Note `REENLISTMENT` is a `two_d6`, **not** a check — it needs the raw value, because a natural 12 forces an extra term.

## File Structure

**Phase A**
- `src/cetools/engine/rolls.py` — new. `RollName`, the `Rolls` protocol.
- `src/cetools/engine/dice.py` — add `LegacyDiceRolls`, the temporary shim satisfying `Rolls` over the old `DiceRoller`, plus `_as_rolls` coercion. Deleted entirely in phase B.
- `src/cetools/engine/generator.py` — 13 roll sites move to the seam; `_check` becomes a one-line DM lookup over `rolls.check`.
- `src/cetools/engine/mishaps.py` — 6 roll sites.
- `src/cetools/engine/psionics.py` — 3 roll sites; stops reimplementing the check rule.
- `src/cetools/engine/names.py` — 2 roll sites; the two d12s become `choose`.
- `tests/test_rolls.py` — new. The check arithmetic, previously tested via `generator._check`.
- `tests/test_generator.py` — **3 lines only** (the `_check` tests at 41/46/52, which relocate to `test_rolls.py`).

**Phase B**
- `src/cetools/engine/rolls.py` — add `RandomRolls` and `ScriptedRolls`.
- `tests/conftest.py` — delete `ConstantRoller`, `SmartRoller`, `SequenceRoller`.
- 9 test files migrate from scripted die sequences to named rolls.
- `src/cetools/engine/dice.py` — deleted.

---

## Phase A — move the engine to the seam, keep the tests green

### Task 1: Add `rolls.py` and the shim

**Files:**
- Create: `src/cetools/engine/rolls.py`
- Modify: `src/cetools/engine/dice.py`
- Test: `tests/test_rolls.py`

**Interfaces:**
- Produces: `RollName` (StrEnum, 21 members); `Rolls` (Protocol: `check`, `d6`, `two_d6`, `choose`); `LegacyDiceRolls(DiceRoller)` satisfying `Rolls`.
- The shim's die consumption must be **identical** to today's engine: `check` → `roll(6, count=2)`; `two_d6` → `roll(6, count=2)`; `d6` → `roll(6)`; `choose(items)` → `items[(roll(len(items)) - 1) % len(items)]`.

- [ ] **Step 1: Write `tests/test_rolls.py`**, covering the check arithmetic (the three tests moved out of `test_generator.py`: meets target, below target, DM applied) plus `choose` wrapping and `d6`/`two_d6` arity.
- [ ] **Step 2: Run it — expect ImportError.**
- [ ] **Step 3: Write `rolls.py` and `LegacyDiceRolls`.** Add `_as_rolls(source)`: pass a `Rolls` through, wrap a `DiceRoller`, and default `None` to `LegacyDiceRolls(RandomDiceRoller())`.
- [ ] **Step 4: Run `tests/test_rolls.py` — expect green.**

### Task 2: Move the four engine modules onto the seam

**Files:** `generator.py`, `mishaps.py`, `psionics.py`, `names.py`

**Interfaces:**
- Public entry points (`generate_character`, `roll_psionics`, `resolve_survival_mishap`, `generate_name`, `draft_character`, `generate_career_character`, `random_career_character`, `roll_until_qualified`) accept `DiceRoller | Rolls | None` and coerce via `_as_rolls`. This is what keeps the existing tests green; the union is temporary and dies with phase B.
- Private helpers take `Rolls` and also coerce, so the ~30 direct helper calls in `test_generator.py` keep working untouched.
- `_check(rolls, characteristics, stat, target, name)` gains the `name` argument. This is the one signature that cannot stay compatible — hence the 3 relocated tests.

- [ ] **Step 1: `names.py`** — two `choose` calls. Run `tests/test_names.py`, expect green, unchanged.
- [ ] **Step 2: `psionics.py`** — `PSI_GATE` and `PSI_TALENT` become `check`; `PSI_STRENGTH` becomes `two_d6`. The `2D6 >= 11` and `2D6 + dm >= 8` arithmetic is deleted from this module. Run `tests/test_psionics.py`, expect green, unchanged.
- [ ] **Step 3: `mishaps.py`** — `MISHAP`, `INJURY` (×2), `INJURY_AMOUNT`, `INJURY_DEBT` become `d6`; `INJURY_STAT` becomes `choose`. Run `tests/test_mishaps.py`, expect green, unchanged.
- [ ] **Step 4: `generator.py`** — the remaining 13 sites. Run `tests/test_generator.py`; expect green **except** the 3 `_check` tests, which are deleted here (they now live in `test_rolls.py`).
- [ ] **Step 5: Full quality gate.** `uv run black . && uv run flake8 src tests && uv run pytest`. Expect the entire suite green with only those 3 lines changed.
- [ ] **Step 6: Commit.** `refactor: move engine randomness behind a named Rolls seam`

---

## Phase B — replace the scripted die sequences

- [x] `RandomRolls` (production) and `ScriptedRolls` (tests) in `rolls.py`.
- [x] Migrate the 10 roller-using test files.
- [x] Delete `dice.py`, `LegacyDiceRolls`, `as_rolls`, the `DiceRoller | Rolls` unions, and the three fake rollers in `conftest.py`. The `roller` parameter is renamed `rolls` throughout.
- [x] Add the aging-ladder tests (see below).

### What phase B found

Two things surfaced only because the tests stopped counting dice.

**Three tests were passing for the wrong reason.** `test_{maritime,surface,aerospace}_commission_roll_failure_stays_at_rank_0` used `SequenceRoller([12], default=1)`, and their comments claimed the leading `12` was the survival check. It was not: it was consumed by the first *background-skill draw*. Survival therefore rolled a 1 and **failed**, the commission roll was never made at all, and the tests passed via the survival-mishap path — asserting `rank == 0` for entirely the wrong reason. Rewritten as `checks={SURVIVAL: True, COMMISSION: False}`, they now exercise the path their names describe. This is precisely the failure mode the seam exists to prevent: a positional die sequence silently means something other than what its comment says.

**The aging ladder was only covered by accident.** Old die sequences wandered into the `-3`…`-6` rungs incidentally; scripting by name stopped that, and generator coverage fell to 94%. It is now covered on purpose, one test per rung, and generator coverage is 99% — above where it started. Writing those tests turned up a rules fact worth recording: **the `-6 or worse` rung is unreachable in a normal career.** `2D6` bottoms out at 2 and the term cap is 7, so the worst reachable roll is `2 - 7 = -5`. Only a natural 12 on re-enlistment, which forces an 8th term, reaches `2 - 8 = -6`.

### Follow-up: the skill-table selection bias (fixed)

Found during phase A, fixed after phase B — deliberately kept out of both, because it changes generated characters and would have destroyed phase A's behaviour-preservation proof.

`_roll_skill` selected a skill table with `(d6 - 1) % len(tables)`. With Education ≥ 8 there are four tables, so a d6 modulo 4 mapped to `0,1,2,3,0,1` — Personal Development and Service Skills came up **twice as often** (≈33% each) as Specialist and Advanced Education (≈17% each).

The SRD is explicit that this is not a roll at all:

> **Choose** one of the Skills and Training tables for this career and roll on it.

So the table is a *choice*, which cetools automates, and automating a choice means picking uniformly. `SKILL_TABLE` moves from a `d6` to a `choose` and now sits with the other uniform picks in `RollName`. Measured over 20,000 skill rolls at Education 8, all four tables now come up at 25%. Rolling *on* the chosen table remains a real 1D6, and the `% 6` that guarded it is gone — a career's tables are validated at exactly 6 entries, so it never did anything.

### Open: a second SRD discrepancy, not investigated

The same SRD paragraph says: *"If you gain a skill as a result and you do not already have levels in that skill, take it at level 1."* `_apply_skill_entry` grants it at level **0** (`skills.get(entry, -1) + 1`). Skills already held (including the level-0 service skills from basic training) do increment correctly. Whether the level-0 grant is a deliberate cetools house rule or a bug has not been established — it is not recorded anywhere.

## Self-Review

**Design decisions, all settled with the user:**
- Scope: all four engine modules; `DiceRoller` is deleted (phase B). ✓
- Addressing: named checks; the scripted adapter is keyed by name. ✓
- Naming: every roll site named, not just checks. ✓
- `choose` returns the item; `_draw_distinct` keeps its own distinctness rule (it is a background-skills rule, not a randomness rule). ✓
- Safety: `RollName` StrEnum as single source of truth — a typo is an `AttributeError`, not a green test. ✓
- Exhaustion: fall back to the per-verb default. ✓
- Characteristics: one `CHARACTERISTIC` name, list in `STAT_NAMES` order — which is what lets a later change delete `preset_characteristics`. ✓
- Migration: two phases behind a temporary shim. ✓

**Known cost:** the `DiceRoller | Rolls` union and `_as_rolls` are deliberate temporary ugliness. They exist to buy a behaviour-preservation proof in phase A and are deleted in phase B. If phase B is abandoned, this debt stays — so do not abandon phase B.

**Placeholder scan:** phase A has no TBDs. Phase B is deliberately a sketch and must not be executed from this plan alone.
