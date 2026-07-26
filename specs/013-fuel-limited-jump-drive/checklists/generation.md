# Generation Rules Checklist: Fuel-Limited Jump Drive Rating

**Purpose**: Validate the quality of the generation requirements (determinism, tonnage arithmetic,
fallback boundary, scope) before `/speckit-tasks` turns them into work items
**Created**: 2026-07-26
**Worked through**: 2026-07-26, all 35 items resolved
**Feature**: [spec.md](../spec.md)
**Audience**: Author self-review, run before task generation
**Depth**: Standard

This checklist tests whether the *requirements are well written*, not whether the implementation
works. Companion to [requirements.md](./requirements.md), which covers the generic spec-quality
gates; this one goes deeper on the four domains where an ambiguity would produce a wrong task.

## Determinism & Draw Order

- [x] CHK001 Is FR-008's "no additional random draws" stated as an invariant checkable in full, or
  does the named guard (ship name drawn last, exactly once) leave a draw inserted earlier in the
  sequence unconstrained? [Measurability, Spec §FR-008]
- [x] CHK002 Is FR-009's "every run" qualified to within a release, given the contract explicitly
  disclaims cross-version seed-to-ship stability? [Conflict, Spec §FR-009 vs contracts §1
  "Explicitly not guaranteed"]
- [x] CHK003 Is "identical ship" given one definition (object equality, serialized design, or
  rendered prose) used consistently by US3 AS1, SC-005's "byte-for-byte" and SC-006's "identical"?
  [Consistency, Spec §SC-005, §SC-006]
- [x] CHK004 Is a sample size specified for SC-006's "100% of trials", as SC-001 specifies "at least
  2000 seeds"? [Measurability, Spec §SC-006]
- [x] CHK005 Is any success criterion defined for FR-008, or does the draw-order guarantee rest
  solely on a replacement guard the spec defers to planning? [Traceability, Gap, Spec §FR-008,
  §Assumptions]
- [x] CHK006 Are determinism requirements stated for the hull-constrained path as well as the
  unconstrained one? [Coverage, Spec §FR-009, §FR-011]

## Tonnage & Fuel Arithmetic

- [x] CHK007 FR-003 lists "hull" among the mandatory systems deducted from the budget, while Key
  Entities lists only bridge, maneuver drive, power plant and power-plant fuel. Is the deduction set
  stated identically in both places? [Conflict, Spec §FR-003 vs §Key Entities]
- [x] CHK008 Is a rounding or tolerance rule defined for the fractional tonnage that 0.1 x hull x
  rating produces, so "fits within the tonnage remaining" and SC-002's "at least" are decidable at
  the boundary? [Ambiguity, Spec §FR-003, §SC-002]
- [x] CHK009 Is "rules-legal" defined by enumerated, checkable conditions rather than left to the
  reader? [Clarity, Spec §FR-013]
- [x] CHK010 Is the predicate for a drive being "legal for the hull" defined in observable terms
  anywhere in the spec? [Gap, Spec §FR-003, §FR-014]
- [x] CHK011 Does FR-005 specify the order of the "subsequent allocations", or does it rely on an
  unstated "same as today"? [Clarity, Spec §FR-005]
- [x] CHK012 Is a non-negative cargo requirement stated in the spec, or only implied by FR-013 and
  asserted downstream in the contract? [Gap, Spec §FR-013 vs contracts §1 G5]
- [x] CHK013 Are any requirements defined for the ship's cost, given the Overview cites wasted money
  as motivation but no FR or SC constrains credits? [Gap, Spec §Overview]
- [x] CHK014 Is power-plant fuel explicitly required to stay constant across the adjustment, rather
  than inferred from "the correction adjusts only the jump drive"? [Completeness, Spec §Assumptions]

## Fallback Boundary & Edge Cases

- [x] CHK015 Where several legal drives share the lowest rating, does FR-014 say which letter is
  installed, and is FR-004's standing lightest-drive rule stated to apply inside the fallback?
  [Ambiguity, Spec §FR-014 vs §FR-004]
- [x] CHK016 Is the case of two legal drives sharing both the same rating and the same tonnage
  addressed, given the contract asserts a *unique* lightest code? [Gap, Spec §FR-004 vs contracts §4
  C3]
- [x] CHK017 Is FR-014's exception list identical everywhere it is restated (FR-001, FR-002, FR-007,
  FR-014 itself, US1 AS2, US2 AS1, SC-001/SC-002/SC-004)? [Consistency, Spec §FR-014]
