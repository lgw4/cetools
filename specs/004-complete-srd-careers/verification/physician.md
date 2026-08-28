<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Physician

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`physician.toml`) | Verdict |
|---|---|---|---|
| Display name | Physician | Physician | match |
| Qualification | Edu 6+ | EDU 6+ | match |
| Survival | Int 4+ | INT 4+ | match |
| Commission | Int 5+ | INT 5+ | match |
| Advancement (promotion) | Edu 8+ | EDU 8+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | Tier 2 (50% at 4+, 75% at 8+) | professional | match |
| Always-available | not named for this career | absent (false) | match |
| Re-enterable | not named for this career | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | +1 Int | INT +1 | match |
| Personal row 5 | +1 Edu | EDU +1 | match |
| Personal row 6 | Gun Combat | Gun Combat | match |
| Service row 1 | Admin | Admin | match |
| Service row 2 | Computer | Computer | match |
| Service row 3 | Mechanics | Mechanics | match |
| Service row 4 | Medicine | Medicine | match |
| Service row 5 | Leadership | Leadership | match |
| Service row 6 | Sciences | Sciences | match |
| Specialist row 1 | Computer | Computer | match |
| Specialist row 2 | Carousing | Carousing | match |
| Specialist row 3 | Electronics | Electronics | match |
| Specialist row 4 | Medicine | Medicine | match |
| Specialist row 5 | Medicine | Medicine | match |
| Specialist row 6 | Sciences | Sciences | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Jack o' Trades (canonical `Jack-of-All-Trades`) | Jack-of-All-Trades | match |
| Advanced-education row 4 | Linguistics | Linguistics | match |
| Advanced-education row 5 | Medicine | Medicine | match |
| Advanced-education row 6 | Sciences | Sciences | match |
| Rank 0 title | Intern | Intern | match |
| Rank 0 grant | Medicine-1 | Medicine 1 | match |
| Rank 1 title | Resident | Resident | match |
| Rank 1 grant | none | none | match |
| Rank 2 title | Senior Resident | Senior Resident | match |
| Rank 2 grant | none | none | match |
| Rank 3 title | Chief Resident | Chief Resident | match |
| Rank 3 grant | none | none | match |
| Rank 4 title | Attending Phys. (verbatim abbreviation) | Attending Phys. | match |
| Rank 4 grant | Admin-1 | Admin 1 | match |
| Rank 5 title | Service Chief | Service Chief | match |
| Rank 5 grant | none | none | match |
| Rank 6 title | Hospital Admin. (verbatim abbreviation) | Hospital Admin. | match |
| Rank 6 grant | none | none | match |
| Cash row 1 | 2000 | 2000 | match |
| Cash row 2 | 10000 | 10000 | match |
| Cash row 3 | 20000 | 20000 | match |
| Cash row 4 | 20000 | 20000 | match |
| Cash row 5 | 50000 | 50000 | match |
| Cash row 6 | 100000 | 100000 | match |
| Cash row 7 | 100000 | 100000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Edu | EDU +1 | match |
| Material row 3 | +1 Int | INT +1 | match |
| Material row 4 | High Passage | High Passage | match |
| Material row 5 | Explorers' Society | Explorers' Society | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | +1 Soc | SOC +1 | match |

## Notes

Full match on the first fetch, including the two verbatim abbreviated rank titles
("Attending Phys.", "Hospital Admin.") the committed file's header comment already
calls out as printed that way in the source rather than as a transcription shorthand.
No corrections or deviations found.
