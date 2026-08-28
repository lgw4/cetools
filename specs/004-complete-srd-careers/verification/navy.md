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
| Rank table shape | one printed column, ranks 0-6 | entry ladder = rank 0, officer ladder = ranks 1-6 (the split every other two-ladder career uses) | corrected — see Notes |
| Enlisted rank 0 title | Starman | Starman | match |
| Enlisted rank 0 grant | Zero-G-1 | Zero-G 1 | match |
| Officer rank 1 title | Midshipman | Midshipman | corrected |
| Officer rank 1 grant | none | (was: Melee Combat (Slashing Weapons) 1) | corrected |
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

**The rank table (004 T095, resolving the prior "match (see note)" rows).** Earlier
passes over this career, including this artifact's first version, could not get a
consistent read of Navy's rank table from this session's summarizing fetch tool — four
attempts flattened what the tool described as two adjacent columns into one
contradictory 0-6 sequence, at various points denying "Petty Officer" appears at all or
claiming Midshipman carries no bracketed grant. Reading the page's raw HTML directly
(bypassing the summarizing tool) settles it: the "Maritime Defense-Physician" tab's
comparison table gives Navy exactly **one** rank column, 0 through 6 — Starman
[Zero-G-1], Midshipman, Lieutenant, Lt Commander [Tactics-1], Commander, Captain,
Commodore — the same shape every other career's rank column has. There is no second,
adjacent column; the premise that one exists is what generated the earlier confusion.

`navy.toml` predates this feature (it is 002-rules-data-loading's reference career) and
carried two departures from that single column, both added deliberately by an earlier
feature (CHANGELOG, T155) to exercise engine paths: an invented rank 5, "Petty Officer"
[Gunnery 1], extending the *entry* ladder past rank 0; and a specified specialty,
"Melee Combat (Slashing Weapons)", on the *officer* ladder's Midshipman grant, where the
source prints the grant bare. Neither is a discrepancy FR-024 admits a deviation for —
the source is neither internally inconsistent nor silent on either point, it simply
prints something else — so both are corrected out. The officer ladder now reproduces
the source's single column at ranks 1-6 exactly, matching the entry-rank-0-only /
officer-ranks-1-N split every other two-ladder career in the package already uses
(Merchant, Scout, and the rest); see `navy.toml`'s header comment for the full
accounting, including the two engine paths (an uncommissioned promotion above rank 0; a
rank bonus with a specified specialty) that no longer have shipped-data coverage as a
result and are now covered by unit fixtures instead
(`test_generator.py::TestPromotionOffTheEntryLadder`,
`test_reference_career.py::test_no_shipped_career_specifies_a_specialty_on_a_rank_bonus`).
