# Specification Quality Checklist: Universal Ship Description Format

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-24
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

---

## Post-Plan Requirements Review (added 2026-07-24)

Appended after Phase 0/1. Scope of review: `spec.md` primarily, with `plan.md`, `research.md`,
`data-model.md` and `contracts/` treated as requirement sources.

**Cross-check status (2026-07-24)**: All 38 items reviewed. **All 38 resolved** — 27 required a
`spec.md` edit, made the same day; the remaining 11 were already answered by an existing
requirement or by a design artifact that is the right home for the answer. See per-item notes.

### Requirement Completeness

- [x] CHK001 Is the behaviour of the drives sentence defined for a starship with a jump drive but no maneuver drive, which the builder permits? [Gap, Spec §FR-006] → **Fixed**: new FR-006a omits the maneuver clause and the G-acceleration clause together.
- [x] CHK002 Is the behaviour of the quarters sentence defined when staterooms, low berths and emergency low berths are all zero? [Gap, Spec §FR-010] → **Fixed**: new FR-010a omits the sentence; FR-021's list now names quarters, which it did not.
- [x] CHK003 Are the crew positions the breakdown may name, and the order they print in, enumerated anywhere in the spec? [Completeness, Spec §FR-018] → **Fixed**: FR-018 enumerates the seven derived positions and fixes their print order.
- [x] CHK004 Is the fuel-processor conversion rate (tons of unrefined fuel per ton of processor per day) stated, or only referred to as "the daily tonnage"? [Completeness, Spec §FR-017] → **Fixed**: FR-017 states the SRD's 20 tons per ton per day.
- [x] CHK005 Is the derivation of "the number of jumps at the ship's jump rating that the jump fuel supports" specified precisely enough to compute? [Completeness, Spec §FR-007] → **Fixed**: new FR-007a — the whole number of jumps at the rated Jump number that the tankage pays for.
- [x] CHK006 Does the spec define the tech level when no fitted component carries an SRD tech level at all? [Gap, Spec §FR-028, §FR-028a] → **Fixed**: new FR-028c — the question does not arise, because every ship carries the standard package included in its bridge or cockpit.
- [x] CHK007 Are requirements defined for whether the paragraph is line-wrapped, and at what width? [Gap] → **Fixed**: new FR-001a — a single unwrapped run, no column width imposed.
- [x] CHK008 Is the presence or absence of a trailing newline after the paragraph specified? [Gap] → **Fixed**: FR-001a — no trailing newline; the caller supplies the terminal's.
- [x] CHK009 Does the spec state where the two new design keys sort in the canonical dump order, given that round-trip losslessness is required? [Gap, Spec §FR-033] → **Resolved**: correctly a schema contract, not a spec requirement. FR-033 requires losslessness, which any stable order satisfies; [contracts/design-schema.md](../contracts/design-schema.md) pins the emission order.
- [x] CHK010 Are requirements defined for a design whose supplied purpose already ends in a period? [Gap, Spec §FR-029] → **Fixed**: FR-029 — a supplied description carries no sentence-ending punctuation; the renderer supplies it.

### Requirement Clarity

- [x] CHK011 Is the heading's exact spacing specified, given that the SRD writes "TL9 Asteroid Miner" for starships but "TL 9 Cutter" for small craft? [Ambiguity, Spec §FR-001] → **Fixed**: FR-001 gives the literal form `TL<tech level> <name>`. The SRD's small-craft spacing is inconsistent with its own starships and is not followed; noted in research §B.
- [x] CHK012 Is "the tons allocated to fire control" defined as a value the description can compute, given that cetools folds turret fire control into the turret's own ton? [Clarity, Spec §FR-011] → **Fixed**: FR-011 defines it as the hardpoint count, as all 20 examples print, and states that saying so allocates no tonnage.
- [x] CHK013 Is "describe each hangar's capacity" resolved to a specific quantity — tonnage capacity, craft count, or named craft? [Clarity, Spec §FR-014] → **Fixed**: FR-014 — capacity in tons of small craft, and explicitly not the craft carried, which a design does not record.
- [x] CHK014 Is the wording of the armour-options clause specified, or only that options MUST be stated? [Clarity, Spec §FR-016] → **Fixed**: new FR-016b — named after the protection rating, once per ship even across layers.
- [x] CHK015 Does FR-029b name the placeholder value, rather than pointing at "the same placeholder name the existing ship output uses"? [Clarity, Spec §FR-029b] → **Fixed**: FR-029b now names `Unnamed Ship`.
- [x] CHK016 Is "grouping identical turrets" defined by which fields must match — mount alone, or mount and weapon loadout? [Clarity, Spec §FR-012] → **Fixed**: new FR-012a — both mount type and weapon loadout.
- [x] CHK017 Is the relative order of bays and turrets within the installed-weapons sentence specified? [Gap, Spec §Assumptions] → **Fixed**: FR-012a puts bays first, matching every example that carries both.
- [x] CHK018 Is "any purchased options" in the computer sentence mapped to specific design fields, so a reader knows which option yields `/bis` and which `/fib`? [Clarity, Spec §FR-008] → **Fixed**: FR-008 maps `/bis` to jump-control specialization and `/fib` to hardened systems, per the SRD's Ship Computer Options section.

