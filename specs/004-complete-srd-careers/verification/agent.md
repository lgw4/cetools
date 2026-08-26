<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Agent

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`agent.toml`) | Verdict |
|---|---|---|---|
| Display name | Agent | Agent | match |
| Qualification | Soc 6+ | SOC 6+ | match |
| Survival | Int 6+ | INT 6+ | match |
| Commission | Edu 7+ | EDU 7+ | match |
| Advancement (promotion) | Edu 6+ | EDU 6+ | match |
| Re-enlistment | 6+ | 6+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | 50%/75%/100% bracket ("professional") | professional | match |
| Always-available | not stated | (absent, default false) | match |
| Re-enterable | not stated | (absent, default false) | match |
| Personal row 1 | +1 Dex | DEX +1 | match |
| Personal row 2 | +1 End | END +1 | match |
| Personal row 3 | +1 Int | INT +1 | match |
| Personal row 4 | +1 Edu | EDU +1 | match |
| Personal row 5 | Athletics | Athletics | match |
| Personal row 6 | Carousing | Carousing | match |
| Service row 1 | Admin | Admin | match |
| Service row 2 | Computer | Computer | match |
| Service row 3 | Streetwise | Streetwise | match |
| Service row 4 | Bribery | Bribery | match |
| Service row 5 | Leadership | Leadership | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Gun Combat | Gun Combat | match |
| Specialist row 2 | Melee Combat | Melee Combat | match |
| Specialist row 3 | Bribery | Bribery | match |
| Specialist row 4 | Leadership | Leadership | match |
| Specialist row 5 | Recon | Recon | match |
| Specialist row 6 | Survival | Survival | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Liaison | Liaison | match |
| Advanced-education row 4 | Linguistics | Linguistics | match |
| Advanced-education row 5 | Medicine | Medicine | match |
| Advanced-education row 6 | Leadership | Leadership | match |
| Rank 0 title | Agent | Agent | match |
| Rank 0 grant | Streetwise-1 | Streetwise 1 | match |
| Rank 1 title | Special Agent | Special Agent | match |
| Rank 1 grant | (none) | (none) | match |
| Rank 2 title | Sp Agent in Charge | Sp Agent in Charge | match |
| Rank 2 grant | (none) | (none) | match |
| Rank 3 title | Unit Chief | Unit Chief | match |
| Rank 3 grant | (none) | (none) | match |
| Rank 4 title | Section Chief | Section Chief | match |
| Rank 4 grant | Admin-1 | Admin 1 | match |
| Rank 5 title | Assistant Directory (misprint) | Assistant Director | match (already corrected, FR-017/D9) |
| Rank 5 grant | (none) | (none) | match |
| Rank 6 title | Director | Director | match |
| Rank 6 grant | (none) | (none) | match |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 10000 | 10000 | match |
| Cash row 4 | 10000 | 10000 | match |
| Cash row 5 | 20000 | 20000 | match |
| Cash row 6 | 50000 | 50000 | match |
| Cash row 7 | 50000 | 50000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Mid Passage | Mid Passage | match |
| Material row 5 | +1 Soc | SOC +1 | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | Explorers' Society | Explorers' Society | match |

## Notes

Everything checked in this fresh fetch matches the committed file, including the already-recorded
correction at rank 5 (the source's own misprint "Assistant Directory" for "Assistant Director",
already noted in `agent.toml`'s header comment per FR-017/D9). No new discrepancies found.
