# Social Careers (Batch 1) + Ship Shares Mechanic

**Date:** 2026-07-08
**Status:** Approved, ready for implementation planning

## Context

Batch 1 of the 18-non-draft-career effort (roadmap in
`docs/superpowers/specs/2026-07-08-optional-qualification-careers-design.md`).
It adds the five **Soc-based "Social" careers** — Agent, Bureaucrat,
Diplomat, Entertainer, Noble — following the established data-driven pattern:
each is a frozen `Career` instance in
`src/cetools/engine/careers/<name>.py`, registered in `registry.py`, with a
per-career test file mirroring the existing ones, plus a README update.

These are **non-draft** careers: they go in `CAREER_REGISTRY` (selectable via
`--career`) but **not** in `DRAFT_TABLE` (the draft stays the canonical six).
Names need no de-parenthesizing; registry keys are the lowercased names
(`"agent"`, `"bureaucrat"`, `"diplomat"`, `"entertainer"`, `"noble"`).

One career (Noble) introduces a mustering-out benefit the engine cannot yet
represent — `1D6 Ship Shares`, a *rolled quantity*. So Batch 1 also delivers
a small **ship-shares mechanic**, sequenced as the foundational first work in
the plan, before the career data.

Data below is transcribed verbatim from the SRD character-creation page.

## Ship Shares Mechanic

The engine currently represents every material benefit as a flat display
string; the formatter counts benefit *instances* (`Weapon (x2)`), not
amounts. Ship shares are a rolled quantity that accumulates across rolls, so
they need a real quantity.

### Model (`src/cetools/engine/models.py`)

Add a field to `Benefit`:

```python
material_quantity: int | None = None
```

It defaults to `None` for every existing benefit (cash and flat material
alike); no new validation. `__post_init__` is unchanged.

### Generator (`src/cetools/engine/generator.py`)

- Add a module constant near the other benefit constants:

  ```python
  _SHIP_SHARES_BENEFIT = "1D6 Ship Shares"
  ```

- Noble's material table stores the literal `"1D6 Ship Shares"` in slot 7
  (index 6), reachable only at rank ≥5 (where `material_dm = 1`).

- In `_muster_out`, the material-benefit branch currently does:

  ```python
  name = _roll_material_benefit(career, material_dm, roller, granted_material_names)
  _apply_material_benefit(name, characteristics, skills)
  granted_material_names.add(name)
  benefits.append(Benefit(kind="material", material_name=name))
  ```

  Change it so that when `name == _SHIP_SHARES_BENEFIT`, the generator rolls
  1D6 for the quantity and records a normalized name:

  ```python
  name = _roll_material_benefit(career, material_dm, roller, granted_material_names)
  if name == _SHIP_SHARES_BENEFIT:
      quantity = roller.roll(6)
      benefits.append(
          Benefit(
              kind="material",
              material_name="Ship Shares",
              material_quantity=quantity,
          )
      )
      granted_material_names.add(name)
      continue
  _apply_material_benefit(name, characteristics, skills)
  granted_material_names.add(name)
  benefits.append(Benefit(kind="material", material_name=name))
  ```

  (The exact control-flow shape — `continue` vs. `if/else` — is an
  implementation detail for the plan; the loop body is a `for` loop over
  benefit rolls.) `_apply_material_benefit` is **not** called for ship shares
  (they affect neither characteristics nor skills). `_roll_material_benefit`
  is unchanged — it still returns the raw table string, including the
  `"1D6 Ship Shares"` sentinel.

### Formatter (`src/cetools/formatter.py`)

In `_combine_material_benefits`, add a third bucket alongside boosts and
plain items: material benefits carrying a `material_quantity` accumulate by
name, tracked in first-appearance order like the existing groups. They are
excluded from the plain-item counting (so they never render as
`Ship Shares (x2)`). Render each as `"<total> <name>"`, e.g. two rolls of 3
and 4 → `"7 Ship Shares"`. No pluralization handling: a single share renders
`"1 Ship Shares"` (consistent, if slightly ungrammatical). The returned
ordering becomes: boosts, then singles, then repeats, then quantity items.

