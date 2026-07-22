# SRD-Fidelity Checklist: World Generation

**Purpose**: Requirements-quality review gate — validate that the World Generation requirements are complete, unambiguous, consistent, and measurable across SRD rule fidelity, edge cases/dependencies, determinism/seams, and naming/subsector. These items test the *requirements*, not the implementation.
**Created**: 2026-07-15
**Feature**: [spec.md](../spec.md)

**Cross-check status (2026-07-15)**: All 33 items reviewed against spec.md, research.md (incl. Appendix C), data-model.md, and contracts/. **All 33 resolved** — the five spec-measurability/completeness gaps were fixed in spec.md/research.md on 2026-07-15 (see per-item notes).

## SRD Rule Fidelity — Completeness

- [x] CHK001 Are the specific Hydrographics size/atmosphere DM values enumerated, rather than referenced only as "the SRD size/atmosphere modifiers"? [Completeness, Spec §FR-003] → **Resolved**: research §3 enumerates Atmo 0/1/A/B/C −4, Atmo E −2, Size 0/1 → 0, clamp 0–10 (`HYDRO_DM_BY_ATMOSPHERE`).
- [x] CHK002 Are the specific Population size/atmosphere/hydrographics DM values enumerated, rather than referenced only as "the SRD ... modifiers"? [Completeness, Spec §FR-004] → **Resolved**: research §4 enumerates Size≤2 −1, Atmo≥A −2, Atmo 6 +3, Atmo 5/8 +1, Hydro 0 & Atmo<3 −2.
- [x] CHK003 Are the individual Technology-Level DMs for each of Starport, Size, Atmosphere, Hydrographics, Population, and Government specified with concrete values? [Completeness, Spec §FR-008] → **Resolved**: full matrix transcribed verbatim in research Appendix C1 (transcription also corrected a missing Hydrographics-0 +1 entry in the §8 summary).
- [x] CHK004 Are the exact conditions that mandate a minimum Technology Level, and each mandated minimum value, enumerated rather than described only as "SRD-mandated minimum"? [Gap, Spec §FR-009] → **Resolved**: research §8 / Appendix C2 lists all four minimum overrides (Hydro 0/A & Pop≥6 → 4; Atmo 4/7/9 → 5; Atmo ≤3 or A–C → 7; Atmo D/E & Hydro A → 7).
- [x] CHK005 Is the full 2D6-to-class Primary Starport table documented in a reviewable location (spec or data-model)? [Completeness, Spec §FR-007] → **Resolved**: research §7 gives the full 2→11+ table plus the ≤2→X / ≥11→A clamp.
- [x] CHK006 Is the complete trade-classification table (each trade code's UWP match ranges) documented as a reference, rather than pointing at "the SRD trade-classification table"? [Completeness, Spec §FR-015] → **Resolved**: all 18 codes' per-field conditions transcribed verbatim in research Appendix C3 (unblocks SC-003 reference-set verification).
- [x] CHK007 Are the scout-base starport DMs and the naval/scout/pirate presence thresholds specified with concrete dice values? [Completeness, Spec §FR-014] → **Resolved**: research §12 gives Naval 2D6≥8 (starport A/B), Scout 2D6≥7 with DM −1(C)/−2(B)/−3(A) (not E/X), Pirate 2D6≥12 (not A, no naval base).

## SRD Rule Fidelity — Clarity & Measurability

- [x] CHK008 Are the atmosphere codes that trigger Hydrographics suppression, and the suppression DM amounts, explicitly specified? [Clarity, Spec §FR-003] → **Resolved**: research §3 — Atmo 0/1/A/B/C → −4, Atmo E → −2; Size 0/1 forces Hydro 0.
- [x] CHK009 Is the pseudo-hexadecimal letter mapping specified across each characteristic's full range (e.g. Atmosphere/Government up to 15 → F)? [Clarity, Spec §FR-010] → **Resolved**: research/data-model D5 delegates to the existing `pseudohex` codec (valid 0–33, covering all UWP values incl. 15→F); starport is a literal letter.
- [x] CHK010 Is the head-count derivation (Population Modifier × 10^Population) stated precisely enough to be objectively verified? [Measurability, Spec §FR-011] → **Resolved**: data-model `head_count → population_modifier * 10**population` (0 when population 0); research §9.
- [x] CHK011 Are the SRD probability bounds in SC-004 (e.g. gas-giant ≈72%) given with an explicit tolerance band so the statistical check is objectively pass/fail? [Measurability, Spec §SC-004] → **Fixed**: SC-004 now specifies ±2 pp over ≥10,000 systems and lists the SRD-derived probabilities; also corrected the gas-giant example from ≈72% to ≈83% (5+ on 2D6 = 30/36).

## Edge Cases & Inter-Characteristic Dependencies

- [x] CHK012 Does a functional requirement (not only an acceptance scenario) state that Technology Level is forced to 0 when Population is 0? [Conflict, Spec §FR-008 vs §US1-AC3 / §SC-002] → **Fixed**: FR-009 now states a Population-0 world MUST have TL 0, "overriding the rolled value and any mandated minimum"; research §8 documents the ordering (minimum overrides → Population-0 zeroing) so the minimum-raise can't re-raise an uninhabited world.
- [x] CHK013 Is an Atmosphere floor of 0 specified, given the 2D6−7+Size formula can yield negatives for low Size? [Gap, Spec §FR-002] → **Resolved**: research §2 states "Never below 0"; data-model range 0–15; SC-001 mandates Atmosphere 0–15.
- [x] CHK014 Is a Law Level upper bound specified, or is "minimum of 0" the only clamp? [Gap, Spec §FR-006] → **Resolved**: research §6 explicitly states no ceiling by design (SRD has none; "A+ = Extreme Law"); data-model law_level ≥ 0. Deliberate, documented.
- [x] CHK015 Are the Size-0 dependencies (Atmosphere 0, Hydrographics 0, guaranteed planetoid belt, Asteroid/Vacuum trade code) stated consistently across FRs, edge cases, and success criteria? [Consistency, Spec §FR-002/003/012, Edge Cases] → **Resolved**: consistent across FR-002/003/012, Edge Cases, SC-002, data-model invariants, and Appendix C3 (As: Size0/Atmo0/Hydro0; Va: Atmo0).
- [x] CHK016 Is the resolution order for base determination specified so the pirate-base exclusions (no pirate base with Class-A starport or a naval base) are unambiguous? [Ambiguity, Spec §FR-014] → **Resolved**: research §12 explicitly resolves Naval → Scout → Pirate "in this order because of exclusions" (pirate checks "no naval base").
- [x] CHK017 Are the Amber Zone trigger conditions (Atmosphere 10+, Government 0/7/10, Law Level 0 or 9+) confirmed complete against the SRD, with combination/precedence relative to Red Zone defined? [Coverage, Spec §FR-016] → **Resolved**: research §14 enumerates the triggers; engine-api contract states an explicit RED supersedes rule-driven AMBER.
- [x] CHK018 Are all value ceilings and floors (Size 0–10, Atmo 0–15, Hydro 0–10, Pop 0–10, Gov 0–15, Law ≥0, TL ≥0) stated identically in the FRs and in SC-001? [Consistency, Spec §SC-001] → **Resolved**: FR-001–008 clamps align field-for-field with SC-001 and data-model ranges.
- [x] CHK019 Is the Population-0 case fully specified (Government, Law, TL, and Population Modifier all 0, Barren-type trade codes), and is "may apply" for Barren codes disambiguated into a rule? [Clarity, Edge Cases] → **Resolved**: research §4 (Gov/Law/TL 0), FR-011/data-model (PBG modifier 0); the vague "may apply" is pinned by the deterministic Appendix C3 matcher (Ba: Pop0/Gov0/Law0; Va: Atmo0).
- [x] CHK020 Is Starport-X behavior specified end-to-end (valid minimal profile plus its effect on base and trade outcomes)? [Coverage, Edge Cases] → **Resolved**: starport table §7 (roll ≤2 → X), TL DM Appendix C1 (X −4), base exclusions §12 (no scout/naval; pirate allowed), rendering D5 (literal 'X').

## Determinism & Library/CLI Seams

- [x] CHK021 Is "seed" defined — its type, how the caller supplies it, and its scope (per-world vs per-subsector)? [Clarity, Spec §FR-022] → **Resolved**: cli.md `--seed int`; research D7 / engine-api build `RandomRolls(random.Random(seed))` threaded through the `rolls` seam of one top-level `generate_*` call.
- [x] CHK022 Is a fixed dice-draw order across characteristics specified, so that same-seed reproducibility is deterministic and not implementation-dependent? [Gap, Spec §FR-022] → **Resolved**: data-model "Generation order (dependencies)" fixes the full draw order (size→…→travel_zone, then system, then subsector); matches research Part A.
- [x] CHK023 Is the interaction between name-collision regeneration and seeded reproducibility specified, so regeneration does not make subsector output non-reproducible? [Consistency, Spec §FR-027 vs §FR-022] → **Resolved (by design)**: all chance flows through the single `Rolls` seam (research D2), so collision-regeneration draws are part of the same deterministic sequence; engine-api guarantees "identical rolls state ⇒ identical World/Subsector".
- [x] CHK024 Is the library/CLI boundary stated measurably — what the CLI subcommand does (I/O only) versus what the engine library owns? [Clarity, Spec §FR-023/FR-024] → **Resolved**: cli.md — "Pure I/O routing: parse args → call `cetools.engine.worlds` → write stdout. No game logic"; engine-api defines the library surface (Principles II/III).
- [x] CHK025 Is the allegiance value's allowed format/domain specified beyond the default `Na`? [Completeness, Spec §FR-017] → **Resolved**: data-model/contracts specify a caller-supplied `str` defaulting to `"Na"`; intentionally unconstrained (allegiance is referee-discretion per Assumptions).

## Naming & Subsector

- [x] CHK026 Is name-generation "variety" quantified (e.g. minimum distinct name combinations), rather than described as "does not visibly repeat"? [Measurability, Spec §FR-026] → **Fixed**: FR-026 now requires the generator "be capable of producing at least 10,000 distinct names" — a measurable floor (enumerable from the generator's output space) atop the SC-008 uniqueness guarantee.
- [x] CHK027 Is it specified whether caller-supplied override names participate in the subsector uniqueness check? [Gap, Spec §FR-025/FR-027] → **Resolved**: research D4 — an overridden `name` is used verbatim and "does not participate in uniqueness regeneration" (and `generate_subsector` auto-generates all names anyway).
- [x] CHK028 Is a termination guarantee or retry bound specified for collision-regeneration when the stem pool is small relative to subsector size? [Edge Case, Spec §FR-027] → **Resolved**: research D4 max-attempts guard (mirrors `_MAX_QUALIFICATION_ATTEMPTS`); engine-api raises `ValueError` after bounded attempts rather than looping.
- [x] CHK029 Is the per-hex world-presence dice mechanic specified (what roll the 50% and the rift/sparse/dense modifiers apply to)? [Ambiguity, Spec §FR-019/FR-020] → **Resolved**: research §15 / engine-api — present iff `1D6 + density.dm ≥ 4` (rift −2, sparse −1, standard 0 ≈50%, dense +1).
- [x] CHK030 Is the recorded hex-coordinate format (column-then-row, e.g. `0101`) specified? [Completeness, Spec §FR-021] → **Resolved**: research §15, data-model, and both contracts specify `"CCRR"` (2-digit column, 2-digit row; columns 01–08, rows 01–10).
- [x] CHK031 Are the density-shift expectations in SC-007 quantified with a tolerance, so "approximately 50%" and "measurably up/down" are objectively verifiable? [Measurability, Spec §SC-007] → **Fixed**: SC-007 now specifies ±2 pp over ≥10,000 hexes per density with the SRD-derived shares (rift ≈17%, sparse ≈33%, standard ≈50%, dense ≈67%) and their 1D6 thresholds.

## Traceability & Assumptions

- [x] CHK032 Are the referee-discretion exclusions (Red Zone, polity boundaries, trade/comm routes, map drawing) stated as accept-as-input requirements rather than left implicit? [Assumption, Spec §Assumptions] → **Resolved**: the Assumptions section explicitly scopes these as referee-set — accepted as inputs where modeled (`travel_zone_red`, `allegiance`), out of scope otherwise (routes, maps).
- [x] CHK033 Is the SC-003 hand-worked reference set (worlds covering every trade classification) identified or defined so trade-code fidelity is traceable? [Traceability, Spec §SC-003] → **Fixed**: SC-003 now names a reference fixture requiring at least one world per classification (all 18 codes listed) plus a multi-code and a no-code world, traced to research Appendix C3.

## Notes

- Check items off as reviewed: `[x]`
- **All 33 resolved.** The five spec-side gaps were fixed on 2026-07-15:
  - **CHK011, CHK031** — SC-004 and SC-007 now carry explicit ±2 pp tolerance bands, ≥10,000-sample sizes, and SRD-derived probabilities (SC-004's gas-giant example was also corrected 72% → 83%).
  - **CHK012** — FR-009 now states TL 0 for Population-0 worlds, overriding any minimum; research §8 pins the ordering.
  - **CHK026** — FR-026 now requires ≥10,000 distinct possible names (measurable floor).
  - **CHK033** — SC-003 now names a per-classification reference fixture traced to Appendix C3.
