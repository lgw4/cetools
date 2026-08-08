# Requirements Quality Checklist: Vehicle Design System

**Purpose**: Formal pre-tasks gate. Test whether the requirements in `spec.md` are complete, clear,
consistent and measurable enough that `/speckit-tasks` can generate tasks without inventing
answers, and whether they still hold against what Phase 0 and Phase 1 discovered.

**Created**: 2026-08-07

**Worked through**: 2026-08-07. All 40 items resolved; see the resolution log at the foot of this
file for what changed and where.

**Feature**: [spec.md](../spec.md)

**Scope**: All four requirement areas—SRD fidelity and divergence, construction rules and
validation, generation and determinism, the command-line and output contract—plus conflicts
between `spec.md` and the downstream artifacts (`research.md`, `plan.md`).

**How to read an item**: every item asks about what the requirements *say*, not about whether code
works. A checked box means the requirement is written well enough to build from, not that the
behavior was tested.

## SRD Fidelity and Divergence

- [x] CHK001 Is the source chapter for the fifteen published vehicles stated correctly, given the construction chapter carries no worked examples at all? [Conflict, Spec §FR-021 and §US2 vs research.md C-001]
- [x] CHK002 Are requirements defined for the case where the construction rules contradict *themselves*, as distinct from a worked example contradicting the rules? [Gap, Spec §FR-017 vs research.md R-003]
- [x] CHK003 Is the precedence rule for resolving an intra-chapter contradiction—a table versus prose in the same chapter—stated as a requirement rather than only as a research decision? [Gap, research.md R-003]
- [x] CHK004 Is the required structure of the divergence page specified beyond "opening with the vehicles section", given the design implies distinct worked-example, rules-defect and generation-policy sections? [Completeness, Spec §FR-020]
- [x] CHK005 Is the machine-readable shape the documentation check must parse stated as a requirement, given FR-020a makes stale divergence prose a gate failure? [Gap, Spec §FR-020a vs research.md R-007]
- [x] CHK006 Does the spec define what counts as "a figure" for the figure-by-figure transcription, so completeness of a vehicle's transcription is objectively assessable? [Measurability, Spec §FR-021a]
- [x] CHK007 Is the comparison tolerance for a transcribed figure specified, given SC-002 requires an exact match while the design calls for a closeness test with an explicit tolerance? [Conflict, Spec §SC-002 vs research.md R-011]
- [x] CHK008 Are the fifteen catalog vehicles enumerated by name in the requirements, or only by count per category with four named as awkward cases? [Completeness, Spec §FR-021, §FR-023, §SC-001]
- [x] CHK009 Is the catalog naming convention specified, given SC-001 requires every one of the fifteen names to appear in a listing and FR-024a requires building by name? [Gap, Spec §FR-021, Key Entities: Catalog Entry]
- [x] CHK010 Does FR-019's ban on a selectable policy clearly extend to the rules-table divergences, where cetools chooses chapter prose over a printed table rather than correcting a worked example? [Ambiguity, Spec §FR-019 vs research.md R-003]

## Construction Rules and Validation

- [x] CHK011 Is the table set quantified, so that "the complete tables of Chapter 1" is a checkable claim rather than a judgment call at review time? [Measurability, Spec §FR-003]
- [x] CHK012 Is the discount's base defined to match the rule it cites, given fuel and weapon ammunition are exempt from the standard design discount? [Conflict, Spec §FR-007 vs research.md C-002]
- [x] CHK013 Is build time's derivation and unit specified, or only its existence alongside price? [Gap, Spec §FR-008]
- [x] CHK014 Is the criterion separating construction rules from play rules stated as a testable rule rather than as an example list, given two options are bought specifically to cancel a play penalty? [Clarity, Spec §FR-010 and Assumptions vs research.md R-004]
- [x] CHK015 Are display-edge rounding rules specified—precision for spaces, prices and speeds—given all rounding is deferred to that edge? [Gap, Spec §FR-033, §FR-005]
- [x] CHK016 Is the permitted weapon-and-mount matrix defined by reference to something checkable, so "combinations Chapter 1 does not permit" is decidable without reading the source? [Clarity, Spec §FR-016]
- [x] CHK017 Is FR-001's stated rationale accurate, given vehicle armor varies by type with tech level acting as an availability gate rather than as a second dimension? [Ambiguity, Spec §FR-001 vs research.md R-002]
- [x] CHK018 Are the required contents of the Universal Vehicle Description Format paragraph specified as a requirement, or inferable only from a sentence in User Story 1? [Completeness, Spec §FR-025, §US1]
- [x] CHK019 Is the over-20-ton rejection criterion expressed in terms the transcribed tables can decide, rather than as a category the builder must recognize? [Clarity, Spec §FR-013 vs research.md R-004]
- [x] CHK020 Do FR-013 and SC-005 agree on the rejection message, given SC-005 requires naming watercraft as the missing capability for a vehicle that may merely be oversized? [Conflict, Spec §FR-013 vs §SC-005]

