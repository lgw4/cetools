<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Colonist

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`colonist.toml`) | Verdict |
|---|---|---|---|
| Display name | Colonist | Colonist | match |
| Qualification | End 5+ | END 5+ | match |
| Survival | End 6+ | END 6+ | match |
| Commission | Int 7+ | INT 7+ | match |
| Advancement (promotion) | Edu 6+ | EDU 6+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | (fringe career, per R6) | fringe | match |
| Always-available | not stated | absent (false) | match |
| Re-enterable | not stated | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | +1 Int | INT +1 | match |
| Personal row 5 | Athletics | Athletics | match |
| Personal row 6 | Gun Combat | Gun Combat | match |
| Service row 1 | Mechanics | Mechanics | match |
| Service row 2 | Gun Combat | Gun Combat | match |
| Service row 3 | Animals | Animals | match |
| Service row 4 | Electronics | Electronics | match |
| Service row 5 | Survival | Survival | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Athletics | Athletics | match |
| Specialist row 2 | Carousing | Carousing | match |
| Specialist row 3 | Jack o' Trades | Jack-of-All-Trades | match (FR-017a: normalized to the canonical form the skill chapter's own heading sanctions) |
| Specialist row 4 | Engineering | Engineering | match |
| Specialist row 5 | Animals | Animals | match |
| Specialist row 6 | Vehicle | Vehicle | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Linguistics | Computer | **corrected** |
| Advanced-education row 3 | Medicine | Medicine | match |
| Advanced-education row 4 | Liaison | Liaison | match |
| Advanced-education row 5 | Admin | Admin | match |
| Advanced-education row 6 | Animals | Animals | match |
| Rank 0 title | Citizen | Citizen | match |
| Rank 0 grant | Survival-1 | Survival 1 | match |
| Rank 1 title | District Leader | District Leader | match |
| Rank 1 grant | (none) | (none) | match |
| Rank 2 title | District Delegate | District Delegate | match |
| Rank 2 grant | (none) | (none) | match |
| Rank 3 title | Council Advisor | Council Advisor | match |
| Rank 3 grant | Liaison-1 | Liaison 1 | match |
| Rank 4 title | Councilor | Councilor | match |
| Rank 4 grant | (none) | (none) | match |
| Rank 5 title | Lieutenant Governor | Lieutenant Governor | match |
| Rank 5 grant | (none) | (none) | match |
| Rank 6 title | Governor | Governor | match |
| Rank 6 grant | (none) | (none) | match |
| Cash row 1 | 1,000 | 1000 | match |
| Cash row 2 | 5,000 | 5000 | match |
| Cash row 3 | 5,000 | 5000 | match |
| Cash row 4 | 5,000 | 5000 | match |
| Cash row 5 | 10,000 | 10000 | match |
| Cash row 6 | 20,000 | 20000 | match |
| Cash row 7 | 50,000 | 50000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Mid Passage | Mid Passage | match |
| Material row 5 | Mid Passage | Mid Passage | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | +1 Soc | SOC +1 | match |

## Notes

One correction found: the Advanced Education table's row 2 is "Linguistics" in the source, not
"Computer". Confirmed by two independent fetches (a full-table read, then a targeted single-field
re-check naming the other five rows and asking specifically for row 2).

Everything else matches, including the rank 3 title correction ("Liaision" → "Liaison") this
feature's transcription pass already applied — the source's own printed form is the misprint
"Liaision", which the file correctly departs from and notes.
