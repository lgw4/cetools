<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Scout

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html
and https://evolvedexperiment.github.io/cepheus-srd/skills.html, independent of this feature's
transcription pass, per spec.md FR-023.

| Field | Source | Committed (`scout.toml`) | Verdict |
|---|---|---|---|
| Display name | Scout | Scout | match |
| Qualification | Int 6+ | INT 6+ | match |
| Survival | End 7+ | END 7+ | match |
| Commission | none | (absent) | match |
| Advancement (promotion) | none | (absent) | match |
| Re-enlistment | 6+ | 6+ | match |
| Advanced-education gate | Education 8+ (FR-004 uniform rule) | EDU 8+ | match |
| Medical tier | service (75%/100%) | service | match |
| Always-available | not stated | (absent) | match |
| Re-enterable | not stated (only Draft/Drifter are the general exceptions) | (absent) | match |
| Personal 1 | +1 Str | STR +1 | match |
| Personal 2 | +1 Dex | DEX +1 | match |
| Personal 3 | +1 End | END +1 | match |
| Personal 4 | Jack o' Trades | Jack-of-All-Trades | match (canonical form, FR-017a normalization) |
| Personal 5 | +1 Edu | EDU +1 | match |
| Personal 6 | Melee Combat | Melee Combat | match |
| Service 1 | Comms | Comms | match |
| Service 2 | Electronics | Electronics | match |
| Service 3 | Gun Combat | Gun Combat | match |
| Service 4 | Gunnery | Gunnery | match |
| Service 5 | Recon | Recon | match |
| Service 6 | Piloting | Piloting | match |
| Specialist 1 | Engineering | Engineering | match |
| Specialist 2 | Gunnery | Gunnery | match |
| Specialist 3 | Demolitions | Demolitions | match |
| Specialist 4 | Navigation | Navigation | match |
| Specialist 5 | Medicine | Medicine | match |
| Specialist 6 | Vehicle | Vehicle | match |
| Adv. Education 1 | Advocate | Advocate | match |
| Adv. Education 2 | Computer | Computer | match |
| Adv. Education 3 | Linguistics | Linguistics | match |
| Adv. Education 4 | Medicine | Medicine | match |
| Adv. Education 5 | Navigation | Navigation | match |
| Adv. Education 6 | Tactics | Tactics | match |
| Rank 0 title | (blank — no title printed) | (absent) | match |
| Rank 0 grant | Pilot-1 (misspelling; skills.html defines "Piloting", never "Pilot") | Piloting 1 | match (FR-017 correction, already applied and confirmed) |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 10000 | 10000 | match |
| Cash row 4 | 10000 | 10000 | match |
| Cash row 5 | 20000 | 20000 | match |
| Cash row 6 | 50000 | 50000 | match |
| Cash row 7 | 50000 | 50000 | match |
| Material 1 | Low Passage | Low Passage | match |
| Material 2 | +1 Edu | EDU +1 | match |
| Material 3 | Weapon | Weapon | match |
| Material 4 | Mid Passage | Mid Passage | match |
| Material 5 | Explorers' Society | Explorers' Society | match |
| Material 6 | Courier Vessel | Courier Vessel | match |
| Material 7 | — (dash, no item) | (row omitted; file carries 6 rows) | match |

## Notes

Scout's rank 0 grant was independently re-verified against skills.html, which defines a skill
named "Piloting" and no skill named "Pilot" — confirming the file's existing FR-017 correction
note (from an earlier phase of this same feature) is itself correct, not merely asserted.

No new corrections or deviations found for this career.