### Requirement Consistency

- [x] CHK019 Do FR-022a ("tonnage … MUST always be rendered as digits") and the zero-cargo edge case ("Cargo capacity is zero tons") state the same rule? [Conflict, Spec §FR-022a, §Edge Cases] → **Fixed**: they do now. FR-022a is narrowed and new FR-022b puts prose tonnage under the count rule, so the edge case is an instance of the rule rather than an exception to it.
- [x] CHK020 Does FR-022a's always-digits rule for tonnage agree with SC-002's requirement that the output use "the same wording patterns" as the SRD, which prints "two tons allocated to fire control"? [Conflict, Spec §FR-022a, §SC-002] → **Fixed**: FR-022a narrowed, FR-022b added, FR-022c added to keep the three rules a partition; recorded in the spec's Clarifications and Assumptions. [plan.md](../plan.md#deliberate-deviations-principle-i) deviation 1 is restated: this is no longer a deviation, since spec and SRD now agree.
- [x] CHK021 Do FR-020 and FR-025 together agree with the SRD's own "MCr597.870", which carries a trailing zero? [Consistency, Spec §FR-020, §FR-025] → **Resolved**: they deliberately do not. FR-025 overrides the SRD's fixed three-decimal habit, so cetools prints `MCr597.87`. A formatting choice that changes no figure; recorded in research §C.
- [x] CHK022 Is grouping of repeated items required consistently across the weapons, screens and hangars sentences, or only for turrets? [Consistency, Spec §FR-012, §FR-013, §FR-014] → **Fixed**: FR-013 now groups identical screens "as FR-012a groups identical turrets". Hangars deliberately do not group: FR-014 requires each hangar's own capacity, which is a per-entry figure, not a repeat.
- [x] CHK023 Does FR-030's list of tables needing display names match the set of components the sentence requirements can actually name — specifically, is a cockpit display name used by any sentence? [Consistency, Spec §FR-030, §FR-027] → **Fixed**: it did not. Cockpits are removed from FR-030's list — FR-027 needs only the word "cockpit", a hull-class distinction rather than a component spelling. `data-model.md` §4 updated to drop the column.
- [x] CHK024 Does FR-019's "number of low passengers" agree with FR-010's separate treatment of emergency low berths, given that the SRD's Chapter 8 says emergency berths carry no passengers while Chapter 9 prints "emergency low passengers"? [Conflict, Spec §FR-019, §FR-010] → **Fixed**: new FR-019a states they are not passenger capacity, and the spec's Assumptions now distinguish a *rules* conflict (rule governs) from a *phrasing* conflict (examples govern) — the distinction the original assumption lacked.
- [x] CHK025 Does the "Unarmed ship with hardpoints" edge case agree with FR-021 on whether an unarmed ship carries any wording about its missing weapons? [Consistency, Spec §Edge Cases, §FR-021] → **Fixed**: new FR-011a puts the SRD's own "but has no weapons installed" clause on the hardpoints sentence, so the edge case is satisfied without a negation sentence FR-021 would forbid.

### Acceptance Criteria Quality

