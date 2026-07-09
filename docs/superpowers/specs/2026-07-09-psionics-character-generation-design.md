# Psionics in Character Generation

**Date:** 2026-07-09
**Status:** Approved, ready for implementation planning

## Context

The character-generation module is otherwise complete: all 24 SRD careers, the
survival-mishap system, mustering-out, and the UPP/skill/benefit output are
shipped. This adds the **generation-relevant slice of SRD Book 1, Chapter 3:
Psionics** — the seventh characteristic (**Psi**) and the five psionic talents.

This is a **feature added to the existing character module**, not a new module.
The scope is deliberately narrow: roll Psi for every character, and — when Psi
is viable — attempt to learn talents. All play-time psionics mechanics
(activation checks, range costs, point recovery) are **out of scope**; they are
referee concerns, not character-generation output.

Rules are transcribed from the canonical Cepheus Engine SRD, cross-checked
against the raw HTML of both
`https://evolvedexperiment.github.io/cepheus-srd/psionics.html` and the
character-creation UPP section
(`.../character-creation.html#the-universal-persona-profile-upp`).

## Rules (the whole in-scope slice)

**Psi Strength.** Rolled **after** the career runs, because it depends on terms
served (Psi erodes over a career):

```
Psi = 2D6 − terms_served     (floored at 0)
```

Psi is rolled for **every** character — the "always test" decision — including
characters whose career ended in a mishap. There is no CLI flag; testing is
universal.

**Viability.** A character is psionic when **Psi ≥ 1**. Only viable characters
attempt talent training. Non-viable characters (`Psi 0`) simply carry no talents
and render exactly as they do today.

**Talent training.** A viable character attempts all five talents. The SRD's
training cost (Cr100,000) and time (four months) are **abstracted away** — cash
and age are untouched. Each talent is attempted as a check:

```
2D6 + PsiDM + talentDM − (previous attempts) ≥ 8
```

- `PsiDM` is the standard characteristic modifier of the Psi score, reusing
  `models.characteristic_modifier`.
- `talentDM` comes from the Learning-DM table below.
- The `− (previous attempts)` term is the SRD's cumulative "−1 DM per check
  attempted": the 1st attempt subtracts 0, the 2nd subtracts 1, … the 5th
  subtracts 4.

Talents are attempted in **highest-DM-first order** (the rational play, which
maximizes successes given the cumulative penalty):

| Order | Talent        | Learn DM |
|-------|---------------|----------|
| 1     | Telepathy     | +4       |
| 2     | Clairvoyance  | +3       |
| 3     | Telekinesis   | +2       |
| 4     | Awareness     | +1       |
| 5     | Teleportation | +0       |

Each success grants that talent at **level 0**.

## New module: `src/cetools/engine/psionics.py`

A single pure function, roller-injected for deterministic tests (matching the
`DiceRoller` convention used throughout the engine):

```python
def roll_psionics(
    terms_served: int,
    characteristics: dict[str, int],
    roller: DiceRoller,
) -> tuple[int, dict[str, int]]:
    """Return (psi_strength, talents).

    psi_strength = max(0, 2D6 − terms_served).
    talents maps learned talent name → 0, empty when psi_strength < 1.
    """
```

- Rolls Psi via `roller.roll(6, count=2) - terms_served`, floored at 0.
- If Psi < 1, returns `(psi, {})` with no talent rolls.
- Otherwise iterates the ordered talent table, rolling
  `roller.roll(6, count=2) + characteristic_modifier(psi) + talent_dm - attempt_index`
  and recording talents that reach 8, where `attempt_index` is the 0-based
  position in the loop.

The ordered `(name, learn_dm)` talent table lives here as a module constant.

## Data model (`models.py`)

`Character` gains two fields, both with safe defaults so existing construction
sites and tests keep working:

```python
psi_strength: int = 0
talents: dict[str, int] = field(default_factory=dict)
```

`Character.upp` **remains the bare six-character UPP** (`encode_upp` is
unchanged). The Psi suffix is a presentation concern, decided by the formatter.

## Generator wiring (`generator.py`)