## Scenario and Edge Case Coverage

- [x] CHK021 Are requirements defined for the known cargo-space divergence in the Air/Raft, or does the acceptance scenario cover only its four price figures? [Coverage, Spec §US2-3 vs research.md C-003]
- [x] CHK022 Are error-stream and exit-code requirements defined for every failure mode, or only for the one scenario that says nothing reaches standard output? [Gap, Spec §US1-3]
- [x] CHK023 Are the watercraft-only rows required to be transcribed and then gated, or is transcribing unreachable rows left to inference from FR-003? [Coverage, Spec §FR-003, §FR-013 vs research.md R-004]
- [x] CHK024 Is a requirement stated for how a table row that no catalog vehicle and no generation path exercises is identified, so SC-006 can be assessed rather than asserted? [Measurability, Spec §SC-006]

## Generation and Determinism

- [x] CHK025 Is the set of vehicle roles enumerated, or left open by "and the like", given SC-011 requires every role to be named in user-facing prose? [Clarity, Spec §FR-026b, §SC-011]
- [x] CHK026 Is a loadout profile's content defined well enough that "only components its role's loadout profile permits" can be objectively verified? [Measurability, Spec §SC-011, §FR-026b]
- [x] CHK027 Is the ordering constraint on random draws stated as a requirement, given reproducibility depends on the role draw preceding every pool it selects? [Gap, Spec §FR-031 vs research.md R-009]
- [x] CHK028 Does the spec distinguish a constraint that must be refused up front from one that may be degraded and reported, or does FR-032 treat all unmet constraints alike? [Gap, Spec §FR-032, §FR-026a vs research.md R-008]
- [x] CHK029 Is the verification method for byte-identical output specified, including which constraint paths a pinned baseline can and cannot cover? [Clarity, Spec §SC-003 vs research.md R-010]
- [x] CHK030 Is the coarse locomotion alias set enumerated in the requirements, or only required to exist, resolve and be documented? [Completeness, Spec §FR-026a, §SC-010]
- [x] CHK031 Is the location of the generation-policy documentation specified, given FR-026c requires user-facing prose while the design places it on the divergence page—a page whose stated subject is divergences? [Conflict, Spec §FR-026c, §FR-020 vs research.md R-008]
- [x] CHK032 Are requirements defined for how an unmet constraint is surfaced—which stream, which exit code, and whether the vehicle is still emitted? [Gap, Spec §FR-032]

## Command-Line and Output Contract

- [x] CHK033 Is "wherever a vehicle is described" bounded, so the scope of the component-table flag across build, generate and catalog is unambiguous? [Clarity, Spec §FR-025a]
- [x] CHK034 Is the ship behavior FR-028 mirrors restated as a requirement, or does implementing it depend on reading the existing CLI code? [Traceability, Spec §FR-028, §US4-3]
- [x] CHK035 Are requirements defined for the catalog listing's output format, given it is a referee-facing surface and SC-001 asserts what it must contain? [Gap, Spec §FR-024a, §SC-001]
- [x] CHK036 Are mutually exclusive flag combinations enumerated completely, beyond the two the spec names? [Completeness, Spec §FR-025a, §US4-3]

## Dependencies, Assumptions and Traceability

- [x] CHK037 Is the Dependencies claim that the documentation check is "the one place the feature reaches outside the vehicles domain and the CLI" consistent with the files the plan actually changes? [Conflict, Spec Dependencies vs plan.md Project Structure and Complexity Tracking]
- [x] CHK038 Is the assumption that the documentation check can read transcribed published figures without reaching into the test tree stated and validated as a requirement? [Assumption, Spec §FR-020a vs research.md R-007]
- [x] CHK039 Are non-functional requirements deliberately excluded and said to be, or absent by omission? [Gap]
- [x] CHK040 Is a requirement and figure identifier scheme established that the divergence page, the stat-block comparison test and the documentation check can all cite consistently? [Traceability, Spec §FR-020, §FR-021a, §SC-002]

## Resolution log

Thirty-nine items were closed by amending `spec.md`; one was closed by confirming a downstream
artifact already fixes it. Nine requirements are new.

