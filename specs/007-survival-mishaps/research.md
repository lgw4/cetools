# Research: Survival Mishaps Instead of Character Death

## Context

This feature replaces the current "character died" `GenerationFailure` path (triggered by
a failed term survival roll) with resolution via the Cepheus Engine SRD's optional
Survival Mishaps table. The spec (`spec.md`) already resolved its two clarification
questions (±10% statistical tolerance for SC-004; 1D6×Cr10,000 injury-crisis debt for
FR-009). This document resolves the remaining SRD-fidelity questions needed to
implement precisely, per Constitution Principle I (SRD-Fidelity): where the SRD is
ambiguous, the most common/simplest interpretation is chosen and recorded here.

## SRD source text (verbatim, fetched from the constitution's authoritative URL)

**Survival Mishaps Table (1D6)**:

1. "Injured in action. (This is the same as a result of 2 on the Injury table.)
   Alternatively, roll twice on the Injury table and take the lower result."
2. "Honorably discharged from the service."
3. "Honorably discharged from the service after a long legal battle. Legal issues
   create a debt of Cr10,000."
4. "Dishonorably discharged from the service. Lose all benefits."
5. "Dishonorably discharged from the service after serving an extra 4 years in prison
   for a crime. Lose all benefits."
6. "Medically discharged from the service. Roll on the Injury table."

**Injury Table (1D6)**:

1. "Reduce one physical characteristic by 1D6, reduce both other physical
   characteristics by 2 (or one of them by 4)."
2. "Reduce one physical characteristic by 1D6."
3. "Reduce Strength or Dexterity by 2."
4. "Reduce any one physical characteristic by 2."
5. "Reduce any physical characteristic by 1."
6. "Lightly injured. No permanent effect."

**Failed survival (base rule)**: "events have forced you from this career. Roll on the
Survival Mishaps table and go to step 10 (you do not receive a benefit roll for this
term.)"

**Injury Crisis**: "If any characteristic is reduced to 0, then the character suffers
an injury crisis. The character dies unless he can pay 1D6×10,000 Credits for medical
care, which will bring any characteristics back up to 1."

## Decisions

### D1: "Take the lower result" ⇔ FR-008's "more severe of the two"

- **Decision**: Resolve outcome 1 by rolling the Injury table twice (two independent
  1D6 rolls) and using whichever roll number is **lower** to index the table.
- **Rationale**: The Injury table is ordered from most severe (row 1) to no effect
  (row 6), so "the lower roll" and "the more severe result" are the same outcome.
  FR-008's wording and the SRD's literal "take the lower result" wording are
  equivalent; no interpretation gap exists here, just a wording note worth recording
  so the implementation (`min()` of two rolls) is legible against both texts.
