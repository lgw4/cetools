<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Merchant

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`merchant.toml`) | Verdict |
|---|---|---|---|
| Display name | Merchant | Merchant | match |
| Qualification | Int 4+ | INT 4+ | match |
| Survival | Int 5+ | INT 5+ | match |
| Commission | Int 5+ | INT 5+ | match |
| Advancement (promotion) | Edu 8+ | EDU 8+ | match |
| Re-enlistment | 4+ | 4+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | Tier 2 (50% at 4+, 75% at 8+) — grouped with the other professional careers | professional | match |
| Always-available | not named for this career | absent (false) | match |
| Re-enterable | not named for this career | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | **Zero-G** | Melee Combat | **corrected** |
| Personal row 5 | Melee Combat | Melee Combat | match |
| Personal row 6 | Steward | Steward | match |
| Service row 1 | Comms | Comms | match |
| Service row 2 | Engineering | Engineering | match |
| Service row 3 | Gun Combat | Gun Combat | match |
| Service row 4 | Melee Combat | Melee Combat | match |
| Service row 5 | Broker | Broker | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Carousing | Carousing | match |
| Specialist row 2 | Gunnery | Gunnery | match |
| Specialist row 3 | Jack o' Trades (canonical `Jack-of-All-Trades`) | Jack-of-All-Trades | match |
| Specialist row 4 | Medicine | Medicine | match |
| Specialist row 5 | Navigation | Navigation | match |
| Specialist row 6 | Piloting | Piloting | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Engineering | Engineering | match |
| Advanced-education row 3 | Medicine | Medicine | match |
| Advanced-education row 4 | Navigation | Navigation | match |
| Advanced-education row 5 | Sciences | Sciences | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | Crewman | Crewman | match |
| Rank 0 grant | Steward-1 | Steward 1 | match |
| Rank 1 title | Deck Cadet | Deck Cadet | match |
| Rank 1 grant | none | none | match |
| Rank 2 title | Fourth Officer | Fourth Officer | match |
| Rank 2 grant | none | none | match |
| Rank 3 title | Third Officer | Third Officer | match |
| Rank 3 grant | Pilot-1 (misspelling; corrected to `Piloting 1`, FR-017) | Piloting 1 | match |
| Rank 4 title | Second Officer | Second Officer | match |
| Rank 4 grant | none | none | match |
| Rank 5 title | First Officer | First Officer | match |
| Rank 5 grant | none | none | match |
| Rank 6 title | Captain | Captain | match |
| Rank 6 grant | none | none | match |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 10000 | 10000 | match |
| Cash row 4 | 20000 | 20000 | match |
| Cash row 5 | 20000 | 20000 | match |
| Cash row 6 | 50000 | 50000 | match |
| Cash row 7 | 100000 | 100000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Edu | EDU +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | High Passage | High Passage | match |
| Material row 5 | 1D6 Ship Shares | 1d6 Ship Share | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | Explorers' Society | Explorers' Society | match |

## Notes

The first full-table request was refused ("substantial reproduction"); falling back to
several small targeted requests (throws; personal+service; specialist+advanced-education;
ranks; cash+material — the same one-field-group-at-a-time approach used successfully
elsewhere in this feature) succeeded on every one.

**One correction found**: Personal Development row 4 is printed as `Zero-G` in the
source, not `Melee Combat`. The committed file currently repeats `Melee Combat` at
rows 4 and 5, which reads as a transcription slip (row 4 mis-copied from row 5) rather
than anything the source itself does twice. Confirmed by two independent fetches. See
T087 for applying this correction.
