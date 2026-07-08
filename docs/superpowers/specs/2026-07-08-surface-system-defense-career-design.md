# Surface System Defense (Planetary Army) career — design

## Summary

Add the **Surface System Defense (Planetary Army)** career to the cetools
character generator, as described in the Cepheus SRD character-creation rules
(<https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#careers>).

The career system is fully data-driven: a career is a frozen `Career` dataclass
instance, and the generator, CLI, and validation all consume it generically.
Adding this career therefore requires **no engine changes** — a new data file,
three registry edits, and tests. Structurally the new career is close to its
sibling `Maritime System Defense`, with army-style ranks and one notable
divergence: Survival keys off **Education**, not Endurance.

This is the sixth and final career of the SRD draft table, so it also retires
the long-standing `navy` placeholder in `DRAFT_TABLE` slot 6.

## Architecture

Three touch points, all additive:

1. `src/cetools/engine/careers/surface.py` — new module defining
   `SURFACE_CAREER = Career(...)`.
2. `src/cetools/engine/careers/registry.py` — register the career and make it
   draftable (finally filling slot 6).
3. `tests/test_surface_career.py` (new) and `tests/test_careers.py` (updated) —
   data and behavioral coverage.

No changes to `generator.py`, `cli/character.py`, or `base.py`. The
Education 8+ gate that unlocks the advanced-education table is already enforced
generically in `generator.py`, so the new career needs no special handling.

## 1. Career data: `src/cetools/engine/careers/surface.py`

`SURFACE_CAREER` is a `Career` instance built from the SRD values below.
Modeled on `maritime.py`.

| Field | Value |
|---|---|
| `name` | `"Surface System Defense"` |
| `qualification_stat` / `qualification_target` | `"Endurance"` / `5` |
| `survival_stat` / `survival_target` | `"Education"` / `5` |
| `commission_stat` / `commission_target` | `"Endurance"` / `6` |
| `advancement_stat` / `advancement_target` | `"Education"` / `7` |
| `reenlistment_target` | `5` |

The `name` drops the "(Planetary Army)" parenthetical, matching how the sibling
careers store `"Maritime System Defense"` rather than
`"Maritime System Defense (Planetary Navy)"`.

Note the distinctive **Survival: Education 5+** — unlike Maritime (Endurance),
this career survives on training rather than toughness. Confirmed against the
SRD source.

### Skill tables (each exactly 6 entries)

- **personal_development:** `+1 Str`, `+1 Dex`, `+1 End`, `Athletics`,
  `Melee Combat`, `Vehicle`
- **service_skills:** `Mechanics`, `Gun Combat`, `Gunnery`, `Melee Combat`,
  `Recon`, `Battle Dress`
- **specialist_skills:** `Comms`, `Demolitions`, `Gun Combat`, `Melee Combat`,
  `Survival`, `Vehicle`
- **advanced_education:** `Advocate`, `Computer`, `Jack o' Trades`, `Medicine`,
  `Leadership`, `Tactics` (unlocked at Education 8+, enforced generically)

### Ranks (0–6)

| Rank | Title | Bonus skill |
|---|---|---|
| 0 | Private | Gun Combat |
| 1 | Lieutenant | — |
| 2 | Captain | — |
| 3 | Major | Leadership |
| 4 | Lt Colonel | — |
| 5 | Colonel | — |
| 6 | General | — |

Rank 0 grants Gun Combat-1 at enlistment and rank 3 grants Leadership-1. Bonus
skills are stored as bare names (`"Gun Combat"`, `"Leadership"`) to match how
`maritime.py`/`marine.py` store theirs; the SRD's "-1" is implied by the engine.

### Mustering-out benefits

- **cash_benefits:** `1000, 5000, 10000, 10000, 20000, 50000, 50000`
- **material_benefits:** `Low Passage`, `+1 Int`, `Weapon`, `Mid Passage`,
  `Weapon`, `High Passage`, `+1 Soc`

(The cash table is identical to Maritime/Marine; the material table differs at
slot 2, which is `+1 Int` here rather than `+1 Edu`.)

## 2. Registry: `src/cetools/engine/careers/registry.py`

- Import `SURFACE_CAREER`.
- Add key `"surface system defense"` → `SURFACE_CAREER` to `CAREER_REGISTRY`.
- Update `DRAFT_TABLE` slot 6 from the `navy` placeholder to
  `"surface system defense"`, making the table fully SRD-accurate.

The SRD Draft is a 1D6 roll:

| Roll | Service |
|---|---|
| 1 | Aerospace System Defense |
| 2 | Marine |
| 3 | Maritime System Defense |
| 4 | Navy |
| 5 | Scout |
| 6 | Surface System Defense (Planetary Army) |

After this change `DRAFT_TABLE` becomes:

```python
DRAFT_TABLE = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "surface system defense",  # 6
)
```

The placeholder comment on slot 6 is removed, since the career now exists.

## 3. Tests

### `tests/test_surface_career.py` (new)

Mirror `tests/test_maritime_career.py`:

- **Fields:** each of qualification/survival/commission/advancement stat and
  target, reenlistment target, and name asserted individually. Include an
  explicit assertion that `survival_stat == "Education"` to lock in the
  divergence from the sibling careers.
- **Skill tables:** exact tuple contents of all four tables plus a 6-entry
  count check for each.
- **Ranks:** count is 7; titles match; indices equal position; rank 0 bonus is
  `Gun Combat`; rank 3 bonus is `Leadership`; ranks 1, 2, 4, 5, 6 have empty
  bonus skills.
- **Benefits:** cash tuple contents and count (7); material tuple contents and
  count (7).
- **Behavior** (via the generator with `ConstantRoller` / `SequenceRoller` from
  `conftest.py`): commission success advances past rank 0; commission failure
  stays at rank 0; advancement increments rank; rank caps at 6 (General);
  Gun Combat applied at enlistment; Leadership applied on reaching rank 3.

### `tests/test_careers.py` (updated)

- Add assertions that `CAREER_REGISTRY` contains the
  `"surface system defense"` key mapping to `SURFACE_CAREER`.
- Update the existing draft-table assertions so slot 6 is
  `"surface system defense"` (no more `navy` placeholder); confirm length 6.

## 4. Documentation

- Update the README supported-careers line to include
  **Surface System Defense**.

## Verification

```bash
uv run black . && uv run flake8 src tests && uv run pytest
```

Coverage must stay at or above 85%. All new data is exercised by the new tests.
