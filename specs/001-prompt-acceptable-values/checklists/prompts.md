# Prompt Surface Requirements Checklist: Acceptable Values at Interactive Ship Prompts

**Purpose**: Formal pre-implementation gate on the *quality* of the requirements governing the
interactive prompt surface—prompt text and spelling, conditional narrowing, input acceptance and
refusals, and the new armour-options capability—including agreement between `spec.md`, `plan.md`
and the two contracts. Every item below interrogates what the requirements say, not whether code
works.

**Created**: 2026-07-29

**Worked through**: 2026-07-29. All 44 items resolved; the resulting amendments are recorded in
`spec.md`'s "Session 2026-07-29 (checklist review)" clarifications and in FR-023 and FR-024.

**Feature**: [spec.md](../spec.md)

**Depth**: formal gate. Each item must be resolved in the spec (or explicitly waived with a
reason recorded here) before `/speckit-tasks` and implementation proceed.

**Companion**: [requirements.md](./requirements.md) covers generic specification quality. This
checklist covers the four domains this feature turns on.

## Requirement Completeness

- [x] CHK001 Is the authoritative inventory of which questions have a "closed, knowable set" enumerated in the requirements, so SC-001's count of zero has a denominator that does not depend on reading the design? [Completeness, Spec §FR-001, §SC-001]
  → **Gap, closed.** FR-001 now gives the test (keys of a rules table, members of an enumerated type, or a contiguous run of counts derived from one) and names the eighteen questions that meet it. SC-001's denominator is that list.
- [x] CHK002 Is the ordering of values within a displayed list specified—table order, ascending, alphabetical—or is ordering left undefined? [Gap, Spec §FR-002]
  → **Gap, closed.** FR-002 now requires words in rules-table order and numbers ascending, which is what `contracts/engine-accessors.md` already assumed without a requirement to point at.
- [x] CHK003 Are the position and connector wording of `none` within a value list specified, given the sets differ ("or none", ", none", and a leading `none`)? [Gap, Spec §FR-002]
  → **Gap, closed; one artifact corrected.** FR-002 requires `none` last wherever it appears. The turret prompt was the sole violation and is now `Turrets (1-2, none)` in the contract, research Decision 8 and the quickstart. The connector is left to prose.
- [x] CHK004 Are requirements defined for how the free part of a compound answer is described at the prompt—the percent after an armour type, a turret count—or only that it lies outside FR-002's count? [Gap, Spec §FR-002]
  → **Gap, closed.** FR-002 now requires the prompt to state a compound answer's shape. This is what the contract's armour prompt was already doing with "each with a percent" (see CHK037).
- [x] CHK005 Is the notation for a collapsed numeric run specified, including multi-segment runs with differing steps and any element that fits no run? [Clarity, Spec §FR-005]
  → **Gap, closed.** FR-005 now fixes `first-last` and `first-last by step`, comma-separated ascending runs, and enumeration for any value belonging to no run. Lifted from research Decision 2, which held the only statement of it.
- [x] CHK006 Are requirements defined for what a question accepts, and what Enter does, once FR-012's narrowed set is empty—is the question still answerable at all? [Completeness, Spec §FR-012]
  → **Gap, closed by decision.** Enter only; any typed answer is refused with the same reason. Chosen over "accept and let assembly refuse" so the question cannot pin a value it has just called impossible.
- [x] CHK007 Is the set of questions whose acceptable set depends on hull class enumerated, as FR-010 enumerates the tonnage-dependent four? [Completeness, Spec §FR-009]
  → **Gap, closed.** FR-009 now separates hull tonnage (class alone) from the five that depend on class and tonnage together.
- [x] CHK008 Is the answer separator for the multi-value armour-options answer specified—space, comma, or both—as the revise question's separators are? [Gap, Spec §FR-018]
  → **Gap, closed.** FR-018: spaces or commas, any case, as the revise question already accepts.
