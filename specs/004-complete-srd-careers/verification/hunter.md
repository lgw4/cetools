<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Hunter

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`hunter.toml`) | Verdict |
|---|---|---|---|
| Display name | Hunter | Hunter | match |
| Qualification | End 5+ | END 5+ | match |
| Survival | Str 8+ | STR 8+ | match |
| Commission | none | absent | match |
| Advancement (promotion) | none | absent | match |
| Re-enlistment | 6+ | 6+ | match |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | (professional career, per R6) | professional | match |
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
| Service row 3 | Melee Combat | Melee Combat | match |
| Service row 4 | Recon | Recon | match |
| Service row 5 | Survival | Survival | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Admin | Admin | match |
| Specialist row 2 | Comms | Comms | match |
| Specialist row 3 | Electronics | Electronics | match |
| Specialist row 4 | Recon | Recon | match |
| Specialist row 5 | Animals | Animals | match |
| Specialist row 6 | Vehicle | Vehicle | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Linguistics | Linguistics | match |
| Advanced-education row 3 | Medicine | Medicine | match |
| Advanced-education row 4 | Liaison | Liaison | match |
| Advanced-education row 5 | Tactics | Animals | corrected |
| Advanced-education row 6 | Animals | Animals | match |
| Rank 0 title | (none) | (none) | match |
| Rank 0 grant | Survival-1 | Survival 1 | match |
| Ranks 1-6 | dashes, no ranks listed | one entry ladder, rank 0 only | match |
| Cash row 1 | 1,000 | 1000 | match |
| Cash row 2 | 5,000 | 5000 | match |
| Cash row 3 | 10,000 | 10000 | match |
| Cash row 4 | 20,000 | 20000 | match |
| Cash row 5 | 20,000 | 20000 | match |
| Cash row 6 | 50,000 | 50000 | match |
| Cash row 7 | 100,000 | 100000 | match |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Int | INT +1 | match |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | High Passage | High Passage | match |
| Material row 5 | 1D6 Ship Shares | 1d6 Ship Share | match (FR-011/FR-015a: quantified notation, prose's singular form) |
| Material row 6 | High Passage | High Passage | match |

## Notes

Every other field matches independently.

**Advanced Education rows 5 and 6 (004 T096, resolving the prior open question).** Earlier
passes over this career could not get a settled read of row 6 from this session's summarizing
fetch tool — five attempts across two passes split three "Animals" to two "Sciences", with one
outlier reordering other rows, so no reading was corroborated by a second independently-phrased
fetch the way every other field in this artifact is. Reading the page's raw HTML directly
(bypassing the summarizing tool) settles it: the "Colonist-Marine" tab's Adv Education table
gives Hunter's column, top to bottom, as Advocate, Linguistics, Medicine, Liaison, **Tactics**,
Animals. Row 6 is `Animals`, confirming the committed value and the prior plurality answer — the
open question is resolved without changing `hunter.toml` on this row. Row 5, which no prior pass
had flagged, turns out to differ: the source's fifth row is `Tactics`, not `Animals` as committed
(`hunter.toml` had `Animals` twice, at rows 5 and 6). Corrected to `Tactics`.
