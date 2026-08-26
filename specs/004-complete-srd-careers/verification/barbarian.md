<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Barbarian

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`barbarian.toml`) | Verdict |
|---|---|---|---|
| Display name | Barbarian | Barbarian | match |
| Qualification | End 5+ | END 5+ | match |
| Survival | Str 6+ | STR 6+ | match |
| Commission | none (dash) | (absent) | match |
| Advancement (promotion) | none (dash) | (absent) | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | 0%/50%/75% bracket ("fringe") | fringe | match |
| Always-available | not stated | (absent, default false) | match |
| Re-enterable | not stated | (absent, default false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | +1 Int | INT +1 | match |
| Personal row 5 | Athletics | Athletics | match |
| Personal row 6 | Gun Combat | Gun Combat | match |
| Service row 1 | Gun Combat | Gun Combat | **corrected**: same, `Gun Combat` (single, not repeated) |
| Service row 2 | Melee Combat | Gun Combat | **corrected**: `Melee Combat` |
| Service row 3 | Recon | Melee Combat | **corrected**: `Recon` |
| Service row 4 | Survival | Recon | **corrected**: `Survival` |
| Service row 5 | Animals | Survival | **corrected**: `Animals` |
| Service row 6 | Vehicle | Animals | **corrected**: `Vehicle` |
| Specialist row 1 | Gun Combat | Gun Combat | match |
| Specialist row 2 | Jack o' Trades (→ Jack-of-All-Trades) | Jack-of-All-Trades | match |
| Specialist row 3 | Melee Combat | Melee Combat | match |
| Specialist row 4 | Recon | Recon | match |
| Specialist row 5 | Animals | Animals | match |
| Specialist row 6 | Tactics | Tactics | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Linguistics | Linguistics | match |
| Advanced-education row 3 | Medicine | Medicine | match |
| Advanced-education row 4 | Leadership | Leadership | match |
| Advanced-education row 5 | Broker | Broker | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | (none) | (none) | match |
| Rank 0 grant | Melee Combat-1 | Melee Combat 1 | match |
| Cash row 1 | 0 | 0 | match |
| Cash row 2 | 1000 | 1000 | match |
| Cash row 3 | 2000 | 2000 | match |
| Cash row 4 | 5000 | 5000 | match |
| Cash row 5 | 5000 | 5000 | match |
| Cash row 6 | 10000 | 10000 | match |
| Cash row 7 | 10000 | 10000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Weapon | Mid Passage | **corrected**: `Weapon` |
| Material row 5 | +1 End | END +1 | match |
| Material row 6 | Mid Passage | Mid Passage | match |
| Material row 7 | dash (no benefit) | (row absent, 6-row table) | match |

## Notes

Two genuine findings, each cross-checked at least twice before recording:

- **Service table**: four independent fetches were needed to settle this field. The first
  full-table fetch returned `Gun Combat, Melee Combat, Recon, Survival, Animals, Mechanics`; a
  second, more explicit request returned the same first five rows but `Vehicle` for row 6; a
  targeted single-row fetch degenerated into repeating `Animals`; a fourth, narrowly-scoped fetch
  confirmed `Vehicle` again. Two of three coherent answers agree on `Vehicle`, and all four agree
  the committed file's repeated `Gun Combat, Gun Combat` at rows 1-2 is wrong — no fetch ever
  reproduced that repeat. Recorded as corrected to
  `["Gun Combat", "Melee Combat", "Recon", "Survival", "Animals", "Vehicle"]`, with the caveat that
  this field's fetch instability was higher than any other field re-read across this batch and a
  future re-check would not be wasted effort.
- **Material row 4**: two independent fetches (a full-table read and a single-row targeted
  re-check) both give `Weapon`, not the committed file's `Mid Passage`. Corrected.

Every other field matches the committed file exactly.
