# SRD Fidelity & Pre-Plan Gap Checklist: Navy Character Generator

**Purpose**: Identify missing or underspecified requirements before writing plan.md — focused on SRD rules completeness, CLI interface clarity, data model precision, and constitution compliance.
**Created**: 2026-06-17
**Feature**: [spec.md](../spec.md)
**Depth**: Standard
**Audience**: Author (pre-plan)
**Focus**: SRD rules fidelity, constitution compliance

---

## SRD Rules Completeness

- [x] CHK001 - Are the Navy enlistment check target number and all characteristic DMs specified in the requirements? [Gap, Spec §FR-002] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK002 - Is the survival roll target number and any characteristic or rank DMs specified? [Gap, Spec §FR-003] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK003 - Are the commission roll target number, per-term eligibility conditions, and DMs specified? [Gap, Spec §FR-003] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK004 - Are the promotion roll target number, eligibility preconditions (e.g., must be commissioned), and DMs specified? [Gap, Spec §FR-003] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK005 - Are the re-enlistment roll target number and any applicable DMs specified? [Gap, Spec §FR-006] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK006 - Is the number of skill rolls acquired per term explicitly stated? [Gap, Spec §FR-003] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK007 - Are the Navy skill tables (e.g., Personal Development, Service Skills, Advanced Education, Officer Skills) enumerated, or is a reference to the SRD version sufficient—and if the latter, is the SRD version pinned? [Gap/Assumption, Spec §FR-011] — SRD URL pinned in FR-011; full tables required in plan.
- [x] CHK008 - Is the number of mustering-out benefit rolls per term (and any bonus rolls for rank) specified? [Gap, Spec §FR-007] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK009 - Are the mustering-out cash and material benefit tables enumerated in the requirements, or are they delegated entirely to FR-011? [Gap, Spec §FR-007] — Delegated to FR-011; valid material names also required in plan.
- [x] CHK010 - Is the characteristic modifier derivation rule (mapping raw characteristic value to its DM) specified? [Gap, Spec §FR-001] — Delegated to FR-011; plan must enumerate before implementation.
- [x] CHK011 - Are all Navy enlisted ratings and commissioned officer rank titles enumerated in the requirements? [Gap, Spec §FR-005] — Closed: delegated to FR-011; plan must enumerate all ratings and titles before implementation.
- [x] CHK012 - Is the maximum attainable characteristic value during generation specified, and is hexadecimal UPP representation defined for values 10–15? [Clarity, Spec §FR-001, §FR-008] — Resolved: FR-008 now states 2d6 range 2–12, max UPP digit is C; hex A–F defined for values 10–15.
- [x] CHK013 - Is the draft assignment procedure (how the SRD determines which service a failed enlistee is assigned to) specified, or is the retry-until-Navy rule a sufficient substitute? [Clarity, Spec §FR-002] — Closed: retry-until-Navy rule is sufficient; draft table internals are an implementation detail covered by FR-011.
- [x] CHK014 - Is the consequence of a survival failure fully specified—career end only, or is character death a possible outcome per the SRD? [Clarity, Spec §FR-006] — Resolved: FR-006 now states survival failure is career-ending only; no death or characteristic modification in MVP.

---

## CLI Interface Requirements

- [x] CHK015 - Is the CLI command name (the Typer entry point invoked by the user) specified? [Gap] — Resolved: FR-008 now specifies `cetools navy`.
- [x] CHK016 - Are all CLI flag names, types, and defaults specified (e.g., `--count INTEGER`, `--json / --no-json`)? [Gap, Spec §FR-009, §FR-010] — Resolved: FR-009 specifies `--count INTEGER` (default 1); FR-010 specifies `--json` boolean (default false).
- [x] CHK017 - Is the human-readable output format for multiple characters defined—specifically how characters are visually separated? [Gap, Spec §FR-008, §FR-009] — Resolved: FR-008 now requires `---` separator between character blocks.
- [x] CHK018 - Is the exact error message format for an invalid `--count` value specified, or only that a validation error must appear? [Clarity, Spec §FR-009, Edge Cases] — Resolved: FR-009 now specifies exact message `Error: count must be a positive integer`.
- [x] CHK019 - Are exit-code requirements specified for successful invocations as well as error cases? [Gap, Spec §FR-009] — Resolved: FR-009 specifies exit 0 on success, exit 1 for validation errors, non-zero for unexpected errors.

---

## Data Model & Schema Clarity

