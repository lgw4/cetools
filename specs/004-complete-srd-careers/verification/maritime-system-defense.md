<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Maritime System Defense

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`maritime-system-defense.toml`) | Verdict |
|---|---|---|---|
| Display name | Maritime Defense (long form: Maritime System Defense, per the career-descriptions list, FR-005) | Maritime System Defense | match |
| Qualification | End 5+ | END 5+ | match |
| Survival | End 5+ | END 5+ | match |
| Commission | Int 6+ | INT 6+ | match |
| Advancement (promotion) | Edu 7+ | EDU 7+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | Tier 1 (75% at 4+, 100% at 8+) — grouped with Aerospace System Defense, Marine, Navy, Scout, Surface System Defense | service | match |
| Always-available | not named for this career | absent (false) | match |
| Re-enterable | not named for this career | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | Athletics | Athletics | match |
| Personal row 5 | Melee Combat | Melee Combat | match |
| Personal row 6 | Vehicle | Vehicle | match |
| Service row 1 | Mechanics | Mechanics | match |
| Service row 2 | Gun Combat | Gun Combat | match |
| Service row 3 | Gunnery | Gunnery | match |
| Service row 4 | Melee Combat | Melee Combat | match |
| Service row 5 | Survival | Survival | match |
| Service row 6 | Watercraft | Watercraft | match |
| Specialist row 1 | Comms | Comms | match |
| Specialist row 2 | Electronics | Electronics | match |
| Specialist row 3 | Gun Combat | Gun Combat | match |
| Specialist row 4 | Demolitions | Demolitions | match |
| Specialist row 5 | Recon | Recon | match |
| Specialist row 6 | Watercraft | Watercraft | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Jack o' Trades (canonical form `Jack-of-All-Trades`, R4) | Jack-of-All-Trades | match |
| Advanced-education row 4 | Medicine | Medicine | match |
| Advanced-education row 5 | Leadership | Leadership | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | Seaman | Seaman | match |
| Rank 0 grant | Watercraft-1 | Watercraft 1 | match |
| Rank 1 title | Ensign | Ensign | match |
| Rank 1 grant | none | none | match |
| Rank 2 title | Lieutenant | Lieutenant | match |
| Rank 2 grant | none | none | match |
| Rank 3 title | Lt Commander | Lt Commander | match |
| Rank 3 grant | Leadership-1 | Leadership 1 | match |
| Rank 4 title | Commander | Commander | match |
| Rank 4 grant | none | none | match |
| Rank 5 title | Captain | Captain | match |
| Rank 5 grant | none | none | match |
| Rank 6 title | Admiral | Admiral | match |
| Rank 6 grant | none | none | match |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 10000 | 10000 | match |
| Cash row 4 | 10000 | 10000 | match |
| Cash row 5 | 20000 | 20000 | match |
| Cash row 6 | 50000 | 50000 | match |
| Cash row 7 | 50000 | 50000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Edu | EDU +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Mid Passage | Mid Passage | match |
| Material row 5 | Weapon | Weapon | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | +1 Soc | SOC +1 | match |

## Notes

Two independent fetches (a full-table request, then a targeted medical-tier-groupings
request covering all twenty-four careers at once) agree on every field. No corrections
or deviations found; this file was already reconciled correctly in Phase 6c (T071).
