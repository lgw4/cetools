<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Aerospace System Defense

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`aerospace-system-defense.toml`) | Verdict |
|---|---|---|---|
| Display name | Aerospace System Defense | Aerospace System Defense | match |
| Qualification | End 5+ | END 5+ | match |
| Survival | Dex 5+ | DEX 5+ | match |
| Commission | Edu 6+ | EDU 6+ | match |
| Advancement (promotion) | Edu 7+ | EDU 7+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | 75%/100% bracket ("service") | service | match |
| Always-available | not stated | (absent, default false) | match |
| Re-enterable | not stated (Drifter/Draft are the only exceptions) | (absent, default false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | Athletics | Athletics | match |
| Personal row 5 | Melee Combat | Melee Combat | match |
| Personal row 6 | Vehicle | Vehicle | match |
| Service row 1 | Electronics | Electronics | match |
| Service row 2 | Gun Combat | Gun Combat | match |
| Service row 3 | Gunnery | Gunnery | match |
| Service row 4 | Melee Combat | Melee Combat | match |
| Service row 5 | Survival | Survival | match |
| Service row 6 | Aircraft | Aircraft | match |
| Specialist row 1 | Comms | Comms | match |
| Specialist row 2 | Gravitics | Gravitics | match |
| Specialist row 3 | Gun Combat | Gun Combat | match |
| Specialist row 4 | Gunnery | Gunnery | match |
| Specialist row 5 | Recon | Recon | match |
| Specialist row 6 | Piloting | Piloting | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Jack o' Trades (→ Jack-of-All-Trades, R4) | Medicine | **corrected**: `Jack-of-All-Trades` |
| Advanced-education row 4 | Medicine | Leadership | **corrected**: `Medicine` |
| Advanced-education row 5 | Leadership | Tactics | **corrected**: `Leadership` |
| Advanced-education row 6 | Tactics | Sciences | **corrected**: `Tactics` |
| Rank 0 title | Airman | Airman | match |
| Rank 0 grant | Aircraft-1 | Aircraft 1 | match |
| Rank 1 title | Flight Officer | Flight Officer | match |
| Rank 1 grant | (none) | (none) | match |
| Rank 2 title | Flight Lieutenant | Flight Lieutenant | match |
| Rank 2 grant | (none) | (none) | match |
| Rank 3 title | Squadron Leader | Squadron Leader | match |
| Rank 3 grant | Leadership-1 | Leadership 1 | match |
| Rank 4 title | Wing Commander | Wing Commander | match |
| Rank 4 grant | (none) | (none) | match |
| Rank 5 title | Group Captain | Group Captain | match |
| Rank 5 grant | (none) | (none) | match |
| Rank 6 title | Air Commodore | Air Commodore | match |
| Rank 6 grant | (none) | (none) | match |
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

- The Advanced Education table's rows 3-6 are the one real finding here: two independent fetches
  (a full-table request and a table-only single-fact request) agree that the source's Advanced
  Education table for this career is `Advocate, Computer, Jack o' Trades, Medicine, Leadership,
  Tactics` — six rows — where the committed file carries `Advocate, Computer, Medicine, Leadership,
  Tactics, Sciences`. `Jack o' Trades` normalizes to the canonical `Jack-of-All-Trades` per R4.
  `Sciences` does not appear in the source's list for this career at all.
- Medical tier confirmed by percentage bracket (75%/100%) since the source names no tier labels
  itself (FR-032); this matches this project's own "service" tier definition exactly.
- Every other field checked matches the committed file exactly, including the two rank rows that
  already carry bonus grants (rank 0's `Aircraft-1`, rank 3's `Leadership-1`) and the full cash and
  material mustering-out tables.
