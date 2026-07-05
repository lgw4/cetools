# Data Model: Survival Mishaps Instead of Character Death

All new types follow the existing codebase conventions (see `research.md` D7): static
SRD reference tables are frozen dataclasses in fixed-length tuples indexed by die roll
(the `Career`/`RankEntry` pattern in `careers/base.py`); per-character results are
plain (mutable) dataclasses alongside `Benefit`/`Term` in `models.py`.

## New static table types — `src/cetools/engine/mishaps.py`

### `InjuryEntry` (frozen)

One row of the SRD Injury table.

| Field | Type | Meaning |
|---|---|---|
| `candidate_stats` | `tuple[str, ...]` | Physical characteristics eligible to be the "primary" reduction target; the primary stat is chosen by an additional roll whenever there's more than one candidate. Empty tuple = no effect (row 6, no roll). This SRD table's 6 rows only ever populate this with 0, 2, or 3 candidates — 3 for "any physical characteristic" (rows 1, 2, 4, 5), 2 for "Strength or Dexterity" (row 3). |
| `primary_dice` | `int` | Number of D6 to roll and sum for the primary reduction amount. `0` means use `primary_fixed` instead. |
| `primary_fixed` | `int` | Fixed reduction amount when `primary_dice == 0`. Ignored otherwise. |
| `secondary_amount` | `int` | Amount applied to each of the *other* two physical characteristics (not chosen as primary). `0` = no secondary effect. |

`INJURY_TABLE: tuple[InjuryEntry, ...]` — exactly 6 entries, indexed as
`INJURY_TABLE[roll - 1]` for a 1D6 roll, validated (`__post_init__`-level check on
the module, mirroring `Career`'s 6-entry validation) to have length 6.

Row-by-row values (see `research.md` for the SRD text each row encodes):

| Roll | candidate_stats | primary_dice | primary_fixed | secondary_amount |
|---|---|---|---|---|
| 1 | all 3 physical stats | 1 | 0 | 2 |
| 2 | all 3 physical stats | 1 | 0 | 0 |
| 3 | (Strength, Dexterity) | 0 | 2 | 0 |
| 4 | all 3 physical stats | 0 | 2 | 0 |
| 5 | all 3 physical stats | 0 | 1 | 0 |
| 6 | () | 0 | 0 | 0 |

### `MishapEntry` (frozen)

One row of the SRD Survival Mishaps table.

| Field | Type | Meaning |
|---|---|---|
| `discharge_type` | `Literal["honorable", "dishonorable", "medical", "none"]` | Discharge classification for this outcome (`"none"` for outcome 1 — injury only, see research.md D4). |
| `imprisoned` | `bool` | Whether this outcome includes 4 years' imprisonment (outcome 5 only). |
| `debt` | `int` | Fixed Cr debt this outcome imposes directly (outcome 3's Cr10,000 legal battle; `0` for all others — injury-crisis debt is computed separately, not part of this static table). |
| `injury_rolls` | `int` | How many times to roll on `INJURY_TABLE` for this outcome: `0` (none), `1` (outcome 6), or `2`, taking the more severe/lower roll (outcome 1). |

`SURVIVAL_MISHAPS_TABLE: tuple[MishapEntry, ...]` — exactly 6 entries, indexed as
`SURVIVAL_MISHAPS_TABLE[roll - 1]` for a 1D6 roll.

| Roll | discharge_type | imprisoned | debt | injury_rolls |
|---|---|---|---|---|
| 1 | none | False | 0 | 2 |
| 2 | honorable | False | 0 | 0 |
| 3 | honorable | False | 10000 | 0 |
| 4 | dishonorable | False | 0 | 0 |
| 5 | dishonorable | True | 0 | 0 |
| 6 | medical | False | 0 | 1 |

## New per-character result type — `src/cetools/engine/models.py`

### `MishapOutcome`

Attached to a `Character` when (and only when) a survival roll failed during
generation. Captures everything FR-010 requires a caller to be able to determine
after the fact.

```python
@dataclass
class MishapOutcome:
    roll: int  # 1-6, which Survival Mishaps table row fired
    discharge_type: Literal["honorable", "dishonorable", "medical", "none"]
    imprisoned: bool
    injury_reductions: dict[str, int]  # stat name -> total amount reduced; empty if no injury
    injury_crisis: bool  # True if an injury-crisis debt was charged
```

No `kind`-discriminated `__post_init__` invariant is added (unlike `Benefit`):
`MishapOutcome` is only ever constructed internally by
`mishaps.resolve_survival_mishap`, never assembled piecemeal by external callers, so
there is no cross-field invariant to defend against invalid external construction.

`debt` amounts (both the fixed Cr10,000 legal-battle debt and any 1D6×Cr10,000
injury-crisis debt) are *not* duplicated on `MishapOutcome` — they are accumulated
directly onto `Character.debt` (see below), since debt is a character-level financial
fact, not mishap-table metadata. `MishapOutcome.injury_crisis` records *that* a
crisis debt was charged (for FR-010 legibility); the amount is visible via
`Character.debt`.

## Changes to existing `Character` — `src/cetools/engine/models.py`

Two new fields, both defaulted so existing call sites/tests that construct
`Character(...)` without them keep working:

```python
@dataclass
class Character:
    ...  # unchanged existing fields
    drafted: bool = False
    mishap: MishapOutcome | None = None  # NEW
    debt: int = 0  # NEW
```

- `mishap is None` ⇔ the character completed generation without a survival-roll
  failure (existing behavior, unchanged).
- `mishap is not None` ⇔ exactly one survival roll failed and ended the career early
  (per spec: at most one mishap can ever occur per generated character).
- `debt` is the total Cr owed (0 if none) — legal-battle debt (Cr10,000) OR
  injury-crisis debt (Cr10,000–60,000), never both simultaneously since only one
  mishap can occur and only one of those two debt sources applies per mishap
  outcome.

No changes to `Benefit`, `Term`, or `GenerationFailure`. `GenerationFailure`
continues to represent only enlistment/qualification failures and unimplemented
drafted careers (FR-012, out of scope) — it is no longer reachable from a survival
roll.

## Behavioral contract of the term loop (for implementation reference)

On a failed survival check for term N (see `research.md` D6, D9):

1. Append `Term(number=N, survived=False, commissioned=False, promoted=False, rank_at_end=rank, skills_gained=[])` to `term_history`.
2. Call `mishaps.resolve_survival_mishap(roller, characteristics)` → `(MishapOutcome, debt_amount)` (see `contracts/mishaps-engine-api.md` — the function returns a tuple, not a bare `MishapOutcome`, since `MishapOutcome` itself carries no `debt` field); accumulate `debt_amount` onto a running `debt` total.
3. `age += 2` (instead of the usual `+= 4`); if `mishap.imprisoned` is `True` (outcome 5 only), `age += 4` additionally (6 years total for that outcome). `terms_served` is **not** incremented.
4. Unconditionally end the term loop (no reenlistment roll, no further terms, no aging-table check for this term).
5. After the loop: if `mishap.discharge_type == "dishonorable"`, skip `_muster_out`/`_pension` entirely (`benefits = []`, `pension = None`); otherwise compute them exactly as today, using the unmodified (mishap-term-excluded) `terms_served`.
6. Construct `Character(..., mishap=mishap, debt=debt, benefits=benefits, pension=pension, terms=term_history, ...)`.

When no mishap occurs, every field defaults exactly as it does today — this is a
strictly additive change to the generation function's outputs.
