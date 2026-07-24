# Ship Design Requirements Quality Checklist: Starship Generator

**Purpose**: Validate the *quality* of the ship-design requirements (SRD fidelity, determinism &
round-trip, validation & constraints, interface & sheet output) before `/speckit-tasks`. Each item
tests whether the requirements are complete, clear, consistent, and measurable — not whether any
implementation works.
**Created**: 2026-07-23
**Feature**: [spec.md](../spec.md)
**Depth**: Standard reviewer gate (PR/plan reviewer, pre-implementation)
**Reviewed**: 2026-07-23 — 37/37 pass. Evaluated against spec.md, plan.md, research.md,
data-model.md, and contracts/. The 7 originally-flagged items were resolved by spec.md edits
(see Findings, marked RESOLVED).

## Requirement Completeness — SRD Rules Fidelity

- [x] CHK001 Are all SRD hull-table attributes required as inputs/outputs (tons, code, base cost, config modifier, build time, derived hardpoints, hull/structure points)? [Completeness, Spec §FR-003, §FR-014, §Key Entities]
- [x] CHK002 Is drive-rating derivation specified for jump, maneuver, and power plant (rating obtained from hull size + drive code, not caller-supplied)? [Completeness, §FR-004]
- [x] CHK003 Is the full set of addable components enumerated (armor types + reflec/self-sealing/stealth options, electronics, staterooms/low/emergency-low berths, the fittings list, turrets/weapons/ammunition, bays, screens)? [Completeness, §FR-008–§FR-010, §FR-020]
- [x] CHK004 Are trigger conditions specified for every crew role (pilot, engineer scaling by drive+plant tonnage, gunners, navigator, medic, steward by passenger count)? [Completeness, §FR-012, §Edge Cases]
- [x] CHK005 Are computer/software requirements complete (model, jump-control and hardened options, software constrained to the computer's rating)? [Completeness, §FR-007]

## Requirement Clarity — Formulas, Rounding & Terms

- [x] CHK006 Is "derives each drive's performance rating from the hull size" backed by a stated table/formula rather than left descriptive? [Clarity, §FR-004] — backed by research Part C2 matrix.
- [x] CHK007 Are rounding rules stated with direction and precision for hull points (÷50 down), structure points (÷50 up), and small-craft fuel (0.1 ton)? [Clarity, §FR-008, §Edge Cases]
- [x] CHK008 Is the jump-fuel formula (0.1 × hull × jump distance) and the assumed jump range when unstated (full jump rating) each defined unambiguously? [Clarity, §FR-006, §Assumptions]
- [x] CHK009 Is the power-plant fuel rule quantified (from power-plant tonnage × stated weeks, two-week starship / one-week small-craft minimum) rather than described? [Clarity, §FR-006, §FR-019] — exact ⌊tons÷3⌋/week factor is in research Part D, not FR-006 itself (acceptable; note below).
- [x] CHK010 Are the armor increment rules precise enough to act on (5% steps, 1-ton-per-5% floor, and whether off-increment armor is normalized or rejected)? [Clarity, §FR-008, §Edge Cases] — RESOLVED (Finding 1): §Edge Cases now states off-increment armor is rejected (not normalized).
- [x] CHK011 Is the small-craft "energy-weapon limits by power plant" restriction quantified rather than described qualitatively? [Ambiguity, §FR-019] — quantified in research Part K (sA–sF:0 … sS–sZ:3).

## Requirement Consistency

- [x] CHK012 Do the starship required-system rule (jump drive mandatory) and the small-craft rule (no jump drive permitted) stay consistent without contradiction? [Consistency, §FR-005, §FR-019]
- [x] CHK013 Is the 10% standard-design discount described consistently across FR-013, the edge-case list, and acceptance scenario US1-5? [Consistency, §FR-013, §Edge Cases] — RESOLVED (Finding 2): FR-013 and §Edge Cases now state the discount excludes fuel and ammunition, matching research Part J.
- [x] CHK014 Does the ship-sheet content list match the exact set of outputs the builder is required to compute (tonnage/cargo, crew, fuel, hull/structure points, cost, build time)? [Consistency, §FR-011–§FR-014, §FR-022]
- [x] CHK015 Are the builder and the random generator required to share the same tables and validation so no rule can diverge between them? [Consistency, §FR-016]

## Acceptance Criteria Quality — Measurability

- [x] CHK016 Are the ≥3 hand-worked SRD reference designs (SC-002) specified concretely enough to serve as golden values (which designs, which figures compared)? [Measurability, SC-002] — RESOLVED (Finding 3): SC-002 now requires each of the three designs to be captured as a golden fixture with its full component list and expected figures during implementation.
- [x] CHK017 Is "effectively instant, well under one second" backed by a concrete, testable threshold? [Measurability, SC-007]
- [x] CHK018 Is "byte-identical ship sheets across runs" objectively verifiable (no un-pinned non-determinism in rendering)? [Measurability, SC-004] — render_sheet is total/deterministic, no timestamps (engine-api).
- [x] CHK019 Is "lossless round-trip" defined by an objective comparison (design-in equals design-out, or sheet equals sheet)? [Measurability, SC-008] — research Part M defines both equalities.
- [x] CHK020 Is "100% of generated ships pass validation" (SC-003) tied to the builder's own validation as the pass/fail oracle? [Measurability, SC-003, §FR-016]

## Scenario Coverage — Validation & Constraints

- [x] CHK021 Are rejection requirements defined for every named constraint (over-allocation, drive/plant mismatch, hardpoint limit, missing required system, armament disallowed for the hull class)? [Coverage, §FR-015] — data-model adds drive-on-hull, software-over-rating, armor-increment, energy-cap.
- [x] CHK022 Is the required error *content* specified (name the specific violated rule) for each rejection, not merely "invalid"? [Clarity, §FR-015, SC-005] — data-model gives per-rule message shapes.
- [x] CHK023 Are requirements defined for a design that violates multiple constraints at once (which violation is reported, or all)? [Coverage, Gap] — RESOLVED (Finding 4): FR-015 now states the first violation in SRD build order is reported.
- [x] CHK024 Is the zero-remaining-tonnage (zero cargo) case explicitly required to be accepted as valid? [Edge Case, §Edge Cases]
- [x] CHK025 Are the powered-craft-without-power-plant and starship-without-jump-drive cases required to be rejected, distinct from over-allocation? [Coverage, §FR-005, §Edge Cases] — distinct messages in data-model.
- [x] CHK026 Is bay-weapon rejection on small craft, and the minimum hull size for bays, specified as a checkable rule? [Coverage, §FR-020, US4-3] — RESOLVED (Finding 5): FR-020 now states "too small" is enforced by the hardpoint (1 per 100 tons) and tonnage limits, not a separate minimum-hull rule.

## Scenario Coverage — Determinism & Round-trip

- [x] CHK027 Is reproducibility tied to the project's existing reproducible-chance seam so "same seed → same ship" is objectively testable? [Coverage, §FR-017, SC-004] — Rolls / RandomRolls.seeded (research Part L).
- [x] CHK028 Is the no-seed behavior specified precisely enough to reproduce the result (the seed used MUST be reported)? [Completeness, §FR-017] — reported to stderr (cli.md).
- [x] CHK029 Is the design-schema expressiveness obligation stated verifiably (the schema MUST represent ANY ship the generator can produce)? [Measurability, §FR-023, SC-008]
- [x] CHK030 Are malformed / schema-invalid TOML error requirements specified (what makes a file invalid and that a clear error is reported)? [Completeness, §FR-021] — design-schema "Rules enforced at load" enumerates them.

## Scenario Coverage — Interface & Sheet Output

- [x] CHK031 Are the small-craft ship-sheet differences (cockpit rather than bridge line, no jump-fuel line) specified for *output*, not only for construction? [Coverage, Gap, §FR-019, §FR-022] — RESOLVED (Finding 6): FR-022 now states the small-craft sheet shows a cockpit line in place of the bridge and no jump/jump-fuel line.
- [x] CHK032 Is the TOML-emission trigger ("on request") defined by a concrete option/behavior rather than left open? [Clarity, §FR-022] — `--toml` / `--out` flags (cli.md).
- [x] CHK033 Are success-vs-failure output-channel and exit-code requirements stated for the CLI (stdout vs stderr, exit 0/1)? [Completeness, Gap] — cli.md error table + Constitution III (not in spec FRs, but fully specified in the contract).

## Dependencies, Assumptions & Boundaries

- [x] CHK034 Is the "no new runtime dependency" constraint stated as a checkable requirement (read via stdlib `tomllib`; emission dependency-free)? [Consistency, §FR-021, §Assumptions]
- [x] CHK035 Are the referee-discretion omissions (crew roles beyond the minimum, mission-specific fittings) enumerated as documented out-of-automated-scope rather than invented? [Assumption, §FR-002] — plan Constitution Check + research Part I.
- [x] CHK036 Are the out-of-scope boundaries (alternative drives/power plants, named catalog, deck plans/combat) unambiguous enough to prevent scope creep into requirements? [Boundary, §Out of Scope]
- [x] CHK037 Is the spec-level ambiguity flagged for minimum-crew composition resolved and traceable from the spec (not only buried in research.md)? [Ambiguity, §FR-012] — RESOLVED (Finding 7): FR-012 now spells out each role, including "a navigator unless the computer carries Jump-Control software."

## Findings (all RESOLVED in spec.md on 2026-07-23)

1. **CHK010 — Armor off-increment disposition.** RESOLVED: §Edge Cases now states off-5% (or
   sub-minimum) armor is rejected as invalid with a message naming the 5% rule; the builder does not
   silently normalize it (matches data-model.md). [Clarity]
2. **CHK013 — Discount scope.** RESOLVED: FR-013 and the §Edge Cases "Standard vs. custom cost" bullet
   now state the 10% discount applies to hull and components but never to fuel or ammunition, matching
   research Part J. [Consistency]
3. **CHK016 — Reference designs.** RESOLVED (spec) / DEFERRED (fixtures): SC-002 now requires each of
   the three designs to be captured as a golden fixture with its full component list and expected
   figures. The concrete numbers are produced during `/speckit-tasks` as test data. [Measurability]
4. **CHK023 — Multi-violation reporting.** RESOLVED: FR-015 now states that when a design violates
   more than one constraint, the first violation in SRD build order is reported. [Coverage]
5. **CHK026 — "Hull too small for a bay."** RESOLVED: FR-020 now states this is enforced by the
   hardpoint (1 per 100 tons) and tonnage limits rather than a separate minimum-hull rule, reconciling
   the US4 Independent Test wording. [Coverage]
6. **CHK031 — Small-craft sheet output.** RESOLVED: FR-022 now states the small-craft sheet shows a
   cockpit line in place of the bridge and no jump drive / jump-fuel line. [Coverage]
7. **CHK037 — Navigator resolution traceability.** RESOLVED: FR-012 now enumerates each crew role,
   including "a navigator unless the computer carries Jump-Control software," surfacing the research
   Part I resolution in the spec itself. [Ambiguity]

## Notes

- Check items off as completed: `[x]`
- Each item tests the *requirements*, not the implementation — a passing item means the requirement is well-written, not that code works.
- All 37 items now pass. The spec edits above are prose-only clarifications, consistent with
  research.md, data-model.md, and the contracts; no requirement was added or removed in substance.
  Finding 3's concrete golden figures remain to be produced as test fixtures during `/speckit-tasks`.
