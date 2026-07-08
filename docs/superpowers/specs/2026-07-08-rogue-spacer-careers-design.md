# Rogue & Spacer Careers (Batch 3)

**Date:** 2026-07-08
**Status:** Approved, ready for implementation planning

## Context

Batch 3 of the 18-non-draft-career effort (roadmap in
`docs/superpowers/specs/2026-07-08-optional-qualification-careers-design.md`).
It adds the five **Rogue/spacer careers** — Belter, Mercenary, Pirate, Rogue,
Merchant — following the established data-driven pattern: each is a frozen
`Career` in `src/cetools/engine/careers/<name>.py`, registered in
`registry.py`, with a per-career test file, plus a README update.

These are **non-draft** careers: added to `CAREER_REGISTRY` (selectable via
`--career`) but **not** `DRAFT_TABLE`. Registry keys are the lowercased names
(`"belter"`, `"mercenary"`, `"pirate"`, `"rogue"`, `"merchant"`).

Batch 3 is **pure data plus one test-only change.** No engine, model, or
formatter changes. It reuses two existing mechanisms:

- **Ship shares (Batch 1):** Belter, Mercenary, Pirate, and Merchant tables
  contain the `"1D6 Ship Shares"` sentinel, rolled to a quantity by
  `_muster_out` — already supported.
- **Explorers' Society once-only dedup (Batch 1):** Merchant's table contains
  `Explorers' Society`, the existing `_UNIQUE_MATERIAL_BENEFIT`. No new
  once-only benefit appears in this batch, so the hard-coded dedup needs no
  generalization. Merchant's table carries both ship shares and Explorers'
  Society; they resolve through independent branches in `_muster_out` and
  coexist correctly.

The one test-only change: `"merchant"` is currently the unknown-career
sentinel in `tests/test_cli.py`. Registering the real Merchant makes
`--career merchant` succeed, so that negative test switches to a new
nonsense-but-realistic token, **`"smuggler"`** (not one of the careers; the
plan's full-suite run verifies it still hits the "Valid careers:" list path
rather than a `difflib` "Did you mean" suggestion).

Established conventions reused:

- **No-commission/advancement careers** (Belter) use the Scout `None` pattern.
- **No-rank careers** get a single `RankEntry(0, "<CareerName>", (bonus...))`.
  Belter's rank-0 has an empty bonus tuple (the SRD lists no rank-0 bonus
  skill), like Drifter.
- **Blank 7th material slot ("—")** on Belter is dropped: Belter has 6
  material entries. The other four have full ranks and keep 7 entries.
- **`Pilot` → `Piloting` normalization:** the SRD rank tables abbreviate the
  pilot skill as `[Pilot-1]` (Pirate rank 2, Merchant rank 3), but every skill
  table and the existing code use `Piloting` (Scout even grants `Piloting` as
  a rank bonus). Rank bonuses are recorded as `Piloting` so they stack with
  the character's other Piloting levels instead of creating a phantom `Pilot`
  skill.

Data below is transcribed verbatim from the SRD character-creation page
(with the single `Pilot`→`Piloting` normalization noted above).

## Career Data

Notation: `+1 X` are stat boosts. Rank entries show the granted bonus skill in
brackets; ranks with no bracket grant nothing (empty `bonus_skills`). Cash and
material tables are in table order.

### Belter (`belter.py`, key `"belter"`)

- Qualification: Intelligence 4
- Survival: Dexterity 7
- Commission: none (`None`/`None`)
- Advancement: none (`None`/`None`)
- Re-enlistment: 5
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `Zero-G`, `Melee Combat`, `Gambling`
- Service Skills: `Comms`, `Demolitions`, `Gun Combat`, `Gunnery`, `Prospecting`, `Piloting`
- Specialist Skills: `Zero-G`, `Electronics`, `Prospecting`, `Sciences`, `Vehicle`, `Vehicle`
- Advanced Education: `Advocate`, `Engineering`, `Medicine`, `Navigation`, `Comms`, `Tactics`
- Ranks: single rank-0 entry, title `Belter`, **no bonus skill** (empty tuple)
- Cash: 1000, 5000, 5000, 5000, 10000, 20000, 50000
- Material (6 entries; blank 7th slot dropped; ship-shares sentinel at index 4):
  `Low Passage`, `+1 Int`, `Mid Passage`, `Mid Passage`, `1D6 Ship Shares`, `High Passage`

### Mercenary (`mercenary.py`, key `"mercenary"`)

- Qualification: Intelligence 4
- Survival: Endurance 6
- Commission: Intelligence 7
- Advancement: Intelligence 6
- Re-enlistment: 5
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `Zero-G`, `Melee Combat`, `Gambling`
- Service Skills: `Comms`, `Mechanics`, `Gun Combat`, `Melee Combat`, `Gambling`, `Battle Dress`
- Specialist Skills: `Gravitics`, `Gun Combat`, `Gunnery`, `Melee Combat`, `Recon`, `Vehicle`
- Advanced Education: `Advocate`, `Engineering`, `Medicine`, `Navigation`, `Sciences`, `Tactics`
- Ranks: 0 Private [`Gun Combat`], 1 Lieutenant, 2 Captain, 3 Major [`Tactics`], 4 Lt Colonel, 5 Colonel, 6 Brigadier
- Cash: 1000, 5000, 10000, 20000, 20000, 50000, 100000
- Material (7 entries; ship-shares sentinel at index 6):
  `Low Passage`, `+1 Int`, `Weapon`, `High Passage`, `+1 Soc`, `High Passage`, `1D6 Ship Shares`