- [x] CHK018 Is an observable criterion defined for classifying a generated ship as an FR-014
  starved-hull ship, given three success criteria require counting them separately? [Measurability,
  Spec §SC-001, §US1 Independent Test]
- [x] CHK019 Are requirements defined for a hull whose mandatory systems alone meet or exceed its
  tonnage, leaving a zero or negative drive budget? [Gap, Edge Case]
- [x] CHK020 Is it recorded as an assumption that every tabulated hull has at least one legal jump
  drive, on which FR-014's "install the lowest-rated legal drive" depends? [Assumption, Spec §FR-014]
- [x] CHK021 Does the spec state whether an FR-014 ship's description must still be internally
  consistent (drive letter, stated rating and jump count agreeing) even while reporting zero jumps?
  [Coverage, Exception Flow, Spec §US2 AS2, §FR-014]
- [x] CHK022 Is FR-005's freed-tonnage rule stated to apply identically in the downgrade and
  same-rating-substitution cases, including when freed tonnage changes which fittings become
  affordable? [Completeness, Spec §FR-005, §Edge Cases]

## Scope & Regression Boundaries

- [x] CHK023 Is FR-012's exemption scoped to design *files*, or to any caller-supplied design
  including one constructed programmatically? [Ambiguity, Spec §FR-012 vs contracts §2]
- [x] CHK024 Is "small-craft output" defined as the object, the serialized design, or the rendered
  prose? [Measurability, Spec §SC-005]
- [x] CHK025 Does SC-007 name the pre-change reference it compares against, given the spec
  simultaneously states the existing pinned baseline necessarily moves? [Conflict, Gap, Spec §SC-007
  vs §Assumptions]
- [x] CHK026 Are FR-008, FR-011 and FR-012 each traceable to a measurable success criterion?
  [Traceability, Gap]
- [x] CHK027 Are requirements stated for designs saved by the pre-change generator (carrying
  over-rated drives) still loading and building unchanged? [Gap, Coverage]
- [x] CHK028 Is it stated that the correction applies only to random generation, and not to any
  other entry point that selects components on the caller's behalf? [Clarity, Spec §Assumptions,
  §FR-012]

## Cross-Artifact Consistency

- [x] CHK029 Is the relationship stated between FR-001's "at least one complete jump" and the data
  model's stronger post-condition that the assumed jump distance *equals* the rating? [Consistency,
  Spec §FR-001 vs data-model.md §Generated ship]
- [x] CHK030 Is the Assumption that a same-rating substitution leaves the power plant's legal
  candidate set untouched extended to the FR-003 downgrade case, where the rating does change? [Gap,
  Spec §Assumptions, §FR-003]
- [x] CHK031 Do the spec's observed-frequency figure (111 of 2000) and the plan's movement figure
  (54% of seeds) each carry enough context that neither reads as a contradiction of the other?
  [Clarity, Spec §Overview vs plan.md §Summary]
- [x] CHK032 Is the spec's "not observed in a 2000-seed sweep" wording for FR-014 reconciled with the
  plan's stronger finding that the case is unreachable over the full cross product? [Consistency,
  Spec §FR-014 vs plan.md §Summary]

## Acceptance Criteria Quality

- [x] CHK033 Can US1's Independent Test be executed from observable ship values alone, without
  recomputing the generator's own drive search? [Measurability, Spec §US1]
- [x] CHK034 Are the concrete figures in the acceptance scenarios (100-ton hull, 56 tons remaining)
  traceable to a stated derivation, so they can be re-verified if the tables change? [Traceability,
  Spec §US1 AS1]
- [x] CHK035 Does every functional requirement have at least one acceptance scenario or success
  criterion that would fail if the requirement were violated? [Coverage, Acceptance Criteria]

## Resolutions

Three items were defects in the spec, one of them a wrong number. Four needed no change. The rest
were genuine under-specification, now written down.