In both `generate_career_character` and `draft_character` (they share the same
tail), after `name = generate_name(roller)` and before constructing the
`Character`:

```python
psi_strength, talents = roll_psionics(terms_served, characteristics, roller)
```

and pass `psi_strength=psi_strength, talents=talents` into `Character(...)`.
The psi rolls are the **last** roller draws in the sequence, so they do not
shift any earlier draw and existing fixed-roller expectations for pre-psi state
(characteristics, skills, benefits, name) are unaffected — only the tail output
grows.

## Output format (`formatter.py`)

**UPP suffix.** Per the SRD, the `-N` suffix appears **only for psionic
characters**. `format_character` builds the displayed UPP as:

```python
upp_display = character.upp
if character.psi_strength >= 1:
    upp_display += f"-{to_pseudohex(character.psi_strength)}"
```

Psi is rendered in pseudo-hex like every other characteristic (a Psi of 10 → `A`;
with the term penalty it is almost always a single digit, but it routes through
`to_pseudohex` for correctness). `line1` uses `upp_display` in place of
`character.upp`.

**Psionics line.** When `character.talents` is non-empty, a `Psionics:` line is
inserted **after the skills line and before the material-benefits line**,
talents alphabetical to match the skill-line convention:

```python
talent_parts = [f"{name}-{level}" for name, level in sorted(character.talents.items())]
# "Psionics: " + ", ".join(talent_parts)
```

Line order becomes: name/UPP/age · career/cash · skills · **Psionics (optional)**
· materials (optional) · mishap (optional).

### Worked output

Psionic character:

```text
Starman Sam Voss	5A3B93-6	Age 38
Navy (5 terms)	Cr52,000
Admin-0, Advocate-1, Comms-0, Engineering-1, Melee Combat-2, Tactics-1, Vehicle-2, Zero-G-1
Psionics: Awareness-0, Telepathy-0
+1 Edu, High Passage
```

Non-psionic character (`Psi 0`) — unchanged from today, no suffix, no Psionics
line:

```text
Trooper Casey Voss	481749	Age 20
Marine (0 terms)	Cr0
Admin-0, Advocate-0, Battle Dress-0, Comms-0, Demolitions-0, Gun Combat-0, Zero-G-1
```

## Testing

New `tests/test_psionics.py` covers `roll_psionics` with fixed rollers:

- **Psi formula:** `2D6 − terms_served`, including the floor at 0 (high terms →
  `Psi 0`, empty talents, no rolls attempted).
- **Viability gate:** Psi 0 attempts no talent checks; Psi ≥ 1 attempts all five.
- **Cumulative penalty & order:** with a controlled roller, assert talents are
  attempted Telepathy→…→Teleportation and that the `− attempt_index` penalty is
  applied (e.g. a roll that would pass at attempt 1 but fail at attempt 5).
- **Level-0 grants:** learned talents map to level 0.

Formatter tests (`tests/test_formatter.py`):

- Psionic character renders the `-N` pseudo-hex UPP suffix and the alphabetical
  `Psionics:` line in the correct position.
- Non-psionic character renders the bare UPP and **no** `Psionics:` line.
- A Psi ≥ 10 case renders the pseudo-hex letter suffix.

Generator tests (`tests/test_generator.py`): existing full-output assertions are
updated for the new tail; add a fixed-roller case asserting a generated
character carries `psi_strength`/`talents` consistent with the tail draws, and a
case confirming a mishap-ended character still rolls Psi.

Coverage stays ≥85% on `src/cetools` (enforced by the suite).

## Out of scope

- All play-time psionics: activation checks, Psionic Range costs, point
  expenditure, and the one-point-per-hour recovery rule.
- The Cr100,000 / four-month training cost and time — abstracted away; cash and
  age are never touched by psionics.
- Any CLI flag or option; testing is universal and needs no new surface.
- Alien traits that modify psionics (Psionic / Anti-Psionic / Esper). Character
  generation is human-only today; these are a separate future concern.
- Talent advancement beyond level 0 (a career/skills mechanic, not generation).
