# Psionics Eligibility Gate

**Date:** 2026-07-09
**Status:** Approved, ready for implementation planning

## Context

Psionics shipped as part of character generation (see
`2026-07-09-psionics-character-generation-design.md`): every character rolls
`Psi = 2D6 − terms_served` (floored at 0), is psionic when `Psi ≥ 1`, and — when
psionic — attempts to learn the five talents.

Testing that feature in generation surfaced a problem: **almost every character
comes out psionic.** Because 2D6 has a minimum of 2, the term penalty rarely
floors young characters to 0:

- **0 terms → 100% psionic** (Psi is always ≥ 2)
- **1 term → 100% psionic** (minimum roll of 2 yields Psi 1)
- **2 terms → ~97%**, decaying only slowly at higher terms

This makes psionics the norm rather than the exception, which is both
unrealistic and drains the characteristic of meaning.

## Decision

Add a **flat eligibility prerequisite** in front of the existing Psi roll: a
character must first pass an unmodified `2D6 ≥ 8` check to be tested for
psionics at all. On failure, the character is not psionic — Psi 0, no talents.
On success, the existing mechanics run unchanged: `Psi = 2D6 − terms_served`
(floored at 0), viability at `Psi ≥ 1`, then talent training.

A flat `2D6 ≥ 8` gate passes ~42% (15/36) of characters, so roughly 58% are
excluded before Psi is ever rolled. Among the ~42% that pass, the term penalty
still floors some to Psi 0, so the two thinnings compound and psionics becomes a
genuine minority outcome.

### On SRD fidelity

This prerequisite is **not in the SRD's psionics chapter**, which tests Psi for
every character. It is a deliberate `cetools` house rule. It is defensible as
*implementing the SRD's intent* rather than contradicting it: in Cepheus /
Traveller, psionics testing was never automatic — a character had to seek out a
Psionics Institute, and referees gated access heavily. The flat check models
"did this character ever get the opportunity to be tested and awaken." The house
rule is recorded here so the departure is intentional and documented.

## Design (Approach A: gate inside `roll_psionics`)

The gate lives inside `roll_psionics`, keeping the psionics module the single
source of truth for "is this character psionic." The generator call site and the
`Character` model are **unchanged** — a failed gate returns `(0, {})`, which is
shape-identical to the existing floored-at-0 path.

`src/cetools/engine/psionics.py`:

- A module constant records the gate target, e.g. `_ELIGIBILITY_TARGET = 8`.
- `roll_psionics` first rolls the prerequisite: `roller.roll(6, count=2)`.
  - If the result `< _ELIGIBILITY_TARGET`, return `(0, {})` immediately —
    **no Psi roll, no talent rolls**.
  - Otherwise proceed exactly as today: roll `Psi = 2D6 − terms_served` (floored
    at 0), and if `Psi ≥ 1`, attempt the ordered talents.

Roll sequence within the function becomes: **gate roll → Psi roll → talent
rolls**. The gate roll is now the first draw the function consumes.

The docstring is updated to state the prerequisite and that a failed gate yields
Psi 0 with no talents.

Nothing else changes: `characteristic_modifier`, the talent table, the
cumulative-penalty loop, the `models.py` fields, `generator.py` wiring, and
`formatter.py` output all stay as they are. A gate failure renders exactly like
any other non-psionic (`Psi 0`) character — bare UPP, no `Psionics:` line.

## Testing

`tests/test_psionics.py`:

- **Gate failure short-circuits:** a gate roll `< 8` returns `(0, {})` and
  consumes **only** the gate draw — prove via a `SequenceRoller` whose
  subsequent high values (which would otherwise produce a large Psi and talents)
  are never consumed.
- **Gate success proceeds:** a gate roll `≥ 8` followed by the existing Psi and
  talent draws reproduces the current behavior (Psi formula, viability, talent
  order, cumulative penalty, level-0 grants).
- **Boundary:** a gate roll of exactly 8 passes; a gate roll of 7 fails.
- Existing `roll_psionics` tests are updated to **prepend a passing gate roll**
  (e.g. 8) to their `SequenceRoller` sequences, since the gate is now the first
  draw.

`tests/test_generator.py`:

- Fixed-roller full-output cases are updated for the new leading psionics draw
  (the gate roll precedes the Psi roll in the tail).
- Keep a case asserting a gate-failed character carries `psi_strength == 0` and
  empty `talents`, and a case (gate passing) asserting a psionic character's
  `psi_strength`/`talents` are consistent with the tail draws.
- The existing "mishap-ended character still rolls psionics" case still holds —
  the gate roll happens regardless of how the career ended.

Coverage stays ≥85% on `src/cetools` (enforced by the suite).

## Out of scope

- Any DM on the eligibility check — it is deliberately flat and unmodified.
- Changes to the Psi formula, viability threshold, talent table, or output
  format — only the prerequisite is added.
- A CLI flag to toggle the gate; the house rule is universal, matching the
  existing "testing is universal" stance.
