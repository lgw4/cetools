# Frontier Careers (Batch 2)

**Date:** 2026-07-08
**Status:** Approved, ready for implementation planning

## Context

Batch 2 of the 18-non-draft-career effort (roadmap in
`docs/superpowers/specs/2026-07-08-optional-qualification-careers-design.md`).
It adds the five **Frontier/survival careers** — Athlete, Barbarian,
Colonist, Hunter, Drifter — following the established data-driven pattern:
each is a frozen `Career` instance in
`src/cetools/engine/careers/<name>.py`, registered in `registry.py`, with a
per-career test file, plus a README update.

These are **non-draft** careers: added to `CAREER_REGISTRY` (selectable via
`--career`) but **not** `DRAFT_TABLE` (the draft stays the canonical six).
Registry keys are the lowercased names (`"athlete"`, `"barbarian"`,
`"colonist"`, `"hunter"`, `"drifter"`).

Batch 2 is **pure data — no engine or model changes.** It is the first batch
to consume two mechanisms built earlier:

- **Optional qualification (Batch 0):** Drifter has no qualification
  requirement (`qualification_stat=None`, `qualification_target=None`) and is
  "always open" per the SRD. `generate_character` auto-passes enlistment and
  `roll_until_qualified` returns immediately for it — already supported.
  Drifter's SRD role as the automatic fallback when another career's
  qualification fails is **out of scope**: it is selectable by name, not
  auto-assigned.
- **Ship shares (Batch 1):** Hunter's material table contains the
  `"1D6 Ship Shares"` sentinel, rolled to a quantity by `_muster_out` and
  rendered as `"N Ship Shares"` — already supported.

Established conventions reused:

- **No-commission/advancement careers** (Athlete, Barbarian, Hunter, Drifter)
  use the Scout `None` pattern for `commission_*`/`advancement_*`.
- **No-rank careers** get a single `RankEntry(0, "<CareerName>", (bonus...))`
  (the Entertainer/Scout precedent). Drifter's rank-0 title is `"Drifter"`
  with empty bonus skills (the SRD lists neither).
- **Blank 7th material slot ("—")** on Athlete, Barbarian, Hunter, and
  Drifter is dropped: those careers have 6 material entries. The 7th column is
  unreachable at rank 0 (material DM only applies at rank ≥5). Colonist has
  full ranks, so it keeps all 7 material entries.
- **Cash benefit of `0`** (Barbarian, Drifter first slot) is valid data:
  `Benefit(kind="cash", cash_amount=0)` passes `__post_init__` (0 is not
  `None`).
- **Duplicate skills within a table** (e.g. Athlete `Athletics` twice,
  Barbarian `Gun Combat` twice) are valid and transcribed verbatim.

Data below is transcribed verbatim from the SRD character-creation page.

## Career Data

Notation: `+1 X` are stat boosts. Rank entries show the granted bonus skill in
brackets; ranks with no bracket grant nothing (empty `bonus_skills`). Cash and
material tables are in table order.

### Athlete (`athlete.py`, key `"athlete"`)

- Qualification: Endurance 8
- Survival: Dexterity 5
- Commission: none (`None`/`None`)
- Advancement: none (`None`/`None`)
- Re-enlistment: 6
- Personal Development: `+1 Dex`, `+1 Int`, `+1 Edu`, `+1 Soc`, `Carousing`, `Melee Combat`
- Service Skills: `Athletics`, `Admin`, `Carousing`, `Computer`, `Gambling`, `Vehicle`
- Specialist Skills: `Zero-G`, `Athletics`, `Athletics`, `Computer`, `Leadership`, `Gambling`
- Advanced Education: `Advocate`, `Computer`, `Liaison`, `Linguistics`, `Medicine`, `Sciences`
- Ranks: single rank-0 entry, title `Athlete`, bonus skill [`Athletics`]
- Cash: 2000, 10000, 20000, 20000, 50000, 100000, 100000
- Material (6 entries; blank 7th slot dropped):
  `Low Passage`, `+1 Int`, `Weapon`, `High Passage`, `Explorers' Society`, `High Passage`

### Barbarian (`barbarian.py`, key `"barbarian"`)

- Qualification: Endurance 5
- Survival: Strength 6
- Commission: none (`None`/`None`)
- Advancement: none (`None`/`None`)
- Re-enlistment: 5
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `+1 Int`, `Athletics`, `Gun Combat`
- Service Skills: `Gun Combat`, `Melee Combat`, `Recon`, `Survival`, `Animals`, `Gun Combat`
- Specialist Skills: `Gun Combat`, `Jack o' Trades`, `Melee Combat`, `Recon`, `Animals`, `Tactics`
- Advanced Education: `Advocate`, `Linguistics`, `Medicine`, `Leadership`, `Broker`, `Tactics`
- Ranks: single rank-0 entry, title `Barbarian`, bonus skill [`Melee Combat`]
- Cash: 0, 1000, 2000, 5000, 5000, 10000, 10000
- Material (6 entries; blank 7th slot dropped):
  `Low Passage`, `+1 Int`, `Weapon`, `Weapon`, `+1 End`, `Mid Passage`

### Colonist (`colonist.py`, key `"colonist"`)