- [x] CHK026 Can SC-002 ("read as the same kind of writeup") be objectively verified, or does it rest on a reviewer's judgement? [Measurability, Spec §SC-002] → **Fixed**: SC-002 restated as two checkable conditions — sentences in the FR-004 order, and each sentence matching the SRD's wording with only this ship's values substituted.
- [x] CHK027 Is the set of "SRD Chapter 9 sentence patterns" enumerated anywhere, so SC-004 can be checked rather than asserted? [Measurability, Spec §SC-004] → **Fixed**: SC-004 now refers to the FR-004 sentence list, which is the enumeration.
- [x] CHK028 Does SC-007 define what "correct description wording" means for a newly added row — specifically, which columns a row must carry to be renderable? [Measurability, Spec §SC-007] → **Fixed**: SC-007 names them — display name, plural where countable, tech level where the SRD tabulates one — and adds the derived tech level to what must come out right.
- [x] CHK029 Is SC-006's list of figures traceable to specific sentences, so a missing figure is a defined failure rather than a reading? [Traceability, Spec §SC-006] → **Fixed**: SC-006 now cites FR-006, FR-018, FR-015 and FR-020.
- [x] CHK030 Does SC-005 identify which existing tests constitute "all previously-passing ship build, generation, TOML round-trip and cost calculations"? [Measurability, Spec §SC-005] → **Fixed**: SC-005 restated as a rule over the suite — every such test passing before must pass afterwards *unmodified*, and only rendered-output tests are replaced. That is checkable from the diff.

### Scenario & Edge Case Coverage

- [x] CHK031 Are requirements defined for a small craft that fits no computer, given that FR-027 specifies only the cockpit wording when one is present? [Coverage, Spec §FR-027] → **Resolved**: a computer is equipment, so FR-021's omission rule already covers it; [contracts/description-format.md](../contracts/description-format.md) §4 states the sentence is omitted.
- [x] CHK032 Are requirements defined for a design whose jump fuel supports fewer than one jump? [Coverage, Gap, Spec §FR-007] → **Fixed**: FR-007a keeps the clause and states zero jumps, so the stated tankage is accounted for; FR-021a lists this as one of the three sanctioned zero-quantity clauses.
- [x] CHK033 Are requirements defined for a turret carrying two different weapon types in one mount? [Coverage, Gap, Spec §FR-012] → **Resolved**: FR-012 requires describing "its weapons" and FR-024 governs the join; contract §8 gives the per-slot grouping. No further requirement needed.
- [x] CHK034 Are requirements defined for ammunition carried across more than one turret group? [Coverage, Gap, Spec §FR-012] → **Fixed**: FR-012a aggregates ammunition across every turret sharing a kind and type.
- [x] CHK035 Are requirements defined for more than one hangar fitting, with different capacities, on the same ship? [Coverage, Gap, Spec §FR-014] → **Fixed**: FR-014 requires *each* hangar's capacity; contract §10 gives the multi-entry sentence form.

### Dependencies & Assumptions

- [x] CHK036 Is the assumption that "component tech levels the SRD states but the current rules data omits are transcribed from the SRD tables" validated against which categories the SRD actually tabulates? [Assumption, Spec §Assumptions] → **Fixed**: research §D audits every table column by column, and FR-028a now says which categories tabulate a tech level is a finding from reading every table, not an assumption from the category's importance.
- [x] CHK037 Is the assumption that the TOML dump remains the machine-readable output stated as a requirement, or only in Assumptions? [Traceability, Spec §Assumptions, §FR-002] → **Resolved**: correctly an assumption. FR-002 scopes the replacement to the sheet and says nothing about `--toml`, which is therefore unchanged; the contract's CLI section records that.
- [x] CHK038 Does the spec state whether the checked-in example designs may be edited, given that they encode hand-worked SRD figures relied on by SC-005? [Gap, Spec §Dependencies] → **Fixed**: SC-005's "unmodified" requirement covers the tests that read them, and [contracts/design-schema.md](../contracts/design-schema.md) states the examples are not edited — a new example is added instead.

## Notes

- Iteration 1 (2026-07-24): One [NEEDS CLARIFICATION] marker on FR-028 (tech level
  sourcing). Presented to the user; resolved and folded into FR-028. All other items
  passed on first review.
- `cetools ship build` / `cetools ship generate` are named in FR-002 as the existing
  user-facing surface whose output changes, not as an implementation prescription.
- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
- Post-plan review (2026-07-24): all 38 items worked. 27 produced a `spec.md` edit; 11 were
  already answered by an existing requirement or by the design artifact that is the right home
  for the answer.
- The spec gained 19 new sub-requirements (FR-001a, FR-006a, FR-007a, FR-009a, FR-010a,
  FR-011a, FR-012a, FR-016b, FR-019a, FR-019b, FR-021a, FR-022b, FR-022c, FR-023a, FR-024a,
  FR-025a, FR-028c) and reworded eleven existing ones. No requirement was removed; one list
  (FR-030's) lost an entry that named a component no sentence spells.
- CHK019/CHK020 (the FR-022a conflict) are closed by the amendment; `plan.md`'s deviation 1 is
  restated accordingly and now records the 11–99 number-band departure, which is the only
  remaining knowing departure from the SRD's examples.