| Item | Resolution |
| --- | --- |
| CHK001 | FR-008 rewritten. The old wording implied a seed's total draw count is stable; it is not, and cannot be. `_select_turrets` skips its weapon draw when a mount does not fit the tonnage remaining, so freed tonnage legitimately changes the draw count downstream. FR-008 now constrains the adjustment step only, and says so explicitly. |
| CHK002 | FR-009 scoped to "within a given release", with cross-release movement called out. |
| CHK003, CHK024 | "Equal ships" defined once in Assumptions as field equality, and SC-005 reworded off "byte-for-byte". |
| CHK004, CHK006 | SC-006 now names the sweep and covers the standard-hull, small-craft and hull-constrained paths. |
| CHK005, CHK026 | Added SC-008 (draw order), SC-009 (hull size), SC-010 (authored designs). FR-008, FR-011 and FR-012 were previously untraceable to any success criterion. |
| CHK007 | **Defect.** FR-003 listed "hull" among the systems deducted from the hull's own tonnage. Removed. |
| CHK008 | Verified: zero boundary disagreements between the FR-003 fit test and the generator's `floor(remaining / (0.1 x hull))` across every hull and rating. Drive and bridge tonnages are integers, so one float appears. Recorded as an Assumption and flagged as a property to pin with a test, since it rests on floating-point behaviour rather than on any rule. |
| CHK009 | FR-013 now defines "rules-legal" as passing the same validation a caller-supplied design must pass. |
| CHK010, CHK016, CHK020 | Key Entities now gives the legality predicate, records that every hull has at least one legal drive (the smallest has three), and records that no two letters share a tonnage cost, so "lightest at a rating" always names exactly one drive. All three verified against the tables. |
| CHK011 | FR-005 states the subsequent allocations keep their existing order and rules. |
| CHK012 | No change. SC-003 already constrains total allocated tonnage to the hull, which is the same claim as non-negative cargo. |
| CHK013 | No requirement added, but Assumptions now says so explicitly: cost is unconstrained and follows from the components chosen. |
| CHK014 | Assumptions notes power-plant fuel follows from the power plant alone, so it cannot move. |
| CHK015, CHK019 | FR-014 now applies FR-004 inside the fallback (lightest at the lowest rating) and covers the degenerate zero-budget case. The minimum budget over the full cross product is 69 tons on a 100-ton hull, so that case is unreachable. |
| CHK017 | No change. The exception list is consistent across all nine places it is restated. |
| CHK018, CHK033 | FR-014 now defines an FR-014 ship observably, recomputable from the finished ship, so the separate counts SC-001 requires do not depend on generator internals. |
| CHK021 | FR-007 now requires an FR-014 ship's description to stay internally consistent even while reporting zero jumps. |
| CHK022, CHK029 | No change. FR-005 already names both cases; data-model.md already explains that its equality post-condition is stronger than FR-001. |
| CHK023, CHK028 | FR-012 broadened from "design file" to any caller-supplied design, file or in-memory, and states the correction applies to no other entry point. |
| CHK025 | **Conflict resolved.** SC-007 now names its pre-change reference as the generator immediately before this feature, explicitly not the feature-012 pinned baseline that this feature invalidates. |
| CHK027 | Assumptions records that the stored design schema is unchanged, so a design saved by the pre-change generator still loads and builds identically. |
| CHK030 | Assumptions extended to the downgrade case: the power plant's legality floor is the higher of the jump and maneuver ratings, so lowering the jump rating only relaxes it. Verified in `_select_drive_codes`. |
| CHK031, CHK032 | Assumptions now carries the 54% figure alongside the 5.5%, and cites the full cross product rather than the 2000-seed sample for FR-014's unreachability. |
| CHK034 | **Defect, wrong number.** The acceptance scenario and the contract's fourth worked example both used a 72-ton drive budget as 56. The 56 is that ship's *fuel tankage* (50 jump plus 6 power plant), an output of the allocation, not the budget going into it. Corrected in both spec.md and contracts/jump-drive-fit.md, with the derivation spelled out. The resulting drive is `B` either way, which is why the error was invisible in the outcome. |
| CHK035 | Added a Requirement Coverage table mapping all fourteen FRs to acceptance scenarios and success criteria. |

## Notes

- Two follow-ups for `/speckit-tasks`, both arising from CHK001 and CHK008:
  - The draw-order test must assert SC-008's invariant (name last, drawn once; jump, maneuver and
    power drawn in order). It must **not** assert a stable draw count per seed, which FR-008 now
    explicitly disclaims.
  - The fit test and the generator's jump-distance arithmetic agree at the boundary today, but only
    empirically. Worth one test pinning that agreement across every hull and rating.
- `plan.md` §Summary still says "No draw is added or moved, so the seam that makes a seed
  reproducible is untouched". That is true of the adjustment itself but reads as a stronger claim
  than FR-008 now makes; worth a wording pass when the plan is next touched.