- [x] CHK009 Are requirements defined for whether a count question accepts the digit `0` alongside `none`, and if it does, whether FR-002 obliges naming it? [Gap, Spec §FR-002]
  → **Confirmed against code, closed.** `_read_staterooms` and `_read_turret_count` both accept `0` today (`ship.py:279`, `ship.py:335`). FR-002 now names `0` an alternate spelling of `none` at a count question, so it is outside the count and not separately named. No code change.
- [x] CHK010 Does the spec state *where* in a prompt a named set must appear—a parenthesised list, or naming inside the question text as the accept/revise question does? [Gap, Spec §FR-001]
  → **Gap, closed.** FR-001's closing paragraph: a parenthesised list between question and Enter label, except where the question text already names every value once.

## Requirement Clarity & Ambiguity

- [x] CHK011 Is "closed, knowable set" defined precisely enough to classify a borderline question without appeal to the implementation? [Ambiguity, Spec §FR-001]
  → **Closed by CHK001's definition.**
- [x] CHK012 Is FR-011's "MUST make clear the set is not narrowed to a chosen hull" quantified with required phrasing or a checkable property? [Clarity, Spec §FR-011]
  → **Clarified.** FR-011 now requires a qualifier naming the *ruleset* rather than a hull, so a prompt carrying none reads as a claim about the hull in hand. That is checkable per prompt.
- [x] CHK013 Can FR-012's "say the hull can take none of the values" be distinguished objectively from "displaying an empty choice"? [Measurability, Spec §FR-012]
  → **Clarified.** FR-012 now requires the prompt to name *no value at all* and to say which hull can take none—two properties a test can assert on the string.
- [x] CHK014 Is "the acceptable values" in a refusal defined as the same set the prompt named, `none` included? [Ambiguity, Spec §FR-016]
  → **Clarified; one artifact corrected.** FR-016 now says same set, same spelling, same order, `none` included. The contract's refusal example omitted `none` and has been fixed (see CHK038).
- [x] CHK015 Does the `--hull` disagreement edge case identify *which* question is then asked with its list—hull class, hull tonnage, or both? [Clarity, Spec §Edge Cases]
  → **Resolved against code.** `ship.py:459-473`: the message is printed, `hull` is cleared, and the *hull tonnage* question is asked. The edge case now says so.
- [x] CHK016 Is FR-022's "user-facing documentation of the interactive session" identified specifically, and are the passages that currently imply refusal-as-discovery named? [Clarity, Spec §FR-022]
  → **Clarified.** FR-022 now names the README's `--interactive` section and the specific claim that must stop serving as the route to the acceptable set.
- [x] CHK017 Is "evenly spaced numeric run" defined for a two-element run, given FR-005 mandates collapsing only at three or more while the turret prompt renders two counts as `1-2`? [Ambiguity, Spec §FR-005, contracts/prompt-contract.md §1]
  → **Real conflict, resolved by decision.** A two-element run collapses when its step is 1, otherwise it is enumerated (`1, 3`, not `1-3 by 2`). FR-005 and research Decision 2 both updated; the contract and quickstart stand as written.

## Requirement Consistency & Conflicts

- [x] CHK018 Do FR-005 and FR-015 conflict? A collapsed range is displayed text that is not itself an acceptable answer, yet FR-015 requires every displayed value to be accepted verbatim. [Conflict, Spec §FR-005, §FR-015]
  → **Real conflict, resolved.** A range is *notation for* values, not a value. FR-002 now lists notation among its exclusions, FR-005 says a range stands for its members, and FR-015 requires each member to be accepted. This was the checklist's highest-value find: as written, SC-002 was undecidable for every numeric prompt.
- [x] CHK019 Does SC-002's "every value displayed at every prompt, typed back verbatim, is accepted" exclude range notation, the floor clause and the Enter default label, or does it count them as displayed values? [Conflict, Spec §SC-002]
  → **Resolved with CHK018.** SC-002 now states its denominator (the set FR-003 publishes) and defers to FR-002's three exclusions; the contract's §7 test definition was tightened to match.