## Career Data

Notation: `+1 X` entries are stat boosts. Rank entries show the granted bonus
skill in brackets; ranks with no bracket grant nothing (empty
`bonus_skills`). Cash and material tables are in table order.

### Agent (`agent.py`, key `"agent"`)

- Qualification: Social Standing 6
- Survival: Intelligence 6
- Commission: Education 7
- Advancement: Education 6
- Re-enlistment: 6
- Personal Development: `+1 Dex`, `+1 End`, `+1 Int`, `+1 Edu`, `Athletics`, `Carousing`
- Service Skills: `Admin`, `Computer`, `Streetwise`, `Bribery`, `Leadership`, `Vehicle`
- Specialist Skills: `Gun Combat`, `Melee Combat`, `Bribery`, `Leadership`, `Recon`, `Survival`
- Advanced Education: `Advocate`, `Computer`, `Liaison`, `Linguistics`, `Medicine`, `Leadership`
- Ranks: 0 Agent [`Streetwise`], 1 Special Agent, 2 Sp Agent in Charge, 3 Unit Chief, 4 Section Chief [`Admin`], 5 Assistant Director, 6 Director
- Cash: 1000, 5000, 10000, 10000, 20000, 50000, 50000
- Material: `Low Passage`, `+1 Int`, `Weapon`, `Mid Passage`, `+1 Soc`, `High Passage`, `Explorers' Society`

### Bureaucrat (`bureaucrat.py`, key `"bureaucrat"`)

- Qualification: Social Standing 6
- Survival: Education 4
- Commission: Social Standing 5
- Advancement: Intelligence 8
- Re-enlistment: 5
- Personal Development: `+1 Dex`, `+1 End`, `+1 Int`, `+1 Edu`, `Athletics`, `Carousing`
- Service Skills: `Admin`, `Computer`, `Carousing`, `Bribery`, `Leadership`, `Vehicle`
- Specialist Skills: `Admin`, `Computer`, `Perception`, `Leadership`, `Steward`, `Vehicle`
- Advanced Education: `Advocate`, `Computer`, `Liaison`, `Linguistics`, `Medicine`, `Admin`
- Ranks: 0 Assistant [`Admin`], 1 Clerk, 2 Supervisor, 3 Manager, 4 Chief [`Advocate`], 5 Director, 6 Minister
- Cash: 1000, 5000, 10000, 10000, 20000, 50000, 50000
- Material: `Low Passage`, `+1 Edu`, `+1 Int`, `Mid Passage`, `Mid Passage`, `High Passage`, `+1 Soc`

### Diplomat (`diplomat.py`, key `"diplomat"`)

- Qualification: Social Standing 6
- Survival: Education 5
- Commission: Intelligence 7
- Advancement: Social Standing 7
- Re-enlistment: 5
- Personal Development: `+1 Dex`, `+1 End`, `+1 Int`, `+1 Edu`, `Athletics`, `Carousing`
- Service Skills: `Admin`, `Computer`, `Carousing`, `Bribery`, `Liaison`, `Vehicle`
- Specialist Skills: `Carousing`, `Linguistics`, `Bribery`, `Liaison`, `Steward`, `Vehicle`
- Advanced Education: `Advocate`, `Computer`, `Liaison`, `Linguistics`, `Medicine`, `Leadership`
- Ranks: 0 Attaché [`Liaison`], 1 Third Secretary, 2 Second Secretary, 3 First Secretary [`Admin`], 4 Counselor, 5 Minister, 6 Ambassador
- Cash: 1000, 5000, 10000, 20000, 20000, 50000, 100000
- Material: `Low Passage`, `+1 Edu`, `Mid Passage`, `High Passage`, `+1 Soc`, `High Passage`, `Explorers' Society`

### Entertainer (`entertainer.py`, key `"entertainer"`)