| Item | Resolved by |
|---|---|
| CHK001 | US2 opening and FR-021 now name Chapters 2, 3, 4 and 6 and state that the construction chapter carries no examples |
| CHK002, CHK003, CHK010 | **New FR-017a**: prose beats a table within the same chapter, an uncontradicted printed value is transcribed as printed, and both are recorded. FR-018 and FR-019 widened to cover both classes |
| CHK004 | FR-020 fixes three sections: worked examples, rules defects, generation policy |
| CHK005, CHK038 | **New FR-020b**: both enforcement paths read the same rows; Vehicle/Figure/Published/cetools/Why columns; figures readable without importing from the test tree |
| CHK006, CHK040 | FR-021a enumerates the ten figure labels, which doubles as the identifier scheme |
| CHK007 | SC-002 now compares within an explicit stated tolerance instead of requiring exact equality |
| CHK008 | FR-021 enumerates all fifteen by name |
| CHK009 | **New FR-021b**: stable lowercase hyphenated names, treated as a compatibility surface |
| CHK011 | FR-003 states forty tables, and that watercraft and over-20-ton rows are transcribed then gated |
| CHK012 | FR-007 rewritten to discountable lines only, quoting the rule |
| CHK013 | FR-008 gives the derivation, the custom-made multiplier, and a floor of one |
| CHK014 | FR-010 states the test: does it feed component selection or a printed figure? |
| CHK015 | **New FR-034**: fixed precision, stripped trailing zeros, no scientific notation, thousands separators on money |
| CHK016 | FR-016 makes both tests table membership |
| CHK017 | FR-001 re-argued from key shape; the old rationale is retained as a correction so the change is legible |
| CHK018 | FR-025 enumerates the paragraph's slots; **new FR-025b** omits four |
| CHK019, CHK020, CHK023 | FR-013 split into two limits with accurate messages; SC-005 follows |
| CHK021 | New US2 acceptance scenario 4 covers the unbalanced Spaces column |
| CHK022, CHK032 | **New FR-029a**: stdout carries the artifact, stderr everything else, exit code tracks whether an artifact was produced |
| CHK024 | SC-006 states how the exercised-row set is collected |
| CHK025 | FR-026b fixes six roles |
| CHK026 | **New FR-026d**: the five decisions a loadout profile makes |
| CHK027 | **New FR-030a**: the role is drawn first, as a requirement |
| CHK028 | FR-032 split into refused-outright and degraded-and-reported, with the pin-versus-roll rule |
| CHK029 | FR-031 and SC-003 state the caveat and the two-part verification |
| CHK030 | FR-026a enumerates all nine aliases |
| CHK031 | FR-026c points at the generation-policy section of `DIVERGENCES.md` |
| CHK033 | FR-025a bounds it to build and generate |
| CHK034, CHK036 | FR-028 enumerates all three argument rules self-containedly |
| CHK035 | Already fixed by [contracts/cli.md](../contracts/cli.md)—one name per line on stdout—and now covered at requirement level by FR-029a. No spec change |
| CHK037 | Dependencies corrected; registration-cost files listed separately |
| CHK039 | New Assumptions bullet states there are deliberately none, and why |

## What this pass turned up beyond the checklist

Two findings that were not on the list and are worth a reader's attention:

1. **The construction chapter contradicts itself in nine places, not seven.** Verifying build time
   against the SRD found that its prose says to multiply base hours by *additional* armor while its
   own worked example one sentence later multiplies by a *total* of 12 Armor. Verifying the
   description format found four starship slots in the vehicle template—fire control tonnage, a
   hardpoints sentence, screens and small craft hangars—one of which still reads "This **ship**
   has". Both are recorded as R-003 defects 8 and 9 in [research.md](../research.md); `plan.md` is
   updated from seven to nine.
2. **Correcting FR-007 invalidated a published acceptance figure.** US2 scenario 3 asserted cetools
   would print Cr94,153.05 for the Air/Raft, which is Cr104,614.5 × 0.9. Once fuel is exempt from
   the discount and the Air/Raft carries fuel, that is no longer the figure the rules produce. The
   scenario now states the rule and defers the number to the authored design rather than asserting
   an arithmetic that no longer holds. **This is the one open number in the feature**: it cannot be
   computed until `catalog/air-raft.toml` exists, and it must be checked when it does.

## Notes

- Check items off as resolved: `[x]`. An item is resolved when `spec.md` answers it, not when
  someone knows the answer.
- This checklist does not restate the spec-quality items already cleared in
  [requirements.md](./requirements.md); it assumes those and probes deeper.