- [x] CHK020 Are FR-002, FR-006 and FR-018 consistent for the armour-options question—does it accept the literal `none`, and if so must it name it despite `none` being the advertised default? [Conflict, Spec §FR-002, §FR-006, §FR-018]
  → **Conflict, resolved by decision.** It accepts `none` and does not name it, for the reason `purpose` does not: the Enter label already says it. FR-018 states this and the contract carries a note marking it the one closed-set list that omits `none`.
- [x] CHK021 Is AS 1.6's "no question names an answer that ruleset cannot take" reconciled with a value the ruleset permits pinning but never rolls, as with small-craft turret mounts? [Conflict, Spec §US1 AS-6]
  → **Clarified.** "Cannot take" now means the ruleset *refuses* it. A value the rules permit pinning but the dice never draw is still named, so all five mounts appear on a small craft—which is what `_read_turret_mount` (`ship.py:312`) does today.
- [x] CHK022 Are FR-012 and FR-013 consistent—must the power-plant floor still be stated when the narrowed set is empty, and does stating a floor beside "can carry none" read as contradictory? [Consistency, Spec §FR-012, §FR-013]
  → **Clarified.** FR-013 now requires the floor in all three narrowing states: a floor the drives require holds whether or not this hull can meet it. The contract's §4 table gained an "Accepts" column making the empty row's Enter-only rule explicit.
- [x] CHK023 Do FR-014's spelling rule and the SRD-fidelity obligation agree on where the hyphenated SRD spelling must still appear? [Consistency, Spec §FR-014]
  → **Clarified.** FR-014 is now scoped to prompts and refusals; ship descriptions keep the SRD's "pop-up turret" and "self-sealing hull". This is what data-model.md already recorded, now stated where the requirement lives.
- [x] CHK024 Is FR-004's list of questions where Enter does something other than roll complete and consistent with the screens-on-a-small-craft edge case and the armour-options default? [Consistency, Spec §FR-004, §Edge Cases]
  → **Real incompleteness, fixed.** The old list named only purpose and a small-craft screen. Against `ship.py` the full set also includes hull class (`[starship]`, line 443), the accept-or-revise question (`[accept]`, line 607), the revise question (`[all]`, line 591) and the new armour-options question (`[none]`). FR-004 now names all six.

## Acceptance Criteria Quality & Measurability

- [x] CHK025 Is SC-005's two-line budget measurable—does the 80-column count include the trailing space, the referee's typed answer on the same line, and are the terminal assumptions it rests on stated? [Measurability, Assumption, Spec §SC-005]
  → **Clarified.** SC-005 now defines a prompt as the string the session writes, trailing space included, excluding whatever the referee types. Research Decision 6's table was re-measured on that basis.
- [x] CHK026 Is SC-003 objectively verifiable, or is "without consulting the SRD, the README, or a refusal" a subjective outcome needing a proxy criterion? [Measurability, Spec §SC-003]
  → **Restated.** SC-003 now leads with the checkable property—every value needed for those seven questions is named at its prompt—and keeps the referee sentence as the reason.
- [x] CHK027 Does SC-006 state how "no edit to the prompt itself" is demonstrated—a specific table mutation and the prompt change it must produce? [Measurability, Spec §SC-006]
  → **Clarified.** SC-006 now names the demonstration, which quickstart Scenario 8 already performs.
- [x] CHK028 Is SC-002's second count—"every distinct value a prompt accepts, the prompt named it"—enumerable from the requirements alone, without reading the reader implementations? [Measurability, Spec §SC-002]
  → **Closed.** The denominator is the set FR-003 publishes for that question, which is exactly what the accessor contract's completeness invariant establishes.
