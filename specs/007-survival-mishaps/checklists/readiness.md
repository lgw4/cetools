# Pre-Tasks Readiness Checklist: Survival Mishaps Instead of Character Death

**Purpose**: Broad requirements-quality sweep across spec.md (and, where relevant,
plan.md/research.md/data-model.md) before running `/speckit-tasks` — for the
feature author's own self-review, not for verifying the implementation.
**Created**: 2026-07-05
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [x] CHK001 Is the effect on character age of outcome 5's "extra 4 years in prison" specified, or does FR-007's "two years of service" rule leave imprisonment time's effect on age undefined? [Gap, Spec §FR-002, FR-007]
  → **Resolved (confirmed with feature author).** Outcome 5 adds 4 years to age *on top of* the mishap term's 2 years (6 total for that outcome alone) — "extra" is additive elapsed time, not narrative color. FR-007 states this explicitly; rationale recorded as `research.md` D9; `data-model.md`'s behavioral contract reorders steps so `mishap.imprisoned` is known before the age adjustment is applied; `quickstart.md` scenario 1 now asserts `age == 24` for outcome 5 vs. `age == 20` for the other five.
- [x] CHK002 Are the complete effects (discharge type, injury, debt, benefit/pension impact) enumerated for outcome 2 (plain honorable discharge) as explicitly as they are for the other five outcomes, or is "no injury, no debt" left to be inferred by omission? [Completeness, Spec §FR-002]
  → **Resolved.** FR-002 now reads "(2) honorably discharged with no injury and no debt" instead of leaving it implicit.
- [x] CHK003 Is the interaction between mishap-induced characteristic reduction and existing aging-related characteristic loss (for characters 34+) addressed, beyond the general statement that aging itself is out of scope? [Gap, Spec §Assumptions]
  → **No gap.** FR-009 (as tightened per CHK015) is worded generically ("if an injury reduces a characteristic to zero or below") and doesn't care why a stat was already low, so aging+injury interaction is covered by the same general rule with no special-casing required. Recorded as part of `research.md` D8's rationale.

## Requirement Clarity

- [x] CHK004 Is SC-004's sample size ("e.g., 10,000") a required minimum for validation, or merely illustrative — and if illustrative, is the actual required sample size specified anywhere? [Ambiguity, Spec §SC-004]
  → **No gap.** "e.g." is intentionally illustrative; the ±10% band is the enforceable criterion, and the minimum sample size needed to check it is a test-design decision appropriately left to implementation, not the spec.
- [x] CHK005 Does FR-004's "the mustering-out benefit roll" (singular) unambiguously match how the existing benefit-roll mechanic is quantified per term, including any careers/ranks that may grant more than one roll? [Clarity, Spec §FR-004]
  → **No gap.** Verified against `generator.py`'s `_muster_out`: `total_rolls = terms_served + bonus_rolls` — exactly one roll is earned per fully-completed term, and rank bonus rolls are a separate career-long pool not tied to any single term. FR-004's singular framing matches this mechanic exactly.
- [x] CHK006 Is "the more severe of the two [injury] results" in FR-008 objectively defined (e.g., by an explicit ordering or severity metric), or does it rely on an unstated comparison rule? [Clarity, Spec §FR-008]
  → **No gap.** Already resolved in `research.md` D1: the Injury table is ordered most-to-least severe, so "more severe" = "lower roll" (`min()` of the two rolls) — no new ambiguity.

## Requirement Consistency

