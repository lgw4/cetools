# Learned Careers (Batch 4)

**Date:** 2026-07-08
**Status:** Approved, ready for implementation planning

## Context

Batch 4 — the **final** batch — of the 18-non-draft-career effort (roadmap in
`docs/superpowers/specs/2026-07-08-optional-qualification-careers-design.md`).
It adds the three **Learned careers** — Physician, Scientist, Technician —
following the established data-driven pattern: each is a frozen `Career` in
`src/cetools/engine/careers/<name>.py`, registered in `registry.py`, with a
per-career test file, plus a README update.

Shipping these completes **all 24 SRD careers**. The registry grows from 21 to
24 careers.

These are **non-draft** careers: added to `CAREER_REGISTRY` (selectable via
`--career`) but **not** `DRAFT_TABLE`. Registry keys are the lowercased names
(`"physician"`, `"scientist"`, `"technician"`).

Batch 4 is **data plus one small engine change.** No model or formatter
changes. All three careers have a full commission and advancement target, full
7-entry rank/cash/material tables, and **no ship shares**.

### Once-only benefits (engine change: generalize the dedup)

The muster-out logic already treats **Explorers' Society** as a once-only
benefit: `_roll_material_benefit` in `generator.py` re-rolls if the drawn
benefit equals the hard-coded `_UNIQUE_MATERIAL_BENEFIT = "Explorers' Society"`
and it has already been granted this muster-out.

Scientist's material table contains a **Research Vessel** benefit, and the
already-shipped Scout career has a **Courier Vessel** benefit. The SRD rules
text only *explicitly* marks Explorers' Society as "can only be received once,"
but this project treats **all three ship/society grants as once-only** — you
cannot sensibly be granted the same single vessel twice. This is a deliberate,
documented interpretation beyond the literal SRD text.

The engine change is minimal:

- Rename `_UNIQUE_MATERIAL_BENEFIT` (a single `str`) to
  `_UNIQUE_MATERIAL_BENEFITS`, a `frozenset[str]`:
  `{"Explorers' Society", "Research Vessel", "Courier Vessel"}`.
- Change the dedup check in `_roll_material_benefit` from
  `name == _UNIQUE_MATERIAL_BENEFIT` to `name in _UNIQUE_MATERIAL_BENEFITS`.

Everything else is unchanged: a once-only benefit still flows through
`_muster_out`'s non-ship-shares branch, `_apply_stat_boost` no-ops on it (no
`+1 ` prefix), and it is recorded once as `Benefit(kind="material",
material_name=...)`.

**This retroactively changes the Scout career:** Courier Vessel is now capped
at one per muster-out (previously it could be granted repeatedly). That is the
intended behavior and gets its own regression test (below).

Data below is transcribed verbatim from the canonical Cepheus Engine SRD
character-creation page
(`https://evolvedexperiment.github.io/cepheus-srd/character-creation.html`),
cross-checked against the orffenspace mirror. Two normalizations are noted
below (rank-title expansion).

## Career Data

Notation: `+1 X` are stat boosts. Rank entries show the granted bonus skill in
brackets; ranks with no bracket grant nothing (empty `bonus_skills`). Cash and
material tables are in table order (rolls 1–7).

Two tables are **identical across all three careers**:

- **Personal Development:** `+1 Str`, `+1 Dex`, `+1 End`, `+1 Int`, `+1 Edu`, `Gun Combat`
- **Advanced Education:** `Advocate`, `Computer`, `Jack o' Trades`, `Linguistics`, `Medicine`, `Sciences`

### Physician (`physician.py`, key `"physician"`)

- Qualification: Education 6
- Survival: Intelligence 4
- Commission: Intelligence 5
- Advancement: Education 8
- Re-enlistment: 5
- Service Skills: `Admin`, `Computer`, `Mechanics`, `Medicine`, `Leadership`, `Sciences`
- Specialist Skills: `Computer`, `Carousing`, `Electronics`, `Medicine`, `Medicine`, `Sciences`
- Ranks: 0 Intern [`Medicine`], 1 Resident, 2 Senior Resident, 3 Chief Resident,
  4 Attending Physician [`Admin`], 5 Service Chief, 6 Hospital Administrator
