# Specification Quality Checklist: NPC Generator

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-20
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

Validation run 2026-08-20 against the spec as written. Two testability traps were identified
while drafting and are closed in the delivered spec, recorded here so review does not have to
rediscover them:

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
- **SC-018 is qualitative** where the rest are countable. It is retained as the one criterion
  that states what the feature is for, and it is verifiable by reading a rendered sheet against
  what running an NPC in a scene requires.
