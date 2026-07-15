# Phase 0 Research: World Generation

**Source of truth**: Cepheus Engine SRD, Chapter 12 "Worlds"
(https://evolvedexperiment.github.io/cepheus-srd/worlds.html). All rule numbers below are
transcribed from that page (fetched as raw HTML per project convention). Terminology follows the
SRD exactly.

No `[NEEDS CLARIFICATION]` markers remain in the spec; the three clarifications (default naming,
naming method, subsector uniqueness) are recorded in `spec.md` and reflected in the decisions below.

---

## Part A—SRD rules digest (the generation algorithm)

The Universal World Profile (UWP) is generated in this order; later steps depend on earlier ones.

### 1. Size—`2D6 − 2` (range 0–10)

Table maps digit → diameter and surface gravity. Size 0 is "typically an asteroid".

### 2. Atmosphere—`2D6 − 7 + Size`

- If Size = 0 → Atmosphere = 0.
- Cap at 15 (F). Never below 0.

### 3. Hydrographics—`2D6 − 7 + Size`, then DMs:

- Size 0 or 1 → Hydrographics = 0 (overrides the roll).
- Atmosphere 0, 1, A, B, or C → DM −4.
- Atmosphere E → DM −2.
- Clamp to 0–10.

### 4. Population—`2D6 − 2`, then DMs:

- Size ≤ 2 → −1.
- Atmosphere ≥ A → −2.
- Atmosphere = 6 → +3.
- Atmosphere = 5 or 8 → +1.
- Hydrographics = 0 **and** Atmosphere < 3 → −2.
- Clamp to 0–10. If Population = 0 the world is uninhabited: Government, Law Level and Technology
  Level are all 0.

### 5. Government—`2D6 − 7 + Population`

- If Population = 0 → Government = 0.
- Clamp to 0–15. Table maps digit → government type.

### 6. Law Level—`2D6 − 7 + Government`

- If Government = 0 → Law Level = 0.
- Never below 0. (No stated ceiling; A+ = "Extreme Law".)

### 7. Starport—`2D6 − 7 + Population`, read from the Primary Starport table:

| Roll | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11+ |
|------|---|---|---|---|---|---|---|---|----|-----|
| Class | X | E | E | D | D | C | C | B | B | A |

(Roll may fall below 2 or above 11 after the −7; clamp the lookup to the table's ends: ≤2 → X,
≥11 → A.)

### 8. Technology Level—`1D6 +` DMs from the TL-DM matrix, then minimums:

DMs are summed across six UWP columns (Starport, Size, Atmosphere, Hydrographics, Population,
Government) keyed by each characteristic's value. Notable entries (full matrix goes in
`tables.py`):

- Starport: A +6, B +4, C +2, X −4.
- Size: 0–1 +2, 2–4 +1.
- Atmosphere: 0–3 +1, A–F +1.
- Hydrographics: 9 +1, A +2.
- Population: 1–5 +1, 9 +1, A +2, B +3, C +4.
- Government: 0 +1, 5 +1, 7 +2, D −2, E −2.

Never below 0. Then apply **minimum TL** overrides (raise TL to the minimum if lower):

- Hydrographics 0 or A **and** Population ≥ 6 → min 4.
- Atmosphere 4, 7, or 9 → min 5.
- Atmosphere ≤ 3 or A–C → min 7.
- Atmosphere D or E **and** Hydrographics A → min 7.

### 9. Population Modifier—`2D6 − 2`

- If Population > 0, minimum 1. If Population = 0, modifier = 0.
- Specific head-count = `modifier × 10^Population`.

### 10. Planetoid belts

- Presence: `2D6 ≥ 4`. If the primary world is Size 0, a belt is present automatically.
- Count when present: `1D6 − 3`, minimum 1.

### 11. Gas giants

- Presence: `2D6 ≥ 5`.
- Count when present: `1D6 − 2`, minimum 1.

