# Feature Specification: Combined Benefit Display and Explorers' Society Uniqueness

**Feature Branch**: `008-benefit-list-refinements`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "We need to combine repeated benefits. For example, a
character whose raw mustering-out rolls were Weapon, +1 Edu, High Passage, Weapon, +1
Soc, Weapon should display as: +1 Edu, High Passage, +1 Soc, Weapon x 3.
Additionally, a character can only receive the Explorers' Society benefit once. If a
character has already received the Explorers' Society benefit, and rolls it again,
the benefit should be rerolled until they receive a different benefit."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Readable material benefit list (Priority: P1)

A user reads a generated character's equipment line and sees the same material
benefit name repeated several times (e.g. "Weapon, Weapon, Weapon"). This is
harder to scan than a single grouped entry and doesn't match how a person would
naturally describe the same set of gear.

**Why this priority**: This is the entire point of the feature - it's a pure
display improvement with no gameplay effect, so it's the whole deliverable for this
half of the request.

**Independent Test**: Format a character whose material benefits list contains a
repeated name and confirm the equipment line shows that name once with a count,
alongside singly-occurring names shown as before.

**Acceptance Scenarios**:

1. **Given** a character with material benefits `[Weapon, +1 Edu, High Passage,
   Weapon, +1 Soc, Weapon]`, **When** the character is formatted, **Then** the
   equipment line reads `+1 Edu, High Passage, +1 Soc, Weapon x 3`.
2. **Given** a character whose material benefits contain no repeated names, **When**
   the character is formatted, **Then** the equipment line is unchanged from today's
   behavior (each name once, in original order).
3. **Given** a character with two different benefit names that are each repeated
   (e.g. `Weapon` twice and `High Passage` three times), **When** the character is
   formatted, **Then** both are rendered with an "x N" count, ordered among
   themselves by which name first appeared in the raw list.
4. **Given** a character with no material benefits, **When** the character is
   formatted, **Then** the equipment line is omitted entirely, as today.

---

### User Story 2 - Explorers' Society membership is granted at most once (Priority: P2)

A user generates a character whose mustering-out rolls happen to land on the
"Explorers' Society" material benefit more than once. Being admitted to the same
society twice makes no narrative sense, and today's engine has no rule preventing
it for careers whose material benefit table includes that entry (Navy, Marine,
Scout).

**Why this priority**: This is a correctness/plausibility fix for generated data,
independent of and secondary to the display change in User Story 1.

**Independent Test**: Force a sequence of material-benefit rolls that would, without
this rule, produce "Explorers' Society" more than once for the same character, and
confirm the character's benefit list contains it exactly once, with the repeat
rolls instead resolving to different material benefits.

**Acceptance Scenarios**:

1. **Given** a character whose first "Explorers' Society" roll occurs, **When** that
   roll is resolved, **Then** the benefit is granted normally (no reroll).
2. **Given** a character who already has "Explorers' Society" among their granted
   benefits, **When** a later material-benefit roll would also resolve to
   "Explorers' Society", **Then** the system rerolls that single benefit (using the
   same die mechanics, including any rank-based DM) until it resolves to a
   different material benefit, and grants that instead.
3. **Given** a career whose material benefits table does not include "Explorers'
   Society" at all (e.g. Aerospace System Defense), **When** any character from
   that career musters out, **Then** this rule has no observable effect.

---

### Edge Cases

- A reroll (per User Story 2) itself resolves to "Explorers' Society" again: the
  system keeps rerolling until a different result is produced, rather than
  stopping after one retry.
- The reroll never consumes an extra roll from the character's total mustering-out
  allotment - it replaces the roll that would have produced the duplicate, rather
  than being an additional roll on top of it.
- A character has zero material benefits (e.g., all mustering-out rolls were spent
  on the 3-roll cash cap): there is nothing to combine, and the equipment line is
  omitted, exactly as today.
- Cash benefits are entirely unaffected by both user stories - they are already
  summed into a single `Cr<amount>` total and are never listed individually.

## Clarifications

### Session 2026-07-05

- Q: How should combined material benefits be ordered? → A: Names occurring exactly
  once keep their original first-occurrence relative order; names occurring more
  than once are pulled out and appended after all the singles, ordered among
  themselves by first occurrence. (Confirmed against the worked example: `+1 Edu,
  High Passage, +1 Soc, Weapon x 3`.)
