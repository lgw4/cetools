# Feature Specification: Survival Mishaps Instead of Character Death

**Feature Branch**: `007-survival-mishaps`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "As cetools character is for generating characters on demand, character death is a undesirable outcome. We should use the optional mishaps table detailed at https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#survival instead."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Always receive a usable character (Priority: P1)

A user generates a character for a career. During one of the character's terms of
service, the character fails their survival roll. Today this ends generation in an
unrecoverable "character died" failure with no character produced. Instead, the user
should receive a complete, usable character record whose career was cut short by a
survival mishap, with all the consequences of that mishap (injury, discharge type,
debt, lost benefits) applied.

**Why this priority**: This is the entire point of the feature. On-demand character
generation for a tool like cetools should never dead-end in "no character" - every
generation attempt (that passes career qualification) must produce a character.

**Independent Test**: Force a failed survival roll (e.g., via a scripted die roller in
tests) and confirm the system returns a complete character rather than a failure
result.

**Acceptance Scenarios**:

1. **Given** a character in career service, **When** the character fails a term's
   survival roll, **Then** the system resolves the outcome using the Survival Mishaps
   table instead of ending generation in failure.
2. **Given** a character whose survival roll fails, **When** generation completes,
   **Then** the returned character reflects a shortened final term (two years of
   service instead of four) and no further terms are attempted.

---

### User Story 2 - Understand why a career ended early (Priority: P2)

A user inspecting a generated character whose career ended via a mishap wants to know
what happened: was the character hurt, discharged honorably, discharged
dishonorably, imprisoned, or left in debt? Without this information the character's
short career and reduced stats/benefits look arbitrary or like a bug.

**Why this priority**: The mishaps table exists specifically to give a fired-but-alive
character a story. Hiding that story removes most of the value of choosing mishaps
over silent, unexplained early retirement.

**Independent Test**: Generate several characters whose careers end via each of the
six mishap outcomes and confirm each character's record identifies which outcome
occurred (discharge type, any injury applied, any debt incurred).

**Acceptance Scenarios**:

1. **Given** a character discharged dishonorably by a mishap, **When** the character
   record is inspected, **Then** it clearly indicates a dishonorable discharge
   occurred.
2. **Given** a character injured by a mishap, **When** the character record is
   inspected, **Then** it reflects the specific characteristic reduction(s) applied
   and indicates that an injury occurred.
3. **Given** a character who incurred debt from a mishap, **When** the character
   record is inspected, **Then** the debt amount is visible.

---

### User Story 3 - Accurate financial and physical consequences (Priority: P3)

A user relies on generated characters having internally consistent mustering-out
benefits, pensions, and characteristics. When a mishap occurs, those downstream
numbers must reflect the specific mishap's severity rather than behaving as if the
character had a normal, voluntary end of career.

**Why this priority**: Correct consequences matter for the character to be usable at
the table, but this refines the outcome rather than defining the feature's core
value (P1) or its legibility (P2).

**Independent Test**: For each of the six mishap outcomes, generate a character that
had already completed enough terms to qualify for a pension, then confirm pension and
mustering-out benefits match the expected outcome (preserved, reduced, or forfeited).

**Acceptance Scenarios**:

1. **Given** a character who already qualifies for a retirement pension, **When** a
   later mishap results in dishonorable discharge, **Then** both the mustering-out
   benefits and the pension are forfeited.
2. **Given** a character who already qualifies for a retirement pension, **When** a
   later mishap results in honorable discharge (with or without debt), **Then** the
   pension is preserved.
3. **Given** any mishap outcome, **When** generation completes, **Then** the
   mustering-out benefit roll for the term in which the mishap occurred is skipped,
   while benefit rolls earned from prior, fully-completed terms are unaffected.

---

### Edge Cases

- A mishap occurs during a character's very first term, before any benefits have
  accrued: the character still leaves service immediately, with age reflecting two
  years of service and no mustering-out benefits or pension (since none were earned
  yet regardless of the mishap).
- An injury roll (from mishap results 1 or 6) would reduce a characteristic to zero:
  the system resolves this without the character dying, incurring a 1D6×Cr10,000
  treatment cost as debt and restoring the characteristic to 1.
- A character fails career-qualification (fails to enlist at all): unaffected by
  this feature - that failure path is unrelated to survival rolls and continues to
  behave as it does today.
- A drafted character (assigned to a career via the draft table) fails a survival
  roll: resolved via the same mishaps table as any other character.
- Because a mishap always ends the character's career immediately, at most one
  mishap can ever occur for a single generated character.

## Clarifications

### Session 2026-07-05

- Q: SC-004 says the six mishap outcomes should fall within "statistical tolerance" of a uniform 1-in-6 chance across a large sample (e.g. 10,000 characters), but doesn't define that tolerance. What should the acceptance test check? → A: ±10% band per outcome — each of the six outcome counts must fall within ±10% of the expected 1/6 share (e.g., ~1667 ± 167 per 10,000 samples).
- Q: FR-009 says a characteristic-to-zero crisis costs "the cost of treatment" as debt, but doesn't specify the amount. What amount should the system record? → A: SRD exact rule — roll 1D6 and multiply by Cr10,000 (range Cr10,000–60,000), matching the Cepheus SRD's Injury Crisis rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a character fails a term's survival roll, the system MUST resolve
  the outcome via the Survival Mishaps table (as defined in the Cepheus Engine SRD)
  instead of ending generation in an unrecoverable failure.
