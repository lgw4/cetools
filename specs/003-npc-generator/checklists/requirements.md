# Specification Quality Checklist: NPC Generator

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-20
**Last validated**: 2026-08-20 (after the name-tables amendment)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

### First validation, 2026-08-20

Two testability traps were identified while drafting and are closed in the delivered spec,
recorded here so review does not have to rediscover them:

1. **"No code edit" is untestable unless the constants are named (FR-038, SC-013).** Asserting
   that rules constants live in data without naming any gives no test something to fail.
   FR-038 enumerates the constants it binds, and SC-013 names the five places a change must be
   demonstrated through.
2. **The always-living criteria need a bounded sample (SC-003, SC-004, SC-006, SC-007).**
   "Many seeds" fixes no threshold. The sample is stated as one thousand or more with no seed
   excluded, and SC-006 and SC-007 carry numeric thresholds rather than adjectives.

Two items were considered and deliberately left as they stand:

- **FR-039 mentions moving data between two file kinds**, which reads as structural detail.
  It is retained because the move is user-visible: it changes which file a referee overrides to
  change the modifier bands, and SC-014 exists to prove the move changes no result.
- **SC-020 is qualitative** where the rest are countable. It is retained as the one criterion
  that states what the feature is for, and it is verifiable by reading a rendered sheet against
  what running an NPC in a scene requires. (Numbered SC-018 before the amendment.)

### Second validation, 2026-08-20, after the name-tables amendment

The amendment overturns an exclusion this spec previously stated, so the whole document was
re-read for places the old reading survived rather than only the sections edited. Four were
found and corrected: the User Story 1 acceptance scenario listing what a complete character
carries, the "no name is supplied" edge case, the Character key entity, and FR-029. The Input
section still quotes the original decisions brief verbatim, including its exclusion of name
generation; that is deliberate, since the Input is the record of what was asked for and the
Clarifications section directly beneath it is where the record is corrected.

Three amendment-specific traps were identified and closed:

1. **The licensing checks silently changed meaning (FR-042, FR-042a, SC-015, SC-015a).** Until
   this amendment every shipped data file was Open Game Content, so "every data file" and "every
   OGC file" named the same set and the existing checks could not tell which they meant. The name
   tables split the sets. Left alone, the checks would either fail on the name tables or, once
   relaxed to pass them, stop proving the designation for the files that need it. FR-042a states
   the obligation and SC-015a makes it fail-able by requiring that adding a file under either
   designation without extending the corresponding check breaks the suite.
2. **Regional weighting had to be pinned to the tables in force, not to seven (FR-043f).** The
   request names seven regions, but an override may add or replace one. Weighting written as a
   fixed seventh share would be wrong the moment a referee added a region, and the failure would
   be silent. SC-019 tests the weighting with shipped tables of deliberately differing sizes, so
   that a weighting mistakenly taken over names rather than over regions fails rather than
   passing by coincidence.
3. **"Supplying a name must not change the character" needed stating (FR-047b, FR-056a).** The
   natural implementation, rolling a name at the start of the walk, would make a caller-supplied
   name shift every subsequent draw, so the same seed would produce a different person depending
   on whether it was named. Nothing in the request rules that out and nothing else in the spec
   would have caught it.

One judgment call is recorded rather than tested:

- **FR-043b's "gender neutral" is verifiable by review, not by automation.** No check can read a
  name and decide whether it is gender-marked in its source language. What is made testable
  instead is the structural half of the requirement: no name table carries a gender field
  (SC-015b) and the generator models no gender anywhere. The selection criterion itself is stated
  in the requirement so that review has something definite to hold entries against.