- Q: What exact text marks a repeated benefit's count? → A: `"<Name> x <count>"` -
  lowercase "x" with a space on each side (e.g. `Weapon x 3`).
- Q: Should the "only once" rule be a general mechanism (e.g. a new Career-level
  "unique benefits" set) or specific to Explorers' Society? → A: Hardcode the check
  to the exact string `"Explorers' Society"` only. No other career table currently
  has a one-time-only material benefit, so a general mechanism would be
  speculative; this can be revisited if a future benefit needs the same treatment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The formatted equipment line MUST group a character's material
  benefits by exact `material_name` before rendering.
- **FR-002**: Any `material_name` occurring exactly once in a character's benefits
  MUST be rendered as its bare name, and all such single-occurrence names MUST
  preserve their relative order from the original benefits list.
- **FR-003**: Any `material_name` occurring two or more times MUST be rendered
  exactly once, formatted as `"<Name> x <count>"`, where `<count>` is the total
  number of occurrences of that name (not the number of extra occurrences beyond
  the first).
- **FR-004**: All names rendered with a count (FR-003) MUST appear after all
  singly-occurring names (FR-002) in the equipment line, and MUST themselves be
  ordered by which name first occurred in the original benefits list.
- **FR-005**: Cash benefit totaling and rendering MUST be unaffected by FR-001
  through FR-004.
- **FR-006**: During mustering-out, if a material-benefit roll resolves to
  `"Explorers' Society"` and the character has already been granted a material
  benefit named `"Explorers' Society"` earlier in the same generation, the system
  MUST reroll that benefit - reapplying the same die mechanics (including the
  rank-based material DM) - and use the new result instead, repeating until a
  result other than `"Explorers' Society"` is produced.
- **FR-007**: The uniqueness rule in FR-006 MUST apply specifically and only to the
  exact string `"Explorers' Society"`; no other material benefit name is subject to
  a reroll-on-repeat rule.
- **FR-008**: The reroll described in FR-006 MUST NOT change the total number of
  mustering-out rolls a character receives - it replaces the single roll that would
  have produced the duplicate rather than adding an additional roll.

### Key Entities

No new entities and no changes to existing entity shapes. `Benefit` and `Career`
(including `Career.material_benefits`) are used exactly as they exist today; this
feature is implemented entirely in the mustering-out roll logic and the character
formatter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any character whose material benefits contain one or more
  repeated names, the formatted equipment line names each distinct benefit exactly
  once - no name ever appears twice in the rendered line.
- **SC-002**: For any name that occurs more than once, the rendered line states the
  correct total count for that name.
- **SC-003**: Across any number of generated characters, no character's benefits
  ever contain `"Explorers' Society"` more than once.
- **SC-004**: For characters with no repeated material benefit names, the formatted
  equipment line is byte-for-byte identical to today's output.

## Assumptions

- The display-combining rule (User Story 1) and the Explorers' Society uniqueness
  rule (User Story 2) are independent mechanisms: the formatter always collapses
  duplicate names for display regardless of how they were produced, while the
  generator's reroll rule is what prevents "Explorers' Society" specifically from
  ever existing twice in the underlying data. In practice this means "Explorers'
  Society" will never appear in the formatter's "x N" group - only ever as a
  single - but the formatter does not need to know that; it would combine any
  repeated name it's given.
- Only "Explorers' Society" is treated as unique, per explicit user direction.
  Other repeatable material benefits (Weapon, passages, characteristic boosts) are
  intentionally allowed to occur multiple times for the same character and are
  only deduplicated for display purposes.
- The reroll mechanism relies on being able to call the existing `DiceRoller.roll()`
  an unbounded number of times in sequence, consistent with the existing
  unbounded-retry pattern already used elsewhere in the generator (e.g.
  `roll_until_qualified`).
- This feature does not introduce a general "unique material benefit" mechanism on
  the `Career` data model. If a future benefit needs the same one-time-only
  treatment, that would be handled as a separate feature.
- Careers whose material benefits table does not include "Explorers' Society" at
  all (currently: Aerospace System Defense) are unaffected by User Story 2.