- [x] CHK020 - Is the type of the `value` field in each `benefits` array object specified per benefit type (e.g., integer for cash, string for material)? [Clarity, Spec §FR-010, Clarifications] — Resolved: FR-010 now specifies integer credits for cash, string name for material.
- [x] CHK021 - Are the valid string values for material benefits enumerated (e.g., "Low Passage", "Ship Shares", "Weapon")? [Gap, Spec §FR-010] — Closed: delegated to FR-011; plan must enumerate all material benefit names before implementation.
- [x] CHK022 - Is the `rank` JSON field value defined for enlisted characters who never received a commission (no officer rank)? [Gap, Spec §FR-010] — Resolved: FR-010 now specifies empty string `""` for characters with no rank title.
- [x] CHK023 - Is the `career_history` entity (Career Term in Key Entities) explicitly excluded from the JSON output schema, or is its absence an unintentional gap? [Clarity, Spec §FR-010, Key Entities] — Resolved: FR-010 now explicitly states `career_history` is intentionally excluded.
- [x] CHK024 - Is the `skills` JSON object schema defined for zero-skill characters (empty object `{}` vs. absent field)? [Edge Case, Spec §FR-010] — Resolved: FR-010 now specifies `skills` MUST be `{}` for a character with no skills.

---

## Scenario & Edge Case Coverage

- [x] CHK025 - Is the "characteristic value of 0" edge case in the spec valid? Since 2d6 has a minimum of 2, a raw characteristic cannot be 0—does the spec mean a characteristic reduced to 0 by some modifier, or should this edge case be removed as impossible? [Ambiguity, Spec §Edge Cases] — Resolved: edge case removed from spec; 2d6 minimum of 2 documented.
- [x] CHK026 - Is the behavior defined when the same skill is gained more than once within a single term (not across terms)? [Clarity, Spec §FR-004] — Closed: FR-004's "combining duplicate skills into a higher skill level" applies universally regardless of whether duplicates arise within a single term or across terms.
- [x] CHK027 - Are requirements defined for a promotion roll that succeeds when the character is already at the maximum Navy rank? [Gap, Spec §FR-005] — Resolved: FR-005 now specifies promotion at max rank has no effect.
- [x] CHK028 - Is the re-enlistment behavior before term 4 specified? FR-006 states the generator attempts re-enlistment "after term 4," which is ambiguous about whether re-enlistment can fail (and end the career) in terms 1–4. [Ambiguity, Spec §FR-006, Clarifications] — Resolved: FR-006 now states terms 1–4 are served automatically; re-enlistment rolls only begin at term 5.
- [x] CHK029 - Is there a defined termination condition or maximum retry limit for the "retry from scratch until Navy is obtained" loop in FR-002, to prevent an unbounded generation loop? [Gap, Spec §FR-002] — Resolved: FR-002 now mandates a hard limit of 1,000 retries with an error on breach.
- [x] CHK030 - Are requirements defined for how a Navy-drafted character (drafted directly into Navy, not a non-Navy service) progresses through the career—same path as an enlisting character? [Clarity, Spec §FR-002, Edge Cases] — Closed: Edge Cases already states "A character drafted directly to Navy follows the same career path as an enlistee"; FR-002 guarantees all outcomes produce a Navy character.

---

## Non-Functional Requirements

- [x] CHK031 - Does SC-001 ("under five seconds") apply to a single character, to a 100-character batch, or to both—and is this measurable from the implementation? [Ambiguity, Spec §SC-001, §SC-003] — Resolved: SC-001 now explicitly scopes to a single character; batch invocations (SC-003) have no time constraint.
- [x] CHK032 - Is the "cryptographically unbiased random number generator" assumption sufficient as a requirement, or does the spec need to name the Python module or interface? [Assumption, Spec §Assumptions] — Closed: "cryptographically unbiased" is sufficient at spec level; the choice of Python RNG module is an implementation detail for plan.md.
- [x] CHK033 - Is SC-002 ("zero discrepancies against SRD") measurable given that no automated oracle exists for SRD correctness—what is the acceptance procedure? [Measurability, Spec §SC-002] — Resolved: SC-002 now specifies the acceptance procedure: generate 10 sample characters and verify all fields manually against the SRD tables.

---

## Constitution Compliance

- [x] CHK034 - Does the spec explicitly require that character generation logic resides in a library module under `src/cetools/` independent of the CLI layer, as mandated by Constitution Principle I? [Gap, Constitution §I] — Resolved: FR-012 added.
- [x] CHK035 - Does the spec explicitly require that CLI entry points (Typer commands) contain no business logic, as mandated by Constitution Principle I? [Gap, Constitution §I] — Resolved: FR-012 added.
- [x] CHK036 - Are SRD table data structures (enlistment targets, skill tables, benefit tables) required to be separately importable and testable independent of the CLI, enabling TDD per Constitution Principle II? [Gap, Constitution §I, §II] — Resolved: FR-012 added.
- [x] CHK037 - Does the spec or an accompanying governance document require the Red-Green-Refactor cycle before implementation begins, per Constitution Principle II? [Gap, Constitution §II] — Closed: TDD is mandated by Constitution Principle II, which supersedes all other project conventions; duplicating governance in the feature spec is unnecessary.
