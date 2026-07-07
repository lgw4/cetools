# Background Skills — Design

## Summary

Replace the placeholder background-skill logic in `generate_character`
(`src/cetools/engine/generator.py`) with rules-accurate background skills per
the Cepheus SRD. Each character receives a number of level-0 skills based on
their Education, drawn from a homeworld pool and the primary education pool.

Source rule (verbatim, Cepheus SRD, character creation):

> Before embarking on your careers, you get a number of background skills equal
> to 3 + your Education DM (1 to 5, depending on your Education score).

The first two background skills come from **Homeworld Skills** (SRD tables keyed
to planetary description and trade codes); the rest come from the **Primary
Education Skills** list. All background skills are gained at level 0.

## Current state

`generate_character` contains a placeholder that always grants the same three
fixed skills (`Admin`, `Advocate`, `Animals`) at level 0, regardless of
Education:

```python
skills: dict[str, int] = {}
for i in range(3):
    bg_skill = _BACKGROUND_SKILLS[i % len(_BACKGROUND_SKILLS)]
    skills[bg_skill] = skills.get(bg_skill, -1) + 1
```

The module already holds the 15 Primary Education Skills in the
`_BACKGROUND_SKILLS` tuple. Two existing tests lean on `Advocate` always being
present as a side effect of this placeholder.

## Scope decisions

- **Homeworld skills:** cetools has no world/planet/trade-code subsystem.
  Rather than generate a homeworld, this feature introduces a curated
  **homeworld skill pool** (the deduplicated union of the SRD homeworld tables)
  and draws the first background skills from it. The character has no defined
  homeworld; the pool is simply the skill source for those slots. Full
  homeworld/world generation is explicitly out of scope (possible future work).
- **Count:** `count = 3 + characteristic_modifier(Education)`. Re-reading the
  SRD, the "(1 to 5)" parenthetical describes the *resulting number of skills*,
  not the DM. With 2d6 Education and this project's existing
  `characteristic_modifier`, `3 + EDU DM` naturally lands in 1–5. No special
  clamping beyond a floor of 0.
- **Selection:** generation is automated (no player choice), so skills are drawn
  **randomly without replacement** using the injected `DiceRoller`, keeping
  tests deterministic.
- **Provenance:** background skills merge into the character's `skills` dict at
  level 0 with no separate tracking, exactly as career skills flow today. No
  data-model, CLI, or formatter changes.

## Behavior

At character-creation start (before qualification and careers), grant `count`
**distinct** skills at level 0:

1. `count = max(0, 3 + characteristic_modifier(Education))`.
2. `homeworld_count = min(2, count)` — drawn from the homeworld pool.
3. `education_count = count - homeworld_count` — drawn from the education pool,
   excluding any skill already chosen from the homeworld pool so the whole
   background set is distinct.
4. Each chosen skill is seeded at level 0 in the `skills` dict. Career service
   skills, rank bonuses, and skill rolls stack on top afterward, unchanged.

### Homeworld skill pool

Deduplicated union of the SRD homeworld tables (10 skills):

`Animals, Broker, Carousing, Computer, Gun Combat, Melee Combat, Streetwise,
Survival, Watercraft, Zero-G`

Note: `Animals`, `Carousing`, and `Computer` also appear in the education pool;
the exclusion step in (3) prevents duplicates across the two pools.

### Edge cases

- `count == 1` → 1 homeworld skill, 0 education skills.
- `count == 2` → 2 homeworld skills, 0 education skills.
- `count` is floored at 0. In practice 2d6 Education (minimum score 2, DM -2)
  never yields fewer than 1.
- Pool sizes always exceed demand: homeworld draws ≤ 2 of 10; education draws
  ≤ 10 of (15 minus up to 2 excluded). Draws never run dry.

## Code changes

Two files.

### `src/cetools/engine/generator.py`

- Add `_HOMEWORLD_SKILLS` tuple (the 10 skills above).
- Rename the existing `_BACKGROUND_SKILLS` tuple to `_EDUCATION_SKILLS` (clearer
  now that there are two distinct pools).
- Add `_draw_distinct(pool, count, roller, exclude=())`: draw-without-replacement
  using the existing `(roll - 1) % len` indexing idiom against a shrinking
  remaining list. Bounded pop loop — terminates and is deterministic for a given
  roller.
- Add `_grant_background_skills(characteristics, skills, roller)` implementing
  the behavior above, and call it where the placeholder loop currently sits in
  `generate_character`.

### `tests/test_generator.py`

- New tests:
  - `count` equals `3 + EDU DM` across representative Education values (set via
    `preset_characteristics`): e.g. EDU 2 → 1, EDU 7 → 3, EDU 10 → 4, EDU 12 → 5,
    EDU 15 → 6.
  - The first `min(2, count)` background skills come from the homeworld pool.
  - The remaining skills come from the education pool.
  - All background skills are distinct and at level 0.
  - Determinism: the same roller produces the same background skills.
- Update the two existing tests that assume `Advocate` is always granted
  (`test_education_below_8_excludes_advanced_education_skills` and its neighbor)
  so they control Education/roller instead of relying on the fixed placeholder.

## Out of scope

- Homeworld / world / trade-code generation.
- Recording or displaying background-skill provenance (homeworld vs. education).
- Any CLI, formatter, or data-model changes.

## Verification

`uv run black . && uv run flake8 src tests && uv run pytest` must pass, with
`src/cetools` coverage staying at or above 85%.
