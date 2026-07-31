# Specification Quality Checklist: Acceptable Values at Interactive Ship Prompts

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-29
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

- Four clarifications were resolved with the requester before drafting, so the spec carries no
  `[NEEDS CLARIFICATION]` markers: values are named inline in the prompt (not a numbered menu);
  armour options become a follow-up question accepting zero or more; values are displayed in
  readable spelling and accepted in either spelling; and hull-narrowed sets are named too.
- Two names of user-facing CLI surface appear in the spec (`--interactive`, `--toml`, `--out`,
  `--hull`, `--small-craft`) and one file name (README). These are the product's own vocabulary
  rather than implementation detail: the feature *is* a change to what the command prints, so the
  requirements cannot be stated without naming the command's flags. No module, function, or type
  names appear.
- FR-002 (the displayed set equals the accepted set) is the spec's central invariant and the one
  most worth a dedicated test per prompt. SC-002 states it as a measurable outcome.
- The spec deliberately does **not** shorten a prompt's list by anticipating rules refusals that
  only assembly can decide (e.g. fuel scoops on a distributed hull). See Assumptions; this
  preserves the existing single-authority-on-rules boundary.