- **FR-002**: The system MUST support all six Survival Mishaps table outcomes:
  (1) injured in action, (2) honorably discharged with no injury and no debt, (3) honorably discharged with a
  Cr10,000 debt after a legal battle, (4) dishonorably discharged with all benefits
  lost, (5) dishonorably discharged with all benefits lost after 4 years'
  imprisonment, and (6) medically discharged with an injury applied.
- **FR-003**: Every mishap outcome MUST force the character to leave the career
  immediately - no further terms of service are attempted after a mishap, regardless
  of what a normal reenlistment roll would otherwise produce.
- **FR-004**: A mishap MUST cost the character the mustering-out benefit roll for the
  term in which it occurred, while leaving benefit-roll eligibility already earned
  from prior, fully-completed terms intact (except where FR-005 applies).
- **FR-005**: For the two "dishonorably discharged" outcomes, the system MUST
  forfeit both the character's mustering-out benefits and any retirement pension the
  character would otherwise have qualified for.
- **FR-006**: For the "honorably discharged after legal battle" outcome, the system
  MUST record a Cr10,000 debt against the character while leaving mustering-out
  benefits and pension eligibility otherwise unaffected, beyond the mishap term's
  own forfeited benefit roll already required by FR-004.
- **FR-007**: The character's age at the end of generation MUST reflect two years of
  service (half a term) for the term in which the mishap occurred, rather than the
  usual four years for a completed term. For outcome 5 specifically, the
  character's age MUST additionally reflect the four extra years spent in prison,
  on top of the term's two years — six years of age increase in total for that
  outcome alone; every other outcome increases age by exactly two years.
- **FR-008**: For outcomes that call for an injury (outcomes 1 and 6), the system
  MUST apply the SRD's Injury table to reduce the character's physical
  characteristics (Strength, Dexterity, Endurance) accordingly, and MUST resolve
  outcome 1 by rolling the Injury table twice and applying the more severe of the two
  results, per the SRD.
- **FR-009**: If an injury reduces a characteristic to zero or below zero, the system MUST NOT
  allow this to end generation in failure. It MUST instead resolve the resulting
  medical crisis automatically, restoring the characteristic to 1 and recording the
  cost of treatment as debt against the character, per the SRD's Injury Crisis rule:
  a 1D6 roll multiplied by Cr10,000 (i.e., a random amount between Cr10,000 and
  Cr60,000).
- **FR-010**: The generated character's record MUST include enough information for a
  caller to determine, after the fact, whether a mishap occurred and what happened
  (which of the six outcomes, any injury applied, any debt incurred), so this can be
  surfaced to users.
- **FR-011**: This behavior MUST apply uniformly across every character generation
  entry point in the system (direct career generation, drafted characters, and any
  other path that performs survival rolls) - a survival roll MUST never again produce
  an unrecoverable character-death result.
- **FR-012**: Career-qualification (enlistment) failures are out of scope for this
  feature and MUST continue to behave exactly as they do today.

### Key Entities

- **Mishap Outcome**: The result of resolving a failed survival roll. Captures which
  of the six Survival Mishaps table results occurred, the resulting discharge type
  (honorable, dishonorable, medical, or none if not discharged via mishap), whether
  imprisonment occurred, any injury applied, and any debt incurred (from a legal
  battle or from a medical crisis).
- **Character** (existing entity, extended): in addition to its existing attributes,
  a character now carries its Mishap Outcome (if any), and a debt amount (if any)
  incurred through the mishap process.
- **Survival Mishaps Table / Injury Table**: static SRD reference data describing
  each possible outcome and its effects; used to resolve a failed survival roll.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of character generation attempts that pass career qualification
  complete with a full character record - a failed survival roll never again
  produces "no character" as a result.
- **SC-002**: For every character whose career ended via a mishap, a user can
  determine what happened (discharge type, injury, debt) directly from the
  character's record, without needing implementation-level or log-level detail.
- **SC-003**: Mustering-out benefits and pensions for mishap-affected characters
  match the expected outcome (preserved, reduced, or fully forfeited) in 100% of
  generated cases, consistent with which of the six outcomes occurred.
- **SC-004**: Across a large sample of generated characters that fail a survival
  roll (e.g., 10,000), each of the six mishap outcomes occurs within ±10% of its
  expected uniform 1-in-6 share (e.g., ~1,667 ± 167 occurrences per 10,000 samples).

## Assumptions

- Death is eliminated system-wide for survival-roll failures. Career-qualification
  (enlistment) failures are a separate, unrelated mechanic and are unaffected by this
  feature.
- The SRD gates this optional rule behind "the Referee's approval." Since cetools
  generates characters with no referee or session context, and the user has
  explicitly requested this as the standard behavior, approval is assumed to always
  be granted - this is the only behavior, not a toggle.
- Mishap outcome 1 ("Injured in action") is resolved by rolling the Injury table
  twice and taking the more severe of the two results, per the SRD's own guidance for
  that specific outcome.
- A medical crisis triggered by a characteristic reaching zero is always resolved
  successfully (treatment is always "affordable") rather than risking death, per
  explicit user direction that death is never a desired outcome of on-demand
  generation. The cost is tracked as debt rather than silently ignored.
- Dishonorable discharge ("lose all benefits") is read to include forfeiting an
  already-qualified retirement pension, not just the current term's benefit roll.
- Only one mishap can occur per generated character, since every mishap outcome ends
  the character's career immediately.
- This feature does not change unrelated systems: aging-related characteristic loss
  (for characters aged 34+) and career-qualification checks are out of scope.
