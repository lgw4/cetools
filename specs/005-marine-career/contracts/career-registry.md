# Contract: Career Registry & Draft Table (Marine addition)

**Scope**: `src/cetools/engine/careers/registry.py` — `CAREER_REGISTRY` and `DRAFT_TABLE`.

This document defines the contract change for adding Marine to the registry and draft table.
The `--career` CLI flag's own contract (normalization, "did you mean", help text, error
formatting) is unchanged from
[`specs/003-aerospace-system-defense-career/contracts/cli-career-flag.md`](../../003-aerospace-system-defense-career/contracts/cli-career-flag.md)
— it is registry-derived and automatically picks up Marine with no code change.

---

## CAREER_REGISTRY

| Key | Career | Status |
|-----|--------|--------|
| `"aerospace system defense"` | `AEROSPACE_CAREER` | unchanged |
| `"marine"` | `MARINE_CAREER` | **NEW** |
| `"navy"` | `NAVY_CAREER` | unchanged |
| `"scout"` | `SCOUT_CAREER` | unchanged |

**Guarantee**: `CAREER_REGISTRY["marine"] is MARINE_CAREER` and `MARINE_CAREER.name == "Marine"`.

---

## DRAFT_TABLE

`draft_character()` indexes `DRAFT_TABLE[roll - 1]` for a 1D6 roll.

| Index | Roll | Career key | Status |
|-------|------|-----------|--------|
| 0 | 1 | `"aerospace system defense"` | unchanged |
| 1 | 2 | `"marine"` | **NEW** (was `"navy"` placeholder) |
| 2 | 3 | `"navy"` | unchanged (Maritime System Defense not yet implemented) |
| 3 | 4 | `"navy"` | unchanged |
| 4 | 5 | `"scout"` | unchanged |
| 5 | 6 | `"navy"` | unchanged (Surface System Defense not yet implemented) |

**Guarantee**: A draft roll of 2 resolves to `MARINE_CAREER` via
`CAREER_REGISTRY[DRAFT_TABLE[1]]`, and the resulting `Character.drafted` is `True`.

---

## Unrecognized Career Error (updated valid-careers list)

With Marine registered, the CLI's "no close match" error message now lists four names in
sorted order:

```
Unknown career '<input>'. Valid careers: Aerospace System Defense, Marine, Navy, Scout
```

**Example**: `--career "merchant"` (unregistered, no close match to any of the four keys)

```
Unknown career 'merchant'. Valid careers: Aerospace System Defense, Marine, Navy, Scout
```

`--career --help` text is derived from the same sorted list and updates automatically.
