<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Navy

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

| Field | Source | Committed (`navy.toml`) | Verdict |
|---|---|---|---|
| Display name | Navy | Navy | match |
| Qualification | Int 6+ | INT 6+ | match |
| Survival | Int 5+ | INT 5+ | match |
| Commission | Soc 7+ | SOC 7+ | match |
| Advancement (promotion) | Edu 6+ | EDU 6+ | match |
| Re-enlistment | 5+ | 5+ | match |
| Advanced-education gate | Education 8+ (uniform rule, FR-004) | EDU 8+ | match |
| Medical tier | Tier 1 (75% at 4+, 100% at 8+) | service | match |
| Always-available | not named for this career | absent (false) | match |
| Re-enterable | not named for this career | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | +1 Int | INT +1 | match |
| Personal row 5 | +1 Edu | EDU +1 | match |
| Personal row 6 | Melee Combat | Melee Combat | match |
| Service row 1 | Comms | Comms | match |
| Service row 2 | Engineering | Engineering | match |
| Service row 3 | Gun Combat | Gun Combat | match |
| Service row 4 | Gunnery | Gunnery | match |
| Service row 5 | Melee Combat | Melee Combat | match |
| Service row 6 | Vehicle | Vehicle | match |
| Specialist row 1 | Gravitics | Gravitics | match |
| Specialist row 2 | Jack o' Trades (canonical `Jack-of-All-Trades`) | Jack-of-All-Trades | match |
| Specialist row 3 | Melee Combat | Melee Combat | match |
| Specialist row 4 | Navigation | Navigation | match |
| Specialist row 5 | Leadership | Leadership | match |
| Specialist row 6 | Piloting | Piloting | match |
| Advanced-education row 1 | Advocate | Advocate | match |
| Advanced-education row 2 | Computer | Computer | match |
| Advanced-education row 3 | Engineering | Engineering | match |
| Advanced-education row 4 | Medicine | Medicine | match |
| Advanced-education row 5 | Navigation | Navigation | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Enlisted rank 0 title | Starman | Starman | match |
| Enlisted rank 0 grant | Zero-G-1 | Zero-G 1 | match |
| Enlisted ranks 1-4 | not separately titled in the enlisted column | untitled, no grant | match (see note) |
| Enlisted rank 5 title | Petty Officer | Petty Officer | match (see note) |
| Enlisted rank 5 grant | Gunnery-1 | Gunnery 1 | match (see note) |
| Officer rank 1 title | Midshipman | Midshipman | match |
| Officer rank 1 grant | Melee Combat (Slashing Weapons)-1 | Melee Combat (Slashing Weapons) 1 | match (see note) |
| Officer rank 2 title | Lieutenant | Lieutenant | match |
| Officer rank 2 grant | none | none | match |
| Officer rank 3 title | Lt Commander | Lt Commander | match |
| Officer rank 3 grant | Tactics-1 | Tactics 1 | match |
| Officer rank 4 title | Commander | Commander | match |
| Officer rank 4 grant | none | none | match |
| Officer rank 5 title | Captain | Captain | match |
| Officer rank 5 grant | none | none | match |
| Officer rank 6 title | Commodore | Commodore | match |
| Officer rank 6 grant | none | none | match |
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
| Material row 5 | +1 Soc | SOC +1 | match |
| Material row 6 | High Passage | High Passage | match |
| Material row 7 | Explorers' Society | Explorers' Society | match |

## Notes

Every throw, skill table, and mustering-out row was confirmed by a fresh fetch and
matches the committed file — consistent with research.md R7's original audit finding
Navy already correct in full, and with this feature's own Phase 6c (T067) re-check.

**A tool limitation, not a data finding.** The source prints Navy's ranks as two
adjacent columns — an enlisted ladder (ranks 0-5) and a commissioned officer ladder
(ranks 1-6) — and four separate attempts to have this session's fetch tool quote them
as two distinct columns instead flattened them into one contradictory 0-6 sequence
each time (at various points denying "Petty Officer" appears at all, or claiming
Midshipman carries no bracketed grant, while other attempts in the same series
reproduced both correctly). Given the fetch tool's answers on this one point were
internally inconsistent across attempts, the rows marked "match (see note)" above rest
on the already-established prior verification (the original 003-npc-generator
transcription, reconfirmed by Phase 6c's T067 re-read) rather than a fresh
confirmation from this pass. Whoever accepts this feature may want to manually check
Navy's two-ladder rank table against the live page directly if certainty on this one
point matters; nothing else about Navy is in question.