- Cash: 2000, 10000, 20000, 20000, 50000, 100000, 100000
- Material (7 entries; Explorers' Society at index 4):
  `Low Passage`, `+1 Edu`, `+1 Int`, `High Passage`, `Explorers' Society`, `High Passage`, `+1 Soc`

**Rank-title normalization:** the SRD abbreviates rank 4 as `Attending Phys.`
and rank 6 as `Hospital Admin.` to fit the column width. These are recorded as
the full titles **`Attending Physician`** and **`Hospital Administrator`**
(analogous to the Batch 3 `Pilot`→`Piloting` normalization). Every other title
is already full-length.

### Scientist (`scientist.py`, key `"scientist"`)

- Qualification: Education 6
- Survival: Education 5
- Commission: Intelligence 7
- Advancement: Intelligence 6
- Re-enlistment: 5
- Service Skills: `Admin`, `Computer`, `Electronics`, `Medicine`, `Bribery`, `Sciences`
- Specialist Skills: `Navigation`, `Admin`, `Sciences`, `Sciences`, `Animals`, `Vehicle`
- Ranks: 0 Instructor [`Sciences`], 1 Adjunct Professor, 2 Research Professor,
  3 Assistant Professor [`Computer`], 4 Associate Professor, 5 Professor,
  6 Distinguished Professor
- Cash: 1000, 5000, 10000, 10000, 20000, 50000, 50000
- Material (7 entries; Research Vessel at index 6, once-only — see engine change):
  `Low Passage`, `+1 Edu`, `+1 Int`, `Mid Passage`, `+1 Soc`, `High Passage`, `Research Vessel`

### Technician (`technician.py`, key `"technician"`)

- Qualification: Education 6
- Survival: Dexterity 4
- Commission: Education 5
- Advancement: Intelligence 8
- Re-enlistment: 5
- Service Skills: `Admin`, `Computer`, `Mechanics`, `Medicine`, `Electronics`, `Sciences`
- Specialist Skills: `Computer`, `Electronics`, `Gravitics`, `Linguistics`, `Engineering`, `Animals`
- Ranks: 0 Technician [`Computer`], 1 Team Lead, 2 Supervisor, 3 Manager,
  4 Director [`Admin`], 5 Vice-President, 6 Executive Officer
- Cash: 1000, 5000, 10000, 10000, 20000, 50000, 50000
- Material (7 entries; no special benefits):
  `Low Passage`, `+1 Edu`, `+1 Int`, `Mid Passage`, `Mid Passage`, `High Passage`, `+1 Soc`

## Testing

Follow the per-career test-file pattern: each career gets
`tests/test_<name>_career.py` asserting name, every stat/target,
commission/advancement, re-enlistment, the four 6-entry skill tables, the ranks
(titles + bonus skills, including the "grants nothing" ranks), and the cash and
material tables.

Targeted behavior tests (`tests/test_generator.py`), covering the generalized
once-only dedup:

- **Scientist Research Vessel is once-only** — a Scientist muster-out that
  draws the `Research Vessel` slot (index 6) repeatedly records it **at most
  once**; further draws re-roll to another benefit. Mirrors the existing
  Explorers' Society dedup test.
- **Scout Courier Vessel is once-only** — the retroactive behavior change: a
  Scout muster-out records `Courier Vessel` at most once. Guards the Scout
  regression.

(Physician's Explorers' Society dedup is already covered by Batch 1 tests; no
new test needed there.)

Registry tests (`tests/test_careers.py`): the three keys resolve to their
careers, the registry now holds 24 careers, and `DRAFT_TABLE` stays length 6
with none of the three in it.

CLI tests (`tests/test_cli.py`): the "Valid careers:" strings update to the new
sorted 24-entry list. The `"smuggler"` unknown-career sentinel stays valid
(none of the three careers is `smuggler`); the full-suite run confirms it still
hits the list path, not a `difflib` "Did you mean" suggestion.

Coverage stays ≥85% on `src/cetools` (enforced by the suite).

## Out of scope

- Any change to `DRAFT_TABLE` or the draft mechanic.
- Any model or formatter code, and any engine change beyond generalizing the
  once-only-benefit dedup described above.
- Auditing other careers for further once-only candidates: ship shares
  explicitly accumulate, and Explorers' Society / Research Vessel / Courier
  Vessel are the only ship/society grants in the SRD career tables. No other
  benefit is affected.