- [x] CHK007 Do FR-004 (mishap forfeits the term's benefit roll) and FR-006 (legal-battle outcome leaves benefits "otherwise unaffected") cross-reference clearly enough that a reader can't conclude outcome 3 keeps the mishap term's benefit roll? [Consistency, Spec §FR-004, FR-006]
  → **Resolved.** FR-006 now explicitly says "...unaffected, beyond the mishap term's own forfeited benefit roll already required by FR-004."
- [x] CHK008 Are discharge-type classifications consistent between FR-002's outcome descriptions and FR-005's forfeiture rule (e.g., is it clear outcome 1 — injury only — is neither honorably nor dishonorably discharged, so FR-005 doesn't apply to it)? [Consistency, Spec §FR-002, FR-005]
  → **No gap.** FR-002's parallel phrasing (only outcomes 2–6 use "discharged") already makes outcome 1's non-discharge status clear by the document's own convention; confirmed consistent with `research.md` D4.

## Acceptance Criteria Quality

- [x] CHK009 Is SC-002 ("a user can determine what happened... without needing implementation-level or log-level detail") stated so it can be objectively verified, or does it depend on a subjective judgment of what counts as "implementation-level"? [Measurability, Spec §SC-002]
  → **No gap.** Operationalized concretely by User Story 2's Independent Test and the Key Entities section, which enumerate exactly which fields must be inspectable.
- [x] CHK010 Does SC-003's "match the expected outcome" resolve precisely enough against FR-004/FR-005/FR-006 to be checked without re-deriving the outcome-to-benefit/pension mapping from scratch? [Measurability, Spec §SC-003]
  → **No gap.** User Story 3's three acceptance scenarios already spell out the exact expected mapping per outcome type.

## Scenario Coverage

- [x] CHK011 Are requirements defined for a mishap occurring during a character's final eligible term, including any interaction with mandatory-retirement or term-limit logic? [Coverage, Gap]
  → **No gap.** Verified against `generator.py`: the survival/mishap check happens at the top of each loop iteration, independently of the `_MAX_TERMS`/mandatory-extra-term branch later in the same iteration. FR-003's generic "regardless of what a normal reenlistment roll would otherwise produce" already covers this scenario without needing a special case.
- [x] CHK012 Is it an explicit requirement (rather than an incidental consequence) that the two debt sources — legal-battle debt and injury-crisis debt — never apply simultaneously to the same character? [Coverage, Spec §FR-006, FR-009]
  → **No gap.** Follows necessarily from FR-002's enumeration of six mutually exclusive outcomes (only outcome 3 carries the fixed legal debt; only outcomes 1/6 can trigger injury and thus a crisis); an explicit restatement would be redundant.

## Edge Case Coverage

- [x] CHK013 Is the outcome specified when an injury roll's *secondary* reduction (to a non-primary physical characteristic) is what drives that characteristic to zero, not just the primary target? [Edge Case, Spec §FR-009]
  → **No gap.** FR-009's wording ("a characteristic") is already generic to any reduction source, primary or secondary.
- [x] CHK014 Is it specified whether a single mishap that drives multiple characteristics to zero simultaneously triggers one injury-crisis debt charge or one per affected characteristic? [Edge Case, Ambiguity, Spec §FR-009]
  → **Resolved** (already, pre-existing). `research.md` D5 establishes exactly one crisis event per mishap regardless of how many characteristics hit zero.
- [x] CHK015 Does FR-009's trigger condition ("reduced to zero") also cover reductions that would take a characteristic below zero, given injury amounts (e.g., 1D6) aren't capped to the characteristic's remaining points? [Edge Case, Gap, Spec §FR-009]
  → **Resolved.** FR-009 now reads "reduces a characteristic to zero or below zero." Rationale (mirrors the existing `max(0, ...)` clamp already used for aging in `_apply_aging`) recorded as `research.md` D8.

## Non-Functional Requirements

- [x] CHK016 Beyond the aggregate ±10% uniformity check in SC-004, are there requirements on independence of mishap-outcome distribution from career, prior rolls, or character attributes? [Gap, Spec §SC-004]
  → **No gap — intentionally.** Mishap resolution uses a fresh, independent 1D6 roll via the same `DiceRoller` protocol as every other check in the engine, with no correlation coded anywhere. Adding an explicit independence requirement would be unjustified complexity per the constitution's simplicity default; SC-004's aggregate band is sufficient.

## Dependencies & Assumptions

- [x] CHK017 Is the assumption that dishonorable discharge forfeits an "already-qualified" pension validated against how pension eligibility is otherwise defined, or is it asserted solely as an interpretive choice? [Assumption, Spec §Assumptions]
  → **No gap.** Verified against `generator.py`'s `_pension` (`terms_served >= 5` eligibility) — the assumption is consistent with, and `data-model.md`'s behavioral contract correctly implements, this exact mechanic.
- [x] CHK018 Is the assumption that referee approval for the optional Mishaps rule is "always granted" recorded as a permanent product decision (not a toggle), clearly enough to prevent future ambiguity about whether a toggle should be added later? [Assumption, Spec §Assumptions]
  → **No gap.** Already stated explicitly: "this is the only behavior, not a toggle."

## Ambiguities & Conflicts

- [x] CHK019 Is it clear whether "two years of service" in FR-007 governs age only, or also affects other time-based bookkeeping (e.g., term history/count display) beyond age and terms served? [Ambiguity, Spec §FR-007]
  → **No gap.** Fully specified at the design level in `data-model.md`'s behavioral contract (D6): `age += 2`, `terms_served` not incremented, and a `Term` record is still appended with `survived=False`. Appropriately a design-artifact-level bookkeeping detail rather than a spec-level requirement gap.

## Notes

- All 19 items resolved. Four required actual spec edits (CHK001/FR-007, CHK002/FR-002,
  CHK007/FR-006, CHK015/FR-009); two required new documented SRD-ambiguity decisions
  in `research.md` (D8: injury crisis triggers at zero-or-below; D9: mishap-term age
  adjustment is uniform across all six outcomes). The remaining 13 were verified as
  already adequately covered — either by existing spec wording, an existing
  `research.md`/`data-model.md` decision, or by reading the actual `generator.py`
  mechanics the requirement describes.
- **CHK001/D9 update**: the feature author confirmed outcome 5's "extra 4 years in
  prison" is additive — age += 6 total for that outcome (2 for the interrupted term
  + 4 for imprisonment), not a uniform +2 across all outcomes. `research.md` D9,
  `spec.md` FR-007, `data-model.md`'s behavioral contract, and `quickstart.md`
  scenario 1 were all updated to match.
- The existing [requirements.md](requirements.md) checklist already covers generic
  spec-quality gates (structure, testability, no-implementation-leakage) and is
  fully satisfied; this checklist does not repeat those items.
