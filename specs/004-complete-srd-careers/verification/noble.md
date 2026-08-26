<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Noble

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`noble.toml`) | Verdict |
|---|---|---|---|
| Display name | Noble | Noble | match |
| Qualification | Soc 8+ | SOC 8+ | match |
| Survival | Soc 4+ | SOC 4+ | match |
| Commission | Edu 5+ | EDU 5+ | match |
| Advancement (promotion) | Int 8+ | INT 8+ | match |
| Re-enlistment | 6+ | 6+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | Tier 2 (50% at 4+, 75% at 8+) | professional | match |
| Always-available | not named for this career | absent (false) | match |
| Re-enterable | not named for this career | absent (false) | match |
| Personal row 1 | +1 Dex | DEX +1 | match |
| Personal row 2 | +1 Int | INT +1 | match |
| Personal row 3 | +1 Edu | EDU +1 | match |
| Personal row 4 | +1 Soc | SOC +1 | match |
| Personal row 5 | Carousing | Carousing | match |
| Personal row 6 | Melee Combat | Melee Combat | match |
| Service row 1 | Athletics | Athletics | match |
| Service row 2 | Admin | Admin | match |
| Service row 3 | Carousing | Carousing | match |
| Service row 4 | Leadership | Leadership | match |
| Service row 5 | Gambling | Gambling | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Computer | Computer | match |
| Specialist row 2 | Carousing | Carousing | match |
| Specialist row 3 | Gun Combat | Gun Combat | match |
| Specialist row 4 | Melee Combat | Melee Combat | match |
| Specialist row 5 | Liaison | Liaison | match |
| Specialist row 6 | Animals | Animals | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Liaison | Liaison | match |
| Advanced-education row 4 | Linguistics | Linguistics | match |
| Advanced-education row 5 | Medicine | Medicine | match |
| Advanced-education row 6 | Sciences | Sciences | match |
| Rank 0 title | **Courtier** | (none) | **corrected** |
| Rank 0 grant | **Carousing-1** | (none) | **corrected** |
| Rank 1 title | Knight | Knight | match |
| Rank 1 grant | none | none | match |
| Rank 2 title | Baron | Baron | match |
| Rank 2 grant | none | none | match |
| Rank 3 title | Marquis | Marquis | match |
| Rank 3 grant | none | none | match |
| Rank 4 title | Count | Count | match |
| Rank 4 grant | Advocate-1 | Advocate 1 | match |
| Rank 5 title | Duke | Duke | match |
| Rank 5 grant | none | none | match |
| Rank 6 title | Archduke | Archduke | match |
| Rank 6 grant | none | none | match |
| Cash row 1 | 2000 | 2000 | match |
| Cash row 2 | 10000 | 10000 | match |
| Cash row 3 | 20000 | 20000 | match |
| Cash row 4 | 20000 | 20000 | match |
| Cash row 5 | 50000 | 50000 | match |
| Cash row 6 | 100000 | 100000 | match |
| Cash row 7 | 100000 | 100000 | match |
| Material row 1 | High Passage | High Passage | match |
| Material row 2 | +1 Edu | EDU +1 | match |
| Material row 3 | +1 Int | INT +1 | match |
| Material row 4 | High Passage | High Passage | match |
| Material row 5 | Explorers' Society | Explorers' Society | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | 1D6 Ship Shares | 1d6 Ship Share | match |

## Notes

**One correction found**: rank 0 prints `Courtier [Carousing-1]` in the source — a
title and a bonus grant — confirmed by two independent fetches. The committed file
currently carries rank 0 with neither, on the premise (recorded in a earlier working
note, not the source) that Noble's entry rank was unremarked the way the seven
wholly-untitled careers are. That premise does not hold: the source does print
something for Noble's rank 0. See T087 for applying this correction; note that
adding a title here does not put Noble among the seven wholly-untitled careers
(T076/T076a), since Noble's *other* ranks are already titled and that invariant is
about a ladder with no titles at all, not about rank 0 specifically.

Everything else — every throw, every skill table, ranks 1-6, and both mustering-out
tables — matched on the first full-table fetch.