### 12. Bases (resolved in this order because of exclusions)

- **Naval**: only if Starport is A or B; then `2D6 ≥ 8`.
- **Scout**: only if Starport is not E or X; then `2D6 ≥ 7` with DM −1 (C), −2 (B), −3 (A).
- **Pirate**: only if Starport is not A **and** no naval base; then `2D6 ≥ 12`.
- Reduce to a base code: A = Naval+Scout, N = Naval, S = Scout, P = Pirate, G = Scout+Pirate.
  (No SRD code for Naval+Pirate—the pirate exclusion against a naval base makes it impossible.)

### 13. Trade codes—deterministic from the UWP (UWP Values for Trade Codes table)

Each classification tests a conjunction of ranges over the eight UWP fields; assign every code whose
conditions all hold. Codes: Ag, As, Ba, De, Fl, Ga, Hi, Ht, Ic, In, Lo, Lt, Na, Ni, Po, Ri, Wa, Va.
(Full condition set goes in `tables.py`; e.g. **Ag**: Atmosphere 4–9, Hydro 4–8, Pop 5–7.)

### 14. Travel Zone

- **Amber** candidate (rule-driven, in scope): Atmosphere ≥ 10, or Government ∈ {0, 7, 10}, or
  Law Level ∈ {0, 9+}.
- **Red**: referee discretion only—out of automated scope; caller may set it explicitly.

### 15. Subsector / star mapping

- Grid is 8 columns × 10 rows (80 hexes). Hex coordinate is `CCRR` (2-digit column, 2-digit row).
- Per-hex presence: `1D6 ≥ 4` at default density; density DM applied to the die: rift −2, sparse −1,
  dense +1. Each occupied hex gets a full system.

### 16. Allegiance

- Systems belong to a polity; default `Na` (non-aligned). Polity boundaries are referee discretion
  (out of scope); the caller may supply an allegiance.

---

## Part B—Design decisions

### D1: Domain lives in an `engine/worlds/` subpackage

- **Decision**: New subpackage `src/cetools/engine/worlds/` with `tables`, `models`, `generator`,
  `naming`, `profile` modules and a public `__init__.py`.
- **Rationale**: Mirrors the existing `careers/` package; namespaces five distinct concerns; keeps
  the engine root uncluttered. `check_docs.py` only enforces top-level `engine/*.py` in the module
  map, so subpackage modules add no map churn.
- **Alternatives**: Flat `world_*.py` modules (rejected—prefix noise, larger map diagram); a
  single `worlds.py` (rejected—mixes static tables, models, rules, and rendering in one file).

### D2: All chance flows through the existing `Rolls` seam

- **Decision**: Reuse `Rolls`/`RandomRolls`/`ScriptedRolls`. Add world `RollName` members. The
  engine computes its own DMs and does arithmetic on `two_d6()`/`d6()` totals; `check(dm, target,
  name)` is used for the pure "2D6 + DM ≥ target" base/presence rolls.
- **Rationale**: Satisfies FR-022 (seeded reproducibility) for free and lets tests pin every
  probabilistic rule with `ScriptedRolls`. Consistent with how careers/skills already work.
- **Note on 1D6 presence checks**: World-presence (`1D6 + density ≥ 4`) and belt/gas-giant *counts*
  use `d6()` plus in-engine arithmetic, because `check()` is defined over 2D6. This keeps the seam
  pure (it knows chance, not the specific die math).
- **New `RollName` members**: `WORLD_SIZE`, `WORLD_ATMOSPHERE`, `WORLD_HYDROGRAPHICS`,
  `WORLD_POPULATION`, `WORLD_GOVERNMENT`, `WORLD_LAW_LEVEL`, `WORLD_STARPORT`, `WORLD_TECH_LEVEL`,
  `POPULATION_MODIFIER`, `PLANETOID_BELT_PRESENCE`, `PLANETOID_BELT_COUNT`, `GAS_GIANT_PRESENCE`,
  `GAS_GIANT_COUNT`, `NAVAL_BASE`, `SCOUT_BASE`, `PIRATE_BASE`, `WORLD_PRESENCE`, `WORLD_NAME_STEM`.

