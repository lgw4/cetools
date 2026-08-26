<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Drifter

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`drifter.toml`) | Verdict |
|---|---|---|---|
| Display name | Drifter | Drifter | match |
| Qualification | Dex 5+ | DEX 5+ | match |
| Survival | End 5+ | END 5+ | match |
| Commission | none | absent | match |
| Advancement (promotion) | none | absent | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | (fringe career, per R6) | fringe | match |
| Always-available | "the Drifter career is always open" | `always-available = true` | match |
| Re-enterable | "you can be Drafted into a career you were previously in but got ejected from" is the Draft's own exception; the Drifter career itself is the other named exception to "once you leave a career you cannot return to it" | `re-enterable = true` | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | Melee Combat | Melee Combat | match |
| Personal row 5 | Bribery | Bribery | match |
| Personal row 6 | Gambling | Gambling | match |
| Service row 1 | Streetwise | Streetwise | match |
| Service row 2 | Mechanics | Mechanics | match |
| Service row 3 | Gun Combat | Gun Combat | match |
| Service row 4 | Melee Combat | Melee Combat | match |
| Service row 5 | Recon | Recon | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Electronics | Electronics | match |
| Specialist row 2 | Melee Combat | Melee Combat | match |
| Specialist row 3 | Bribery | Bribery | match |
| Specialist row 4 | Streetwise | Streetwise | match |
| Specialist row 5 | Gambling | Gambling | match |
| Specialist row 6 | Recon | Recon | match |
| Advanced-education row 1 | Computer | Computer | match |
| Advanced-education row 2 | Engineering | Engineering | match |
| Advanced-education row 3 | Jack o' Trades | Jack-of-All-Trades | match (FR-017a: canonical form) |
| Advanced-education row 4 | Medicine | Medicine | match |
| Advanced-education row 5 | Liaison | Liaison | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | (none) | (none) | match |
| Rank 0 grant | (none) | (none) | match |
| Ranks 1-6 | "no rank titles or progression"; blank throughout | one entry ladder, rank 0 only | match |
| Cash row 1 | 0 | 0 | match |
| Cash row 2 | 1,000 | 1000 | match |
| Cash row 3 | 2,000 | 2000 | match |
| Cash row 4 | 5,000 | 5000 | match |
| Cash row 5 | 5,000 | 5000 | match |
| Cash row 6 | 10,000 | 10000 | match |
| Cash row 7 | 10,000 | 10000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Weapon | Weapon | match |
| Material row 5 | Mid Passage | Mid Passage | match |
| Material row 6 | Mid Passage | Mid Passage | match |
| Material row 7 | — (dash) | absent (6-row table) | match |

## Notes

No discrepancies found. `always-available` and `re-enterable` are confirmed directly from the
narrative text, not inferred from the career table alone: "Once you leave a career you cannot
return to it. The Draft and the Drifter career are exceptions to this rule ... the Drifter career
is always open."
