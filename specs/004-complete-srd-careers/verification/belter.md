<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Belter

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`belter.toml`) | Verdict |
|---|---|---|---|
| Display name | Belter | Belter | match |
| Qualification | Int 4+ | INT 4+ | match |
| Survival | Dex 7+ | DEX 7+ | match |
| Commission | none | (absent) | match |
| Advancement (promotion) | none | (absent) | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | 0%/50%/75% bracket ("fringe") | fringe | match |
| Always-available | not stated | (absent, default false) | match |
| Re-enterable | not stated | (absent, default false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | Zero-G | Zero-G | match |
| Personal row 5 | Melee Combat | Melee Combat | match |
| Personal row 6 | Gambling | Gambling | match |
| Service row 1 | Comms | Comms | match |
| Service row 2 | Demolitions | Demolitions | match |
| Service row 3 | Gun Combat | Gun Combat | match |
| Service row 4 | Gunnery | Gunnery | match |
| Service row 5 | Prospecting | Prospecting | match |
| Service row 6 | Piloting | Piloting | match |
| Specialist row 1 | Zero-G | Zero-G | match |
| Specialist row 2 | Electronics | Electronics | match |
| Specialist row 3 | Gun Combat | Sciences | **corrected**: `Gun Combat` |
| Specialist row 4 | Prospecting | Prospecting | match |
| Specialist row 5 | Sciences | Vehicle | **corrected**: `Sciences` |
| Specialist row 6 | Vehicle | Vehicle | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Engineering | Engineering | match |
| Advanced-education row 3 | Medicine | Medicine | match |
| Advanced-education row 4 | Navigation | Navigation | match |
| Advanced-education row 5 | Comms | Comms | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | (none) | (none) | match |
| Rank 0 grant | Zero-G-1 | Zero-G 1 | match |
| Cash row 1 | 1000 | 1000 | match |
| Cash row 2 | 5000 | 5000 | match |
| Cash row 3 | 5000 | 5000 | match |
| Cash row 4 | 5000 | 5000 | match |
| Cash row 5 | 10000 | 10000 | match |
| Cash row 6 | 20000 | 20000 | match |
| Cash row 7 | 50000 | 50000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Mid Passage | Mid Passage | match |
| Material row 5 | 1D6 Ship Shares (→ `1d6 Ship Share`, FR-011/FR-015a) | 1d6 Ship Share | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | dash (no benefit) | (row absent, 6-row table) | match |

## Notes

`Prospecting`'s position (row 4 of both the service and specialist tables) was the one field this
feature's original transcription pass flagged as uncertain across two conflicting fetches; this
re-read's fetch agrees with the committed file's row 4 placement in both tables, so that field
is confirmed rather than corrected.

The Specialist table's other rows are the one real finding: two independent fetches (a full-table
request and a table-only single-fact request) both return
`Zero-G, Electronics, Gun Combat, Prospecting, Sciences, Vehicle` with no repeated name, where the
committed file carries `Zero-G, Electronics, Sciences, Prospecting, Vehicle, Vehicle` — `Sciences`
one row early and `Vehicle` repeated at the end instead of `Gun Combat` appearing at all. Corrected
to the source's order.
