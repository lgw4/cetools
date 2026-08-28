<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Pirate

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html
and https://evolvedexperiment.github.io/cepheus-srd/skills.html, independent of this feature's
transcription pass, per spec.md FR-023.

| Field | Source | Committed (`pirate.toml`) | Verdict |
|---|---|---|---|
| Display name | Pirate | Pirate | match |
| Qualification | Dex 5+ | DEX 5+ | match |
| Survival | Dex 6+ | DEX 6+ | match |
| Commission | Str 7+ | STR 7+ | match |
| Advancement (promotion) | Int 6+ | INT 6+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ (FR-004 uniform rule) | EDU 8+ | match |
| Medical tier | professional (50%/75%/100%) | professional | match |
| Always-available | not stated | (absent) | match |
| Re-enterable | not stated (only the Draft/Drifter exceptions apply generally) | (absent) | match |
| Personal 1 | +1 Str | STR +1 | match |
| Personal 2 | +1 Dex | DEX +1 | match |
| Personal 3 | +1 End | END +1 | match |
| Personal 4 | Melee Combat | Melee Combat | match |
| Personal 5 | Bribery | Bribery | match |
| Personal 6 | Gambling | Gambling | match |
| Service 1 | Streetwise | Streetwise | match |
| Service 2 | Electronics | Electronics | match |
| Service 3 | Gun Combat | Gun Combat | match |
| Service 4 | Melee Combat | Melee Combat | match |
| Service 5 | Recon | Recon | match |
| Service 6 | Vehicle | Vehicle | match |
| Specialist 1 | Zero-G | Zero-G | match |
| Specialist 2 | Comms | Comms | match |
| Specialist 3 | Engineering | Engineering | match |
| Specialist 4 | Gunnery | Gunnery | match |
| Specialist 5 | Navigation | Navigation | match |
| Specialist 6 | Piloting | Piloting | match |
| Adv. Education 1 | Computer | Computer | match |
| Adv. Education 2 | Gravitics | Gravitics | match |
| Adv. Education 3 | Jack o' Trades | Jack-of-All-Trades | match (canonical form, FR-017a normalization) |
| Adv. Education 4 | Medicine | Medicine | match |
| Adv. Education 5 | Advocate | Advocate | match |
| Adv. Education 6 | Tactics | Tactics | match |
| Rank 0 title | Crewman | Crewman | match |
| Rank 0 grant | Gunnery-1 | Gunnery 1 | match |
| Rank 1 title | Corporal | Corporal | match |
| Rank 1 grant | (none) | (absent) | match |
| Rank 2 title | Lieutenant | Lieutenant | match |
| Rank 2 grant | Pilot-1 (misspelling; source's skill chapter defines "Piloting", never "Pilot") | Piloting 1 | match (FR-017 correction, already applied and confirmed) |
| Rank 3 title | Lt Commander | Lt Commander | match |
| Rank 3 grant | (none) | (absent) | match |
| Rank 4 title | Commander | Commander | match |
| Rank 4 grant | (none) | (absent) | match |
| Rank 5 title | Captain | Captain | match |
| Rank 5 grant | (none) | (absent) | match |
| Rank 6 title | Commodore | Commodore | match |
| Rank 6 grant | (none) | (absent) | match |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 10000 | 10000 | match |
| Cash row 4 | 20000 | 20000 | match |
| Cash row 5 | 20000 | 20000 | match |
| Cash row 6 | 50000 | 50000 | match |
| Cash row 7 | 100000 | 100000 | match |
| Material 1 | Low Passage | Low Passage | match |
| Material 2 | +1 Int | INT +1 | match |
| Material 3 | Weapon | Weapon | match |
| Material 4 | High Passage | High Passage | match |
| Material 5 | +1 Soc | SOC +1 | match |
| Material 6 | High Passage | High Passage | match |
| Material 7 | 1D6 Ship Shares | 1d6 Ship Share | match (FR-011/FR-015a quantified-benefit notation) |

## Notes

The first Advanced Education fetch returned a duplicate "Advocate" for row 1, contradicting the
committed file's "Computer"; a second, narrower fetch asking only for that table, one row per
line, returned Computer/Gravitics/Jack o' Trades/Medicine/Advocate/Tactics, confirming the
duplicate was a fetch artifact and the committed file is correct.

Rank 2's grant was independently re-verified against skills.html, which defines a skill named
"Piloting" and no skill named "Pilot" — confirming the file's existing FR-017 correction note is
itself correct, not merely asserted.

**Phase 10 (T099)**: a re-read of the "Pirate-Technician" tab's rank table at
`character-creation.html` found the source prints rank 0 as `Crewman [Gunnery-1]` — a title is
printed. The Rank 0 title row above previously recorded `(none printed)` / `(absent)` / `match`,
which described neither the source nor the committed file (`pirate.toml` has always carried
`title = "Crewman"`). Corrected the row to what both the source and the file actually say; no
data file change was needed.

No corrections to `pirate.toml` were found for this career; the row above was a record-keeping
error in this artifact, not a value the file had wrong.
