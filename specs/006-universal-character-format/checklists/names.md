# Name Generation & Data Source Requirements Checklist: Universal Character Format Output

**Purpose**: Validate the quality (completeness, clarity, consistency, measurability, edge-case
coverage) of requirements governing the new name-generation feature — FR-001 and the "Name
Source" key entity — before proceeding to `/speckit-tasks`.
**Created**: 2026-07-03
**Feature**: [spec.md](../spec.md)
**Depth**: Standard
**Audience / Timing**: Author, self-review prior to task generation

**Note**: This checklist tests whether the *requirements* about name generation are well-written
and unambiguous — it does not test whether any implementation works.

## Requirement Completeness

- [x] CHK001 Are the minimum sizes (or any size constraint) for `FIRST_NAMES` and `LAST_NAMES` specified, or is "whatever the data set needs" left fully open-ended? [Completeness, data-model.md §Name Source]
- [x] CHK002 Is there a requirement for what must happen if either name list were empty at runtime, beyond the assumption that both are non-empty data tables? [Gap, Edge Case]
- [x] CHK003 Are content requirements for individual name entries specified (e.g., allowed characters/casing, whether duplicate entries within one list are permitted)? [Gap, Completeness]
- [x] CHK004 Is the scope of "no gender concept is introduced anywhere in the character model" fully bounded — does it constrain only the name lists, or also any future rank-title/pronoun usage? [Clarity, Spec §FR-001]

## Requirement Clarity

- [x] CHK005 Is "drawn independently" (first name vs. last name) defined precisely enough to rule out an implementation that pairs them (e.g., same index into both lists)? [Clarity, Spec §FR-001]
- [x] CHK006 Is the assembled name's exact format (`"<first> <last>"`, single space, no middle name/initial) stated as a requirement, or only inferable from data-model.md? [Clarity, Ambiguity, Spec §Key Entities]
- [x] CHK007 Does the spec require name generation to reuse the existing `DiceRoller` randomness seam, or is that a research.md design choice not binding at the requirements level? [Clarity, Spec vs. research.md]

## Requirement Consistency

- [x] CHK008 Is "single unisex list, no gender concept" (FR-001) stated consistently everywhere names are mentioned (Key Entities, Assumptions, Edge Cases)? [Consistency]
- [x] CHK009 Do FR-001 and the "Name Source" Key Entity agree on how many data sets exist and how they combine, with no conflicting cardinality (independent draw vs. any implied pairing)? [Consistency, Spec §FR-001 vs §Key Entities]

## Scenario & Edge Case Coverage

- [x] CHK010 Is the duplicate-name-across-characters scenario unambiguous about scope (any two characters generated in any run, not just the same run)? [Edge Case, Spec §Edge Cases]
- [x] CHK011 Are requirements defined for duplicate/degenerate names occurring *within* a single character (e.g., the drawn first name and last name being identical text)? [Gap, Edge Case]
- [x] CHK012 Is it specified that no name is generated on a failed-generation (enlistment/survival failure) path, and that this omission cannot affect roller call order for other rolls? [Coverage, Spec §FR-010 vs research.md]

## Non-Functional / Testability

- [x] CHK013 Can "drawn independently from two separate lists" be objectively verified by a test, i.e., is there a measurable signal distinguishing independent draws from paired/correlated draws? [Measurability, Spec §FR-001]
- [x] CHK014 Is determinism of name generation under test (via roller test doubles) stated anywhere as a testable acceptance criterion, or only inferred from the constitution's Test-First principle? [Traceability, Gap]

## Dependencies & Assumptions

- [x] CHK015 Is the assumption that names aren't varied "by culture, homeworld, species, or gender" checked against Constitution Principle I (SRD-Fidelity) to confirm the SRD itself imposes no such UCF naming requirement? [Assumption, Spec §Assumptions]
- [x] CHK016 Is the dependency on `DiceRoller.roll(sides)` supporting arbitrary list lengths (not just the 6-sided career-table convention) stated as a requirement, rather than left as an implementation detail surfaced only in research.md? [Dependency, Spec vs. research.md]
- [x] CHK017 Is ownership/curation of the actual `FIRST_NAMES`/`LAST_NAMES` contents specified (minimum count, source, appropriateness), or left entirely to implementation discretion? [Gap, Assumption]

## Ambiguities & Conflicts

- [x] CHK018 Is the assumption "every implemented career's rank table has a title at every rank" (needed so a rank title is always available before the name) traceable to a verification step, or merely asserted? [Assumption, Spec §Assumptions]

## Resolution Log

Every item was investigated against spec.md, data-model.md, research.md, and (where a claim
touched code) the actual source in `src/cetools/`. **Fixed** = spec.md/data-model.md edited to
close a real gap. **Confirmed** = investigated and found already adequate; no edit made.