### D3: SRD tables are data, not code (Principle V)

- **Decision**: `tables.py` holds every table as a plain data structure—sequences and dicts of
  tuples/ranges/DMs (e.g. `STARPORT_BY_ROLL`, `TL_DM_BY_VALUE`, `TL_MINIMUMS`, `TRADE_CODES`,
  `GOVERNMENT_TYPES`, `LAW_LEVELS`, `SIZE_DESCRIPTIONS`, `ATMOSPHERE_DESCRIPTIONS`).
- **Rationale**: The generator reads tables generically; correcting or extending a table needs no
  logic change. Trade-code rules are expressed as predicates-as-data (per-field range sets) so the
  matcher loops over them uniformly.

### D4: World naming—hybrid stem generator (clarified: method C)

- **Decision**: `naming.py` holds a curated pool of pronounceable stems (syllable fragments). A name
  is assembled by choosing 2–3 stems via `rolls.choose(..., WORLD_NAME_STEM)` and title-casing the
  result. `generate_world_name(rolls)` returns one name.
- **Rationale**: A hybrid stem pool yields effectively unlimited, pronounceable, invented names—a
  fixed word list would repeat visibly across a ~40-world subsector. Matches the sci-fi convention
  and the workload-reduction goal. Reproducible through the seam.
- **Uniqueness (clarified: A)**: The *subsector* generator enforces per-subsector uniqueness by
  regenerating on collision, bounded by a max-attempts guard (mirroring the existing
  `_MAX_QUALIFICATION_ATTEMPTS` pattern) so an exhausted pool fails fast rather than looping forever.
  Single-world/system generation does not dedupe (there is nothing to collide with).
- **Override**: `name` is an optional parameter on `generate_world`/`generate_system`; when given it
  is used verbatim and skips generation (and does not participate in uniqueness regeneration).

### D5: Rendering lives in `worlds/profile.py`, reusing `pseudohex`

- **Decision**: `profile.py` renders the classic profile string (`A867A9C-F`) and the full
  world-data line. UWP digits (values 0–15) render via the existing
  `pseudohex.to_pseudohex`/`from_pseudohex` (valid over 0–33). Starport class is a literal letter.
- **Rationale**: Reuses the project's canonical pseudo-hex codec; keeps rendering out of the models
  and out of the CLI (Principle III). The existing `formatter.py` handles characters and is left
  untouched.
- **Full line format** (fields separated by single spaces, blanks preserved for absent base/zone):
  `Name  CCRR  A867A9C-F  N  Ag Ni  A  234  Na` → name, hex, profile, base code, trade codes/remarks,
  travel-zone code, PBG triple, allegiance.

### D6: CLI surface—`cetools world`

- **Decision**: `cli/world.py` defines a Typer sub-app registered in `main.py`. Commands:
  `cetools world generate` (single world/system) and `cetools world subsector`. Options include
  `--name`, `--count`, `--seed`, `--allegiance`, and `--density` (subsector). Pure I/O routing.
- **Rationale**: Matches the `cetools character generate` pattern. `--seed` exposes FR-022 to users.
- **Alternatives**: A single flat command with a `--subsector` flag (rejected—two clearly distinct
  outputs read better as two subcommands).

### D7: Reproducibility entry point

- **Decision**: Engine functions accept `rolls: Rolls | None = None`, defaulting to `RandomRolls()`.
  The CLI builds `RandomRolls(random.Random(seed))` when `--seed` is supplied.
- **Rationale**: Same seed → identical world/system/subsector (FR-022, SC-005), while unseeded use
  stays convenient. Mirrors `generator.generate`'s default-rolls approach.