- **Alternatives considered**: The SRD offers a simpler fixed alternative ("this is
  the same as a result of 2 on the Injury table") instead of rolling twice. Not
  used, because FR-008 explicitly requires the roll-twice-take-worse method.

### D2: Injury table row 1's "(or one of them by 4)" branch

- **Decision**: When row 1 fires, always reduce the two non-primary physical
  characteristics by 2 each. The alternative phrasing ("or one of them by 4") is not
  implemented.
- **Rationale**: The SRD leaves this as an open choice normally made by a referee or
  player. cetools generates characters with no referee/session context (see spec's
  Assumptions), so per Principle I, the simplest, deterministic, most common reading
  is used: apply the non-alternative branch uniformly. This avoids introducing an
  arbitrary extra random choice or an unjustified asymmetric reduction.
- **Alternatives considered**: Randomly choosing between "-2/-2" and "-4/0" for the
  two secondary stats. Rejected as unnecessary complexity with no clear source of
  randomness specified by the SRD for that sub-choice.

### D3: Which physical characteristic is "the one" reduced

- **Decision**: Where the table says "one physical characteristic" / "any one
  physical characteristic" / "Strength or Dexterity," the specific stat is chosen by
  an additional die roll among the eligible candidates (e.g. `roll(3)` over
  Strength/Dexterity/Endurance, or `roll(2)` over Strength/Dexterity), using the
  same `DiceRoller` protocol already used everywhere else in the engine.
- **Rationale**: This is the only way to resolve "any one" deterministically and
  testably without a referee; it reuses the existing dice abstraction rather than
  inventing a new selection mechanism, and it keeps the outcome distribution fair
  (uniform per candidate) consistent with the SRD's dice-driven character
  generation throughout.

### D4: Discharge type for Mishap outcome 1 ("Injured in action")

- **Decision**: Outcome 1 does not set an honorable/dishonorable/medical discharge
  type; it is modeled as `discharge_type = "none"` (injury only, no formal
  discharge classification), distinct from outcome 6 which is explicitly "Medically
  discharged."
- **Rationale**: Of the six outcomes, only 2–6 use the word "discharged" in the SRD
  text; outcome 1 is worded purely as an injury event. FR-003 still forces
  immediate career departure for every outcome (career-ending is a property of any
  mishap, not of the discharge-type field specifically), and FR-005's benefit/pension
  forfeiture is scoped only to the two "dishonorably discharged" outcomes (4 and 5) —
  so outcome 1 does not forfeit benefits/pension, it only costs the current term's
  benefit roll like every other non-dishonorable outcome (FR-004).

### D5: Injury Crisis is a single event per mishap, not per stat

- **Decision**: If one or more physical characteristics are driven to 0 by a single
  mishap's injury resolution, exactly one injury-crisis debt charge (1D6×Cr10,000) is
  applied, and every characteristic at 0 is restored to 1.
- **Rationale**: The SRD describes the crisis as one event ("the character suffers
  an injury crisis... which will bring **any** characteristics back up to 1"),
  triggered by the condition "any characteristic is reduced to 0" — singular event,
  plural possible restorations, not one crisis per affected stat.
- **Alternatives considered**: Charging one 1D6×Cr10,000 debt per zeroed
  characteristic. Rejected as unsupported by the SRD's singular "an injury crisis"
  phrasing and unnecessarily punitive for what is already a rare edge case (only
  reachable from Injury table rows 1–2 with an unlucky 1D6, or row 1's -2 secondary
  reduction on an already-low stat).

### D6: Term/age bookkeeping for the mishap term

- **Decision**: When a mishap occurs during term N: `age` is incremented by 2
  (not 4) for that term (see D9 for outcome 5's additional +4 for imprisonment);
  `terms_served` is **not** incremented for that term (it
  continues to reflect only fully-completed prior terms); a `Term` record for term N
  is still appended to the character's term history with `survived=False`; the term
  loop then unconditionally ends (no reenlistment roll, no further terms).
- **Rationale**: `terms_served` already drives both `_muster_out`'s benefit-roll count
  and `_pension`'s eligibility threshold. By defining `terms_served` to mean
  "fully-completed terms," FR-004 (mishap term earns no benefit roll) and the
  pension edge case (mishap in term 1 → no benefits/pension, since none were earned
  yet) fall out of the existing arithmetic with no special-casing needed in
  `_muster_out`/`_pension` beyond the dishonorable-forfeiture override (FR-005,
  which those two functions cannot express on their own since they are unaware of
  discharge type — handled as a post-hoc override in the caller, see data-model.md).
- **Alternatives considered**: Incrementing `terms_served` for the partial term and
  subtracting 1 inside `_muster_out`/`_pension`. Rejected as it would require those
  two pure, already-tested functions to grow mishap-awareness they don't need, and
  would make `terms_served` mean two different things (full terms vs. attempted
  terms) depending on context.

### D7: Where new game-table code lives

- **Decision**: A new module, `src/cetools/engine/mishaps.py`, holds the Survival
  Mishaps table, the Injury table, and the resolution function. `MishapOutcome`
  (the per-character result, analogous to `Benefit`/`Term`) is added to
  `src/cetools/engine/models.py` alongside those.
- **Rationale**: Both tables are global SRD content, not part of any specific
  `Career` (unlike `cash_benefits`/`material_benefits`, which vary per career and
  live on the `Career` dataclass in `careers/base.py`). Following Principle V
  (Data-Driven Extensibility), the tables are frozen dataclasses in tuples indexed
  by roll, mirroring the existing `RankEntry`/`Career` pattern — not hardcoded
  if/elif branches like the pre-existing `_apply_aging` (which is not repeated
  here; see Constitution Check in plan.md).

### D8: Injury Crisis triggers at zero *or below* zero, not only exactly zero

- **Decision**: The injury-crisis path (FR-009) fires whenever an injury reduction
  would take a physical characteristic to zero or below (i.e., the reduction amount
  is clamped at zero rather than allowed to go negative), not only when the
  reduction lands on exactly zero.
- **Rationale**: Injury reduction amounts (e.g., 1D6) aren't capped to a
  characteristic's remaining points, so an unlucky roll against an already-low stat
  (including one already reduced by aging, `_apply_aging`) can overshoot past zero.
  The existing codebase already establishes this exact clamp-at-zero convention for
  aging (`characteristics[stat] = max(0, characteristics[stat] - amount)` in
  `_apply_aging`, `generator.py:120`); mirroring that precedent for injury is the
  simplest, most consistent reading and avoids a new class of unhandled negative
  characteristic values. This also means injury and aging interactions (e.g., a
  late-career character already weakened by aging who then suffers a mishap
  injury) are handled by the same general rule with no special-casing needed.
- **Alternatives considered**: Triggering the crisis only on an exact-zero landing
  and leaving negative results otherwise unhandled. Rejected: it would reintroduce
  an unhandled-failure edge case (negative characteristics with undefined meaning),
  contradicting the feature's core goal of eliminating death/failure dead ends.

### D9: Outcome 5's imprisonment adds 4 years to age, on top of the mishap term's 2

- **Decision**: For outcome 5 ("dishonorably discharged... after serving an extra 4
  years in prison"), `age` increases by 2 (D6's mishap-term adjustment) **plus** 4
  (the prison term) = 6 years total. All other five outcomes still increase `age`
  by exactly 2, per D6.
- **Rationale**: Confirmed with the feature author (see `checklists/readiness.md`
  CHK001): the SRD's own wording singles out the prison time as "extra" — time
  spent beyond, and in addition to, the interrupted term itself. "Extra" is the
  operative word; it marks additional elapsed time, not narrative color. D6's
  uniform +2 still applies to every outcome (including 5) for the interrupted term
  itself; D9 layers outcome 5's additional +4 on top of that base, keyed off
  `MishapOutcome.imprisoned` (true only for outcome 5) rather than checking the
  discharge type or roll number directly.
- **Alternatives considered**: Treating the prison time as narrative only (no age
  effect), leaving FR-007's adjustment uniform at +2 for all six outcomes. This was
  the initial reading; rejected after author confirmation that "extra" specifically
  denotes additive elapsed time the SRD deliberately distinguishes from the base
  term's own 2 years.

## Existing engine facts relied upon (from codebase research)

- Survival check + early `GenerationFailure` return: `generator.py:220-233`.
- Term loop, reenlistment, age/terms_served bookkeeping: `generator.py:208-303`.
- `_muster_out` (benefit rolls, keyed on `terms_served`): `generator.py:123-153`.
- `_pension` (keyed on `terms_served >= 5`): `generator.py:162-167`.
- `_apply_aging` as the closest existing "reduce characteristics" precedent:
  `generator.py:95-121`.
- `DiceRoller` protocol (`roll(sides, count=1) -> int`, sum of dice):
  `src/cetools/engine/dice.py`.
- `Character`, `Benefit`, `Term`, `GenerationFailure` dataclasses: `models.py:51-94`.
- CLI dispatch on `Character | GenerationFailure`: `cli/character.py:49-53`.
- `format_character` (4-line text output, no debt/mishap awareness today):
  `formatter.py`.
- Test doubles for deterministic dice: `ConstantRoller`, `SmartRoller`,
  `SequenceRoller` in `tests/conftest.py`.

## Constitution follow-up (not part of this feature's code changes)

Constitution Principle III ("CLI Interface") currently lists "character death" as an
example of an exit-code-1 user-facing failure. Once this feature ships, a survival
roll failure can no longer produce that outcome. This wording is now stale and should
be corrected via a separate constitution amendment PR (PATCH-level: wording fix, not a
principle change) — tracked as a follow-up, not a task of this feature.
