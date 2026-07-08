# Maritime System Defense (Planetary Navy) career — design

## Summary

Add the **Maritime System Defense (Planetary Navy)** career to the cetools
character generator, as described in the Cepheus SRD character-creation rules
(<https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#careers>).

The career system is fully data-driven: a career is a frozen `Career` dataclass
instance, and the generator, CLI, and validation all consume it generically.
Adding this career therefore requires **no engine changes** — a new data file,
two registry edits, and tests. Structurally the new career is a near-exact twin
of the existing `Aerospace System Defense` career.

## Architecture

Three touch points, all additive:

1. `src/cetools/engine/careers/maritime.py` — new module defining
   `MARITIME_CAREER = Career(...)`.
2. `src/cetools/engine/careers/registry.py` — register the career and make it
   draftable.
3. `tests/test_maritime_career.py` (new) and `tests/test_careers.py` (updated) —
   data and behavioral coverage.

No changes to `generator.py`, `cli/character.py`, or `base.py`. The
Education 8+ gate that unlocks the advanced-education table is already enforced
generically in `generator.py` (`characteristics.get("Education", 0) >= 8`), so
the new career needs no special handling for it.

## 1. Career data: `src/cetools/engine/careers/maritime.py`

`MARITIME_CAREER` is a `Career` instance built from the SRD values below.
Modeled on `aerospace.py`.

| Field | Value |
|---|---|
| `name` | `"Maritime System Defense"` |
| `qualification_stat` / `qualification_target` | `"Endurance"` / `5` |
| `survival_stat` / `survival_target` | `"Endurance"` / `5` |
| `commission_stat` / `commission_target` | `"Intelligence"` / `6` |
| `advancement_stat` / `advancement_target` | `"Education"` / `7` |
| `reenlistment_target` | `5` |

The `name` drops the "(Planetary Navy)" parenthetical, matching how the sibling
career stores `"Aerospace System Defense"` rather than
`"Aerospace System Defense (Planetary Air Force)"`.

### Skill tables (each exactly 6 entries)

- **personal_development:** `+1 Str`, `+1 Dex`, `+1 End`, `Athletics`,
  `Melee Combat`, `Vehicle`
- **service_skills:** `Mechanics`, `Gun Combat`, `Gunnery`, `Melee Combat`,
  `Survival`, `Watercraft`
- **specialist_skills:** `Comms`, `Electronics`, `Gun Combat`, `Demolitions`,
  `Recon`, `Watercraft`
- **advanced_education:** `Advocate`, `Computer`, `Jack o' Trades`, `Medicine`,
  `Leadership`, `Tactics` (unlocked at Education 8+, enforced generically)

### Ranks (0–6)

| Rank | Title | Bonus skill |
|---|---|---|
| 0 | Seaman | Watercraft |
| 1 | Ensign | — |
| 2 | Lieutenant | — |
| 3 | Lt Commander | Leadership |
| 4 | Commander | — |
| 5 | Captain | — |
| 6 | Admiral | — |

Rank 0 grants Watercraft-1 at enlistment and rank 3 grants Leadership-1,
mirroring the aerospace bonus-skill pattern.

### Mustering-out benefits

- **cash_benefits:** `1000, 5000, 10000, 10000, 20000, 50000, 50000`
- **material_benefits:** `Low Passage`, `+1 Edu`, `Weapon`, `Mid Passage`,
  `Weapon`, `High Passage`, `+1 Soc`

(Both benefit tables are identical to Aerospace System Defense.)

## 2. Registry: `src/cetools/engine/careers/registry.py`

- Import `MARITIME_CAREER`.
- Add key `"maritime system defense"` → `MARITIME_CAREER` to `CAREER_REGISTRY`.
- Update `DRAFT_TABLE` to be SRD-accurate.

The SRD Draft is a 1D6 roll:

| Roll | Service |
|---|---|
| 1 | Aerospace System Defense |
| 2 | Marine |
| 3 | Maritime System Defense |
| 4 | Navy |
| 5 | Scout |
| 6 | Surface System Defense (Planetary Army) |

The current `DRAFT_TABLE` predates this career and used `navy` as filler in
slots 3 and 6. After this change it becomes:

```python
DRAFT_TABLE = (
    "aerospace system defense",
    "marine",
    "maritime system defense",  # SRD slot 3
    "navy",
    "scout",
    "navy",  # placeholder: Surface System Defense not yet implemented
)
```

Slot 6 remains `navy` with an explanatory comment because the Surface System
Defense (Planetary Army) career does not yet exist in this project. It becomes
SRD-accurate when that career is added later.

## 3. Tests

### `tests/test_maritime_career.py` (new)

Mirror `tests/test_aerospace_career.py`:

- **Fields:** each of qualification/survival/commission/advancement stat and
  target, reenlistment target, and name asserted individually.
- **Skill tables:** exact tuple contents of all four tables plus a 6-entry
  count check for each.
- **Ranks:** count is 7; titles match; indices equal position; rank 0 bonus is
  `Watercraft`; rank 3 bonus is `Leadership`; ranks 1, 2, 4, 5, 6 have empty
  bonus skills.
- **Benefits:** cash tuple contents and count (7); material tuple contents and
  count (7).
- **Behavior** (via `generate_character` with `ConstantRoller` /
  `SequenceRoller` from `conftest.py`): commission success advances past rank 0;
  commission failure stays at rank 0; advancement increments rank; rank caps at
  6 (Admiral); Watercraft applied at enlistment; Leadership applied on reaching
  rank 3.

### `tests/test_careers.py` (updated)

- Add assertions that `CAREER_REGISTRY` contains the `"maritime system defense"`
  key mapping to `MARITIME_CAREER`.
- Update the existing draft-table assertions to reflect the new `DRAFT_TABLE`
  contents and confirm length 6.

## Verification

```bash
uv run black . && uv run flake8 src tests && uv run pytest
```

Coverage must stay at or above 85%. All new data is exercised by the new tests.
