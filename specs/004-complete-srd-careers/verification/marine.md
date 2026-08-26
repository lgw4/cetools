<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Marine

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023.

**Every corrected row below was confirmed by at least two independent fetches**, several by three
or four, given the scale of the divergence found: the previously-shipped `marine.toml` (research.md
R7's audit only flagged its material table's padded seventh row) turns out to differ from the
source on nearly every field.

| Field | Source | Committed (`marine.toml`) | Verdict |
|---|---|---|---|
| Display name | Marine | Marine | match |
| Qualification | Int 6+ | END 6+ | **corrected** |
| Survival | End 6+ | END 5+ | **corrected** |
| Commission | Edu 6+ | EDU 6+ | match |
| Advancement (promotion) | Soc 7+ | SOC 7+ | match |
| Re-enlistment | 6+ | 5+ | **corrected** |
| Advanced-education gate | Education 8+ | EDU 8+ | match |
| Medical tier | (service career, per R6) | service | match |
| Always-available | not stated | absent (false) | match |
| Re-enterable | not stated | absent (false) | match |
| Personal row 1 | +1 Str | STR +1 | match |
| Personal row 2 | +1 Dex | DEX +1 | match |
| Personal row 3 | +1 End | END +1 | match |
| Personal row 4 | +1 Int | SOC +1 | **corrected** |
| Personal row 5 | +1 Edu | EDU +1 | match |
| Personal row 6 | Melee Combat | Melee Combat | match |
| Service row 1 | Comms | Athletics | **corrected** |
| Service row 2 | Demolitions | Gun Combat | **corrected** |
| Service row 3 | Gun Combat | Melee Combat | **corrected** |
| Service row 4 | Gunnery | Recon | **corrected** |
| Service row 5 | Melee Combat | Vehicle | **corrected** |
| Service row 6 | Battle Dress | Zero-G | **corrected** |
| Specialist row 1 | Electronics | Gun Combat | **corrected** |
| Specialist row 2 | Gun Combat | Recon | **corrected** |
| Specialist row 3 | Melee Combat | Tactics | **corrected** |
| Specialist row 4 | Survival | Melee Combat | **corrected** |
| Specialist row 5 | Recon | Athletics | **corrected** |
| Specialist row 6 | Vehicle | Zero-G | **corrected** |
| Advanced-education row 1 | Advocate | Admin | **corrected** |
| Advanced-education row 2 | Computer | Electronics | **corrected** |
| Advanced-education row 3 | Gravitics | Engineering | **corrected** |
| Advanced-education row 4 | Medicine | Medicine | match |
| Advanced-education row 5 | Navigation | Navigation | match |
| Advanced-education row 6 | Tactics | Tactics | match |
| Rank 0 title | Trooper | Marine | **corrected** |
| Rank 0 grant | Zero-G-1 | Gun Combat 1 | **corrected** |
| Rank 1 title | Lieutenant | Lieutenant | match |
| Rank 1 grant | (none) | Melee Combat (Piercing Weapons) 1 | **corrected** |
| Rank 2 title | Captain | Captain | match |
| Rank 2 grant | (none) | (none) | match |
| Rank 3 title | Major | Force Commander | **corrected** |
| Rank 3 grant | Tactics-1 | Tactics 1 | match |
| Rank 4 title | Lt Colonel | Lt Colonel | match |
| Rank 4 grant | (none) | (none) | match |
| Rank 5 title | Colonel | Colonel | match |
| Rank 5 grant | (none) | (none) | match |
| Rank 6 title | Brigadier | Brigadier | match |
| Rank 6 grant | (none) | (none) | match |
| Cash row 1 | 1,000 | 2000 | **corrected** |
| Cash row 2 | 5,000 | 5000 | match |
| Cash row 3 | 10,000 | 5000 | **corrected** |
| Cash row 4 | 10,000 | 10000 | match |
| Cash row 5 | 20,000 | 10000 | **corrected** |
| Cash row 6 | 50,000 | 20000 | **corrected** |
| Cash row 7 | 50,000 | 20000 | **corrected** |
| Material row 1 | Low Passage | Low Passage | match |
| Material row 2 | +1 Edu | Weapon | **corrected** |
| Material row 3 | Weapon | Weapon | match |
| Material row 4 | Mid Passage | Mid Passage | match |
| Material row 5 | +1 Soc | STR +1 | **corrected** |
| Material row 6 | High Passage | SOC +1 | **corrected** |
| Material row 7 | Explorers' Society | Explorers' Society | match (this row was already fixed once, in Phase 6c, from a comment-acknowledged padded repeat to this real value — that fix was itself already correct) |

## Notes

This is by a wide margin the largest divergence any of the twenty-four careers' verification found
so far. Every corrected field above was confirmed by at least two independent WebFetch passes over
the source (throws, rank 0, and the service table each by four passes, given how much they
diverged from the committed file); nothing here rests on a single read. The scope goes well beyond
research.md R7's own audit of Marine, which recorded only the material table's padded seventh row
as a known issue — R7 states plainly that it "does not bound the work," and this is the case that
proves it. T087 should treat this as a near-total rewrite of `marine.toml` rather than a
field-level patch.