- [x] CHK029 Is SC-001's scope pinned to specific answers, given some prompts appear only on some answer paths (armour options, per-turret questions) and so cannot be counted by an all-Enter walk? [Clarity, Spec §SC-001, §US1 Independent Test]
  → **Real gap, closed.** Three all-Enter questions are unreachable that way. SC-001 now requires a third session that reaches the armour options and each turret's mount and weapon.

## Scenario & Edge Case Coverage

- [x] CHK030 Are requirements defined for armour being revised and the re-asked armour question answered `none`—are previously pinned options dropped, and is that stated? [Gap, Spec §FR-021]
  → **Gap, closed.** FR-021: the options go with the layer they belonged to, since FR-019 leaves no question to carry them. Falls out of research Decision 7's single-field design; now stated rather than implied. Quickstart Scenario 4 gained the case.
- [x] CHK031 Are requirements defined for whitespace tolerance in a multi-word or multi-value answer—leading, trailing, and repeated internal separators? [Gap, Spec §FR-015]
  → **Real gap, closed.** `_ask` strips surrounding whitespace (`ship.py:100`) and the `.split()` readers tolerate internal runs, but a whole-answer reader such as `_read_electronics` would refuse `basic  civilian`. FR-015 now requires an internal run of whitespace to count as one space.
- [x] CHK032 Are requirements defined for a set narrowed by an earlier answer being re-derived after that answer is revised, and for a per-turret sequence where each mount narrows its own weapon set? [Coverage, Gap, Spec §FR-010, §FR-021]
  → **Gap, closed.** FR-010 now requires the set to be derived from the answers standing when the question is asked. Mirrored in data-model.md and the contract's §4.
- [x] CHK033 Are exception-flow requirements complete for the new armour-options question—unrecognised, repeated, and a mix of valid and invalid options in one answer? [Coverage, Spec §FR-018]
  → **Gap, closed.** FR-018 now requires a mixed answer to be refused whole, pinning nothing; a new edge case states the general rule. Quickstart Scenario 4 gained `reflec bogus`.
- [x] CHK034 Are requirements defined for the recovery path when a prompt's narrowed set and the eventual rolled hull disagree, beyond restating that assembly refuses? [Coverage, Spec §Edge Cases]
  → **No change needed.** The existing edge case plus FR-011's qualifier and FR-023 cover it: the answer is accepted, generation may refuse it, and the refusal reaches the existing revise loop. No new requirement earns its place here.

## Non-Functional Requirements

- [x] CHK035 Is the stderr-only requirement stated to cover the new armour-options prompt and every refusal message, not only prompts in general? [Completeness, Spec §FR-008]
  → **Closed.** FR-008 now names refusals explicitly. True in the code already—`_ask_until_understood` echoes with `err=True` (`ship.py:130`)—but unstated.
- [x] CHK036 Does SC-007's seed-parity criterion state that the added question must not alter the roll sequence or draw order on the all-Enter path? [Completeness, Spec §SC-007]
  → **Closed.** SC-007 now states it, and why the armour-options question is not reached on that path: Enter at armour pins nothing for it to attach to.

## Cross-Artifact Agreement

- [x] CHK037 Does the prompt contract's armour prompt, which names that each type takes a percent, trace to a requirement, or does it extend the spec silently? [Traceability, contracts/prompt-contract.md §1, Spec §FR-002]
  → **Silent extension, now traceable.** FR-002's new compound-shape clause is the requirement the contract was already satisfying. Knock-on: research Decision 6 had measured the *old* armour wording at 69 chars; re-measured at 93 (still two lines, so SC-005 holds).
- [x] CHK038 Does the prompt contract's refusal example, which omits `none` from the named set while the prompt names it, agree with FR-016 and FR-002 as written? [Conflict, contracts/prompt-contract.md §6, Spec §FR-016]
  → **Real disagreement, fixed.** The example now ends `…, vault, none`, and §6 states the rule. Left as-is, the prompt and its refusal would have described different sets—the precise failure US3 calls worse than showing nothing.