- Qualification: Social Standing 8
- Survival: Intelligence 4
- Commission: none (`None`/`None`)
- Advancement: none (`None`/`None`)
- Re-enlistment: 6
- Personal Development: `+1 Dex`, `+1 Int`, `+1 Edu`, `+1 Soc`, `Carousing`, `Melee Combat`
- Service Skills: `Athletics`, `Admin`, `Carousing`, `Bribery`, `Gambling`, `Vehicle`
- Specialist Skills: `Computer`, `Carousing`, `Bribery`, `Liaison`, `Gambling`, `Recon`
- Advanced Education: `Advocate`, `Computer`, `Carousing`, `Linguistics`, `Medicine`, `Sciences`
- Ranks: single rank-0 entry, title `Entertainer`, bonus skill [`Carousing`]
- Cash: 2000, 10000, 20000, 20000, 50000, 100000, 100000
- Material (6 entries; SRD's blank 7th slot dropped, unreachable at rank 0):
  `Low Passage`, `+1 Edu`, `+1 Soc`, `High Passage`, `Explorers' Society`, `High Passage`

### Noble (`noble.py`, key `"noble"`)

- Qualification: Social Standing 8
- Survival: Social Standing 4
- Commission: Education 5
- Advancement: Intelligence 8
- Re-enlistment: 6
- Personal Development: `+1 Dex`, `+1 Int`, `+1 Edu`, `+1 Soc`, `Carousing`, `Melee Combat`
- Service Skills: `Athletics`, `Admin`, `Carousing`, `Leadership`, `Gambling`, `Vehicle`
- Specialist Skills: `Computer`, `Carousing`, `Gun Combat`, `Melee Combat`, `Liaison`, `Animals`
- Advanced Education: `Advocate`, `Computer`, `Liaison`, `Linguistics`, `Medicine`, `Sciences`
- Ranks: 0 Courtier [`Carousing`], 1 Knight, 2 Baron, 3 Marquis, 4 Count [`Advocate`], 5 Duke, 6 Archduke
- Cash: 2000, 10000, 20000, 20000, 50000, 100000, 100000
- Material: `High Passage`, `+1 Edu`, `+1 Int`, `High Passage`, `Explorers' Society`, `High Passage`, `1D6 Ship Shares`

## Testing

Follow the per-career test-file pattern (see `tests/test_surface_career.py`):
each career gets `tests/test_<name>_career.py` asserting name, every
stat/target, commission/advancement (or `None`), re-enlistment, each of the
four 6-entry skill tables, the ranks (titles + bonus skills, including the
"grants nothing" ranks), and the cash and material tables. Registry tests
(key present, value identity) go alongside the existing ones in
`tests/test_careers.py`.

Ship-shares mechanic tests:

- **Model** (`tests/test_models.py`): a `Benefit(kind="material",
  material_name="Ship Shares", material_quantity=4)` constructs and carries
  the quantity; existing benefits default `material_quantity` to `None`.
- **Generator** (`tests/test_generator.py`): with a roller sequenced so a
  muster-out material roll draws Noble's ship-shares slot and the 1D6 yields
  a known value, the resulting `Benefit` has `material_name == "Ship Shares"`
  and the expected `material_quantity`; ship shares alter neither
  characteristics nor skills.
- **Formatter** (`tests/test_formatter.py`): two ship-shares benefits of 3
  and 4 render `"7 Ship Shares"`; a single share of 1 renders
  `"1 Ship Shares"`; ship-shares quantities do not render as `(xN)` and
  coexist correctly with boosts and plain items.

Coverage stays ≥85% on `src/cetools` (enforced by the suite).

## Out of scope

- The other 13 non-draft careers (Batches 2–4).
- Any change to `DRAFT_TABLE` (these careers are not draftable).
- Pluralization of the ship-shares label (`"1 Ship Shares"` is accepted).
- Applying ship shares to a ship/asset model — they are recorded as a
  benefit quantity only.
