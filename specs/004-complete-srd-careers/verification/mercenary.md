<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Mercenary

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`mercenary.toml`) | Verdict |
|---|---|---|---|
| Display name | Mercenary | Mercenary | match |
| Qualification | Int 4+ | INT 4+ | match |
| Survival | End 6+ | END 6+ | match |
| Commission | Int 7+ | INT 7+ | match |
| Advancement (promotion) | Int 6+ | INT 6+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | Tier 2 (50% at 4+, 75% at 8+) — grouped with Agent, Athlete, Bureaucrat, Diplomat, Entertainer, Hunter, Merchant, Noble, Physician, Pirate, Scientist, Technician | professional | match |
| Always-available | not named for this career | absent (false) | match |
| Re-enterable | not named for this career | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | Zero-G | Zero-G | match |
| Personal row 5 | Melee Combat | Melee Combat | match |
| Personal row 6 | Gambling | Gambling | match |
| Service row 1 | Comms | Comms | match |
| Service row 2 | Mechanics | Mechanics | match |
| Service row 3 | Gun Combat | Gun Combat | match |
| Service row 4 | Melee Combat | Melee Combat | match |
| Service row 5 | Gambling | Gambling | match |
| Service row 6 | Battle Dress | Battle Dress | match |
| Specialist row 1 | Gravitics | Gravitics | match |
| Specialist row 2 | Gun Combat | Gun Combat | match |
| Specialist row 3 | Gunnery | Gunnery | match |
| Specialist row 4 | Melee Combat | Melee Combat | match |
| Specialist row 5 | Recon | Recon | match |
| Specialist row 6 | Vehicle | Vehicle | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Engineering | Engineering | match |
| Advanced-education row 3 | Medicine | Medicine | match |
| Advanced-education row 4 | Navigation | Navigation | match |
| Advanced-education row 5 | Sciences | Sciences | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | Private | Private | match |
| Rank 0 grant | Gun Combat-1 | Gun Combat 1 | match |
| Rank 1 title | Lieutenant | Lieutenant | match |
| Rank 1 grant | none | none | match |
| Rank 2 title | Captain | Captain | match |
| Rank 2 grant | none | none | match |
| Rank 3 title | Major | Major | match |
| Rank 3 grant | Tactics-1 | Tactics 1 | match |
| Rank 4 title | Lt Colonel | Lt Colonel | match |
| Rank 4 grant | none | none | match |
| Rank 5 title | Colonel | Colonel | match |
| Rank 5 grant | none | none | match |
| Rank 6 title | Brigadier | Brigadier | match |
| Rank 6 grant | none | none | match |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 10000 | 10000 | match |
| Cash row 4 | 20000 | 20000 | match |
| Cash row 5 | 20000 | 20000 | match |
| Cash row 6 | 50000 | 50000 | match |
| Cash row 7 | 100000 | 100000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | High Passage | High Passage | match |
| Material row 5 | +1 Soc | SOC +1 | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | 1D6 Ship Shares (singular vocabulary entry, quantified notation, FR-015a) | 1d6 Ship Share | match |

## Notes

A first fetch answering only "what medical tier does Mercenary use" returned an
inconsistent, self-contradictory summary calling it a "military" tier career. A
follow-up fetch quoting the source's actual three-tier Medical Bills grouping
verbatim settled it: Mercenary sits in the middle (50%/75%/100%) tier alongside the
other professional careers, matching the committed file. Everything else matched
on the first full-table fetch. No corrections or deviations found.
