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
| Advanced-education row 5 | Animals | Animals | match |
| Advanced-education row 6 | inconclusive — see Notes | Animals | match |
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

Every other field matches independently. Advanced Education row 6 is the one exception: three
separate fetches of the source answered three different ways — "Animals" (repeating row 5),
"Sciences", and a third pass that additionally reordered rows 2-4 and inserted "Computer" —
internally inconsistent with itself across fetches, not merely with the committed file. None of
the three reads is corroborated by a second independent fetch the way every other field in this
artifact is (each of those was confirmed twice).

**T087 follow-up (two further independent fetches, differently phrased):** a single-field request
answered "Animals"; a full-six-row verbatim request answered "Sciences". Across all five attempts
across both passes, three answered "Animals" and two answered "Sciences", with one outlier. No
reading is confirmed twice in a row by fresh, independently-phrased fetches the way every other
field in this artifact is, so the evidence stays short of FR-024's bar for changing a committed
value. `hunter.toml` is left unchanged (`Animals`, its committed value and the plurality answer)
rather than changed on a 3-to-2 split; `match` stands, not `corrected`. Recorded here as an
explicit limitation of this pass rather than settled fact: a human re-read of the source page
itself, not through the fetch-and-summarize tool, would resolve this with certainty if it matters
before release.