### Pirate (`pirate.py`, key `"pirate"`)

- Qualification: Dexterity 5
- Survival: Dexterity 6
- Commission: Strength 7
- Advancement: Intelligence 6
- Re-enlistment: 5
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `Melee Combat`, `Bribery`, `Gambling`
- Service Skills: `Streetwise`, `Electronics`, `Gun Combat`, `Melee Combat`, `Recon`, `Vehicle`
- Specialist Skills: `Zero-G`, `Comms`, `Engineering`, `Gunnery`, `Navigation`, `Piloting`
- Advanced Education: `Computer`, `Gravitics`, `Jack o' Trades`, `Medicine`, `Advocate`, `Tactics`
- Ranks: 0 Crewman [`Gunnery`], 1 Corporal, 2 Lieutenant [`Piloting`], 3 Lt Commander, 4 Commander, 5 Captain, 6 Commodore
- Cash: 1000, 5000, 10000, 20000, 20000, 50000, 100000
- Material (7 entries; ship-shares sentinel at index 6):
  `Low Passage`, `+1 Int`, `Weapon`, `High Passage`, `+1 Soc`, `High Passage`, `1D6 Ship Shares`

### Rogue (`rogue.py`, key `"rogue"`)

- Qualification: Dexterity 5
- Survival: Dexterity 4
- Commission: Strength 6
- Advancement: Intelligence 7
- Re-enlistment: 4
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `Melee Combat`, `Bribery`, `Gambling`
- Service Skills: `Streetwise`, `Mechanics`, `Gun Combat`, `Melee Combat`, `Recon`, `Vehicle`
- Specialist Skills: `Computer`, `Electronics`, `Bribery`, `Broker`, `Recon`, `Vehicle`
- Advanced Education: `Computer`, `Gravitics`, `Jack o' Trades`, `Medicine`, `Advocate`, `Tactics`
- Ranks: 0 Independent [`Streetwise`], 1 Associate, 2 Soldier [`Gun Combat`], 3 Lieutenant, 4 Underboss, 5 Consigliere, 6 Boss
- Cash: 1000, 5000, 5000, 5000, 10000, 20000, 50000
- Material (7 entries; no ship shares; `Weapon` at slots 3 and 5):
  `Low Passage`, `+1 Int`, `Weapon`, `Mid Passage`, `Weapon`, `High Passage`, `+1 Soc`

### Merchant (`merchant.py`, key `"merchant"`)

- Qualification: Intelligence 4
- Survival: Intelligence 5
- Commission: Intelligence 5
- Advancement: Education 8
- Re-enlistment: 4
- Personal Development: `+1 Str`, `+1 Dex`, `+1 End`, `Melee Combat`, `Steward`, `Gambling`
- Service Skills: `Comms`, `Engineering`, `Gun Combat`, `Melee Combat`, `Broker`, `Vehicle`
- Specialist Skills: `Carousing`, `Gunnery`, `Jack o' Trades`, `Medicine`, `Navigation`, `Piloting`
- Advanced Education: `Advocate`, `Engineering`, `Medicine`, `Navigation`, `Sciences`, `Tactics`
- Ranks: 0 Crewman [`Steward`], 1 Deck Cadet, 2 Fourth Officer, 3 Third Officer [`Piloting`], 4 Second Officer, 5 First Officer, 6 Captain
- Cash: 1000, 5000, 10000, 20000, 20000, 50000, 100000
- Material (7 entries; ship-shares sentinel at index 4, Explorers' Society at index 6; slot 2 is `+1 Edu`, not `+1 Int`):
  `Low Passage`, `+1 Edu`, `Weapon`, `High Passage`, `1D6 Ship Shares`, `High Passage`, `Explorers' Society`

## Testing

Follow the per-career test-file pattern: each career gets
`tests/test_<name>_career.py` asserting name, every stat/target,
commission/advancement (or `None`), re-enlistment, the four 6-entry skill
tables, the ranks (titles + bonus skills, including the "grants nothing"
ranks), and the cash and material tables.

Targeted behavior test (the ship-shares and Explorers'-Society mechanisms are
already covered by Batch 1/2 tests, so only one new generator test is added):

- **Belter ship shares** (`tests/test_generator.py`): a Belter muster-out that
  draws the `1D6 Ship Shares` slot (index 4, reachable at rank 0 with no rank
  DM) records a `Ship Shares` benefit with a rolled `material_quantity`.
  Mirrors the Hunter test.

Registry tests (`tests/test_careers.py`): the five keys resolve to their
careers, and `DRAFT_TABLE` stays length 6 with none of the five in it.

CLI tests (`tests/test_cli.py`): the `"merchant"` unknown-career sentinel is
replaced with `"smuggler"` (Merchant is now a real career), and the two
"Valid careers:" strings update to the new sorted 21-entry list. The
full-suite run confirms `"smuggler"` (and the existing `"xyzzy"`) still hit
the list path, not a `difflib` "Did you mean" suggestion.

Coverage stays ≥85% on `src/cetools` (enforced by the suite).

## Out of scope

- The remaining 3 non-draft careers (Batch 4: Physician, Scientist,
  Technician).
- Any change to `DRAFT_TABLE` or the draft mechanic.
- Generalizing the `_UNIQUE_MATERIAL_BENEFIT` dedup — no Batch 3 career has a
  once-only benefit other than the already-handled `Explorers' Society`.
- Any new engine/model/formatter code.