| Item | Verdict | Detail |
|---|---|---|
| CHK001 | Fixed | FR-001 and the Name Source key entity now require ≥10 entries per list (data-model.md updated to match). |
| CHK002 | Fixed (via CHK001) | A list satisfying "≥10 entries" can never be empty; the runtime-empty scenario is now foreclosed by requirement, not left as an unstated assumption. |
| CHK003 | Fixed | Added: entries are proper-cased words; intra-list duplicates are explicitly permitted (affect draw probability only). |
| CHK004 | Confirmed | FR-001 already says "no gender concept is introduced **anywhere in the character model**" — scope is already maximal, not name-list-only. |
| CHK005 | Fixed | FR-001 now states the two draws "MUST be two independent random selections... never derived from a single shared random value or a shared list index"; data-model.md's `generate_name` row now says "exactly two independent calls... never a single shared roll or index." |
| CHK006 | Fixed | FR-001 now states the combination format explicitly: `"<first> <last>"`, single space, no middle name/initial. |
| CHK007 | Confirmed | Correctly left to research.md/plan.md — mandating a specific randomness API (`DiceRoller`) in spec.md would violate the spec's own "no implementation details" quality bar. Not a gap. |
| CHK008 | Confirmed | Checked FR-001, Key Entities, and Assumptions side-by-side — the unisex/no-gender wording is repeated consistently, no conflict. |
| CHK009 | Confirmed | FR-001 and the Name Source key entity agree: two independent lists, drawn independently, combined — no cardinality conflict. |
| CHK010 | Confirmed | Edge Cases already reads "two generated characters" with no run/session qualifier — the tool is a single-shot CLI with no session concept, so the broad reading is already the only reading. |
| CHK011 | Fixed | Added an Edge Case and an Assumptions bullet explicitly covering a single character's first name and last name coinciding (e.g. "Grant Grant"), extending the existing cross-character duplicate-acceptance rule. |
| CHK012 | Confirmed | research.md's "Where name generation happens" and "Impact on existing mechanics" sections already specify the name roll happens after all pass/fail branches, so it never perturbs `SequenceRoller`-based failure-path tests — directly satisfies FR-010. |
| CHK013 | Confirmed | Now testable given the CHK005 fix: a test can assert `generate_name` makes exactly two `roll()` calls (one per list) via the existing `ConstantRoller`/`SequenceRoller` doubles in `tests/conftest.py`, distinguishing independent draws from a shared-index implementation. |
| CHK014 | Confirmed | Deliberately left to Constitution Principle IV (Test-First) plus Governance's blanket compliance requirement, rather than restated per-feature — restating it here would be redundant, not a gap. |
| CHK015 | Fixed | Assumptions bullet now states explicitly that the cited SRD page defines only the UCF output layout, not a name-generation/cultural-variation mechanism, so the assumption doesn't conflict with Principle I. |
| CHK016 | Confirmed | Verified directly against `src/cetools/engine/dice.py:11-13`: `RandomDiceRoller.roll(sides, count=1)` = `random.randint(1, sides)`, uniform over **any** `sides` value — research.md's claim is not just asserted, it's true of the actual code today. Appropriately left as a research.md-level dependency, not promoted into spec.md. |
| CHK017 | Fixed | Added an Assumptions bullet: the name lists are tool-authored placeholder data (generic English-language given/family names, no real individuals or licensing constraints), closing the "who curates this" gap. |
| CHK018 | Fixed | Assumptions bullet now states this was verified by inspection (all four current careers — Navy, Marine, Aerospace, Scout — have non-empty titles at every rank) and explicitly flags that this is a data-authoring convention, **not** enforced by `Career.__post_init__` — a future career could violate it silently. |

### Out-of-scope observation (not fixed here)

While investigating CHK018, a wording inconsistency surfaced that belongs to **output-format
grammar**, not name-generation (the focus this checklist was scoped to): FR-003 states rank title
"MUST" prefix the name unconditionally, while User Story 2's acceptance scenario says "rank title
**(if any)**" and the contract (`ucf-output.md`) grammar treats `rank_title` as optional
(`[rank_title " "]`). Given every current career always has a rank title, this never manifests
today, but the spec text itself is inconsistent about whether the omission case is reachable.
Recommend covering this in a future `output-format`/grammar-focused checklist rather than folding
it into this one.

## Notes

- Scope: this checklist deliberately covers only the name-generation/data-source dimension of the
  feature (per author selection); output-grammar, regression-safety, and broader edge-case
  dimensions are out of scope for this file and could be captured in a separate checklist if
  needed.
- Check items off as completed: `[x]`
- Add findings inline under the relevant item if a gap is confirmed