- Qualification: Endurance 5
- Survival: Endurance 6
- Commission: Intelligence 7
- Advancement: Education 6
- Re-enlistment: 5
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `+1 Int`, `Athletics`, `Gun Combat`
- Service Skills: `Mechanics`, `Gun Combat`, `Animals`, `Electronics`, `Survival`, `Vehicle`
- Specialist Skills: `Athletics`, `Carousing`, `Jack o' Trades`, `Engineering`, `Animals`, `Vehicle`
- Advanced Education: `Advocate`, `Linguistics`, `Medicine`, `Liaison`, `Admin`, `Animals`
- Ranks: 0 Citizen [`Survival`], 1 District Leader, 2 District Delegate, 3 Council Advisor [`Liaison`], 4 Councilor, 5 Lieutenant Governor, 6 Governor
- Cash: 1000, 5000, 5000, 5000, 10000, 20000, 50000
- Material (7 entries):
  `Low Passage`, `+1 Int`, `Weapon`, `Mid Passage`, `Mid Passage`, `High Passage`, `+1 Soc`

### Hunter (`hunter.py`, key `"hunter"`)

- Qualification: Endurance 5
- Survival: Strength 8
- Commission: none (`None`/`None`)
- Advancement: none (`None`/`None`)
- Re-enlistment: 6
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `+1 Int`, `Athletics`, `Gun Combat`
- Service Skills: `Mechanics`, `Gun Combat`, `Melee Combat`, `Recon`, `Survival`, `Vehicle`
- Specialist Skills: `Admin`, `Comms`, `Electronics`, `Recon`, `Animals`, `Vehicle`
- Advanced Education: `Advocate`, `Linguistics`, `Medicine`, `Liaison`, `Animals`, `Animals`
- Ranks: single rank-0 entry, title `Hunter`, bonus skill [`Survival`]
- Cash: 1000, 5000, 10000, 20000, 20000, 50000, 100000
- Material (6 entries; blank 7th slot dropped; slot 5 is the ship-shares sentinel):
  `Low Passage`, `+1 Int`, `Weapon`, `High Passage`, `1D6 Ship Shares`, `High Passage`

### Drifter (`drifter.py`, key `"drifter"`)

- Qualification: **none** (`qualification_stat=None`, `qualification_target=None`) — always open
- Survival: Endurance 5
- Commission: none (`None`/`None`)
- Advancement: none (`None`/`None`)
- Re-enlistment: 5
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `Melee Combat`, `Bribery`, `Gambling`
- Service Skills: `Streetwise`, `Mechanics`, `Gun Combat`, `Melee Combat`, `Recon`, `Vehicle`
- Specialist Skills: `Electronics`, `Melee Combat`, `Bribery`, `Streetwise`, `Gambling`, `Recon`
- Advanced Education: `Computer`, `Engineering`, `Jack o' Trades`, `Medicine`, `Liaison`, `Tactics`
- Ranks: single rank-0 entry, title `Drifter`, **no bonus skill** (empty tuple)
- Cash: 0, 1000, 2000, 5000, 5000, 10000, 10000
- Material (6 entries; blank 7th slot dropped):
  `Low Passage`, `+1 Int`, `Weapon`, `Weapon`, `Mid Passage`, `Mid Passage`

## Testing

Follow the per-career test-file pattern (see `tests/test_entertainer_career.py`
for the no-rank/`None`-commission shape and `tests/test_agent_career.py` for
the full-rank shape): each career gets `tests/test_<name>_career.py` asserting
name, every stat/target (Drifter's qualification asserted `is None`),
commission/advancement (or `None`), re-enlistment, the four 6-entry skill
tables, the ranks (titles + bonus skills, including the "grants nothing"
ranks), and the cash and material tables.

Targeted behavior tests:

- **Drifter no-qualification end-to-end** (`tests/test_generator.py`, the
  Batch 0 deferred consumer test): `generate_career_character(DRIFTER)`
  returns a `Character` (never loops or raises on `None` qualification), and
  `DRIFTER.qualification_stat is None`.
- **Zero cash benefit** (`tests/test_generator.py`): a Barbarian or Drifter
  muster-out that draws the `0` cash slot produces a valid `Character` (roller
  sequenced to hit cash index 0); total funds handle the `0` correctly.
- **Hunter ship shares** (`tests/test_generator.py`): a Hunter muster-out that
  draws the `1D6 Ship Shares` slot records a `Ship Shares` benefit with a
  rolled `material_quantity` (reuses the Batch 1 mechanic; no rank DM needed
  since the slot is index 4, reachable at rank 0).

Registry tests (`tests/test_careers.py`): the five keys resolve to their
careers, and `DRAFT_TABLE` stays length 6 with none of the five in it.

The two hard-coded `tests/test_cli.py` "Valid careers:" strings update to the
new sorted 16-entry list.

Coverage stays ≥85% on `src/cetools` (enforced by the suite).

## Out of scope

- The remaining 8 non-draft careers (Batches 3–4).
- Any change to `DRAFT_TABLE` or the draft mechanic.
- Drifter's SRD auto-fallback-on-failed-qualification behavior (selectable by
  name only).
- Any new engine/model/formatter code — Batch 2 is pure data.
