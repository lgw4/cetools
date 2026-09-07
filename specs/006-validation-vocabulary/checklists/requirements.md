# Specification Quality Checklist: Validation Vocabulary

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-06
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

### On "no implementation details" for an internal-quality feature

This feature's subject is the codebase itself: the thing being changed is how
the project states a rule about its own data files. A spec for it cannot avoid
naming code the way a spec for a user-facing feature would, so the standard was
applied as follows.

- The spec names no language, framework, library, or API.
- Requirements are written as obligations on behavior and on where a rule is
  stated, not as instructions to write particular functions. FR-002 through
  FR-008 say which checks must exist and what each must report, not what they
  are called or what their parameters are.
- The Input quotation preserves the original symbol names, since that is the
  description as given and the drift it records is the evidence for the feature.
  Nothing downstream of it depends on those names.
- Success criteria are stated as counts and as comparisons of observable output
  (SC-001 through SC-004) or as what a contributor can do without help
  (SC-005, SC-006). None names a symbol.

The concrete symbol names, signatures, and file paths settled during the design
interview belong in `plan.md`, not here.

### Constitution alignment

- Principle III (Test-First): FR-018 requires the vocabulary's tests to be
  written first and to fail before it exists.
- Principle VI (Simplicity): FR-020 records the four deepenings deliberately not
  attempted, each of which was considered and rejected as speculative for this
  pass.
- Tidy First (project guidance): FR-019 requires the one behavioral change to
  ship before, and separately from, the structural removals.
- Changelog discipline: FR-019 places exactly one changelog entry, for the only
  user-visible change.
