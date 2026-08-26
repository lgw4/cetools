<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Athlete

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`athlete.toml`) | Verdict |
|---|---|---|---|
| Display name | Athlete | Athlete | match |
| Qualification | End 8+ | END 8+ | match |
| Survival | Dex 5+ | DEX 5+ | match |
| Commission | none (dash) | (absent) | match |
| Advancement (promotion) | none (dash) | (absent) | match |
| Re-enlistment | 6+ | 6+ | match |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | 50%/75%/100% bracket ("professional") | professional | match |
| Always-available | not stated | (absent, default false) | match |
| Re-enterable | not stated | (absent, default false) | match |
| Personal row 1 | +1 Dex | DEX +1 | match |
| Personal row 2 | +1 Int | INT +1 | match |
| Personal row 3 | +1 Edu | EDU +1 | match |
| Personal row 4 | +1 Soc | SOC +1 | match |
| Personal row 5 | Carousing | Carousing | match |
| Personal row 6 | Melee Combat | Melee Combat | match |
| Service row 1 | Athletics | Athletics | match |
| Service row 2 | Admin | Admin | match |
| Service row 3 | Carousing | Carousing | match |
| Service row 4 | Computer | Computer | match |
| Service row 5 | Gambling | Gambling | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Zero-G | Zero-G | match |
| Specialist row 2 | Athletics | Athletics | match |
| Specialist row 3 | Athletics | Athletics | match |
| Specialist row 4 | Computer | Computer | match |
| Specialist row 5 | Leadership | Leadership | match |
| Specialist row 6 | Gambling | Gambling | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Liaison | Liaison | match |
| Advanced-education row 4 | Linguistics | Linguistics | match |
| Advanced-education row 5 | Medicine | Medicine | match |
| Advanced-education row 6 | Sciences | Sciences | match |
| Rank 0 title | (none) | (none) | match |
| Rank 0 grant | Athletics-1 (confirmed by a targeted re-check after a first pass mis-read it as blank) | Athletics 1 | match |
| Cash row 1 | 2000 | 2000 | match |
| Cash row 2 | 10000 | 10000 | match |
| Cash row 3 | 20000 | 20000 | match |
| Cash row 4 | 20000 | 20000 | match |
| Cash row 5 | 50000 | 50000 | match |
| Cash row 6 | 100000 | 100000 | match |
| Cash row 7 | 100000 | 100000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | High Passage | High Passage | match |
| Material row 5 | Explorers' Society | Explorers' Society | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | dash (no benefit) | (row absent, 6-row table) | match |

## Notes

A first full-table fetch reported rank 0 as carrying no bonus at all, which would have contradicted
the committed file. A targeted single-fact re-check, asked to look carefully at rank 0's cell
specifically, confirmed the bracketed grant `[Athletics-1]` is in fact printed there — the same
fetch-instability this project's earlier transcription pass already ran into for this exact field
(recorded in this feature's working history). No discrepancies survive against the committed file.
