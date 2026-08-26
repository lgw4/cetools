<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Background Skills (FR-014a)

Source-first re-read against https://evolvedexperiment.github.io/cepheus-srd/character-creation.html,
independent of this feature's transcription pass, per spec.md FR-023a. Compared against
`src/cetools/data/chargen/background-skills.toml` as committed.

## Law-level table (4 rows)

| Row | Source | Committed | Verdict |
|---|---|---|---|
| 1 (No Law) | Gun Combat-0 | Gun Combat 0 | match |
| 2 (Low Law) | Gun Combat-0 | Gun Combat 0 | match |
| 3 (Medium Law) | Gun Combat-0 | Gun Combat 0 | match |
| 4 (High Law) | Melee Combat-0 | Melee Combat 0 | match |

## Trade-code table (14 rows)

Row-by-row, not a set comparison — the repeated rows are the weighting.

| Row | Trade code (source label) | Source | Committed | Verdict |
|---|---|---|---|---|
| 1 | Agricultural | Animals-0 | Animals 0 | match |
| 2 | Asteroid | Zero-G-0 | Zero-G 0 | match |
| 3 | Desert | Survival-0 | Survival 0 | match |
| 4 | Fluid Oceans | Watercraft-0 | Watercraft 0 | match |
| 5 | Garden | Animals-0 | Animals 0 | match |
| 6 | High Technology | Computer-0 | Computer 0 | match |
| 7 | High Population | Streetwise-0 | Streetwise 0 | match |
| 8 | Ice-Capped | Zero-G-0 | Zero-G 0 | match |
| 9 | Industrial | Broker-0 | Broker 0 | match |
| 10 | Low Technology | Survival-0 | Survival 0 | match |
| 11 | Poor | Animals-0 | Animals 0 | match |
| 12 | Rich | Carousing-0 | Carousing 0 | match |
| 13 | Water World | Watercraft-0 | Watercraft 0 | match |
| 14 | Vacuum | Zero-G-0 | Zero-G 0 | match |

Cross-checked with a second, independent fetch asking only for the skill-name sequence
(no trade-code labels) — both fetches returned the identical 14-item sequence:
Animals, Zero-G, Survival, Watercraft, Animals, Computer, Streetwise, Zero-G, Broker,
Survival, Animals, Carousing, Watercraft, Zero-G.

## Education table (15 rows)

| Row | Source | Committed | Verdict |
|---|---|---|---|
| 1 | Admin-0 | Admin 0 | match |
| 2 | Advocate-0 | Advocate 0 | match |
| 3 | Animals-0 | Animals 0 | match |
| 4 | Carousing-0 | Carousing 0 | match |
| 5 | Comms-0 | Comms 0 | match |
| 6 | Computer-0 | Computer 0 | match |
| 7 | Electronics-0 | Electronics 0 | match |
| 8 | Engineering-0 | Engineering 0 | match |
| 9 | Life Sciences-0 | Life Sciences 0 | match |
| 10 | Linguistics-0 | Linguistics 0 | match |
| 11 | Mechanics-0 | Mechanics 0 | match |
| 12 | Medicine-0 | Medicine 0 | match |
| 13 | Physical Sciences-0 | Physical Sciences 0 | match |
| 14 | Social Sciences-0 | Social Sciences 0 | match |
| 15 | Space Sciences-0 | Space Sciences 0 | match |

## Count rule

| Field | Source | Committed | Verdict |
|---|---|---|---|
| Background skill count | "3 + your Education DM" | `base = 3`, `characteristic = "EDU"` (chargen-parameters.toml) | match |

## Notes

All three lists and the count rule match the committed file exactly, row for row and in
printed order, including every repeat in the trade-code list (three `Animals`, three
`Zero-G`, two each of `Survival` and `Watercraft`). No `corrected` or `deviation` verdicts.
The trade-code list was independently cross-checked with a second fetch (skill names only,
no trade-code labels) to guard against the row-order errors that occurred elsewhere in this
feature's transcription pass; it returned the identical sequence. `Life Sciences`,
`Physical Sciences`, `Social Sciences`, and `Space Sciences` are printed bare in the
education list and are each also a specialty of the `Sciences` cascade (FR-016a, D6) — this
is the source's own printed form, not a transcription artifact, and is unaffected by this
verification.