- [x] CHK039 Does the accessor contract's ordering rule—table order for words, ascending for numbers—trace to a spec requirement, or is ordering an undocumented design choice? [Traceability, contracts/engine-accessors.md, Spec §FR-002]
  → **Now traceable** to FR-002's ordering clause (CHK002). The accessor contract needed no change.
- [x] CHK040 Is the count of sixteen revisable answers consistent across FR-007, SC-005, the prompt contract's list, and the data model's claim that `DesignConstraints` gains no field? [Consistency, Spec §FR-007, data-model.md]
  → **Verified consistent, no change.** `_REVISABLE` is `fields(DesignConstraints)` (`ship.py:568`) and the contract's list is sixteen names. Research Decision 7's reason for keeping options inside the `armor` field is what holds it at sixteen.
- [x] CHK041 Does the contract's three narrowing phrasings cover every state FR-009 to FR-012 require, and is each phrasing traceable to exactly one of them? [Traceability, contracts/prompt-contract.md §4]
  → **Closed.** §4's table now carries an "Accepts" column, the empty row's Enter-only rule, the FR-013 floor note for all three states, and the FR-010 re-derivation rule. Each row cites one requirement.
- [x] CHK042 Is the assumption that the README is the only user-facing documentation needing FR-022's update validated against `CONTRIBUTING.md` and `AGENTS.md`? [Assumption, Spec §Assumptions]
  → **Validated.** `rg -i interactive` finds the session described only in `README.md` (lines 315, 331, 340, 345). Neither `CONTRIBUTING.md` nor `AGENTS.md` mentions it. The assumption now records the check.
- [x] CHK043 Is "assembly remains the sole authority on rules legality" stated as a requirement anywhere, or only as an assumption that FR-002's completeness claim silently depends on? [Assumption, Spec §Assumptions]
  → **Promoted to FR-023.** FR-002's claim that the list is complete is only true given this boundary, so it needed to be a requirement rather than an assumption. The assumption now points at it; plan.md's Constitution Check I cites it.
- [x] CHK044 Is the small craft hangar's exclusion from the fitting question traceable to a requirement, or only to an assumption and one acceptance scenario? [Traceability, Spec §Assumptions, §US1 AS-4]
  → **Promoted to FR-024**, stated as the general rule (no prompt names a value whose acceptance needs an answer the session never asks for) and requiring the exclusion be derived from the rules data, which is what the accessor contract already specified for `fitting_kinds()`.

## Outcome

Fourteen items were genuine defects rather than missing prose, and would have reached
implementation:

1. **CHK018/CHK019**: FR-005 and FR-015 used "value" in two senses, leaving SC-002 undecidable for
   every numeric prompt. The largest find.
2. **CHK024**: FR-004's list of non-roll Enter labels was missing four of six.
3. **CHK038**: the contract's refusal example named a different set than its prompt.
4. **CHK003/CHK017**: the turret prompt contradicted both the `none`-last rule and FR-005's
   threshold.
5. **CHK029**: SC-001 was uncountable by the sessions it named, three questions being unreachable
   by an all-Enter walk.
6. **CHK031**: a whole-answer reader would refuse a doubled internal space in a two-word value.
7. **CHK037**: research Decision 6's length table had been measured against superseded wording.
8. Plus FR-002's own internal conflict, found while amending it: it listed "a turret count" as a
   free part outside the count while FR-010 and AS 2.5 require those counts named.

Two items needed a decision rather than a correction (CHK006 empty-set acceptance, CHK017's
two-element threshold); both are recorded in the spec's clarifications. One item (CHK034) needed no
change. The remainder were requirements that existed only in `research.md` or the contracts and are
now stated where they belong.

**Not verified here**: that the implementation matches any of this. These are requirements tests;
the code has not been written. `contracts/prompt-contract.md` §7 and quickstart Scenarios 1-8 are
what check the build.
