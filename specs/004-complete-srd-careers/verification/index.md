<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification index

Every artifact in this directory is a source-first re-read against
<https://evolvedexperiment.github.io/cepheus-srd/character-creation.html>, independent of this
feature's transcription pass (spec.md FR-023). Each is a fresh reading of the source, not a
reconstruction from research.md, tasks.md, or any other working note of the transcription. This
index makes "all twenty-four were re-read, and none only partially" checkable without opening
every artifact.

## Roster-level check (FR-023b)

| Artifact | Complete | Result |
|---|---|---|
| [roster.md](roster.md) | yes | Clean — the source's published roster and the package's shipped roster are the same twenty-four names; none missing, none invented. |

## Background skills (FR-014a)

| Artifact | Complete | Result |
|---|---|---|
| [background-skills.md](background-skills.md) | yes | Clean — all three lists (law-level, trade-code, education) match the committed `background-skills.toml` row by row, including every repeat. |

## Per-career field verification (FR-023, FR-023a), alphabetical by basename

| Basename | Artifact | Complete | Result |
|---|---|---|---|
| aerospace-system-defense | [aerospace-system-defense.md](aerospace-system-defense.md) | yes | Corrected — advanced-education rows 3-6. |
| agent | [agent.md](agent.md) | yes | Match. |
| athlete | [athlete.md](athlete.md) | yes | Match. |
| barbarian | [barbarian.md](barbarian.md) | yes | Corrected — service table (rows 1-6) and material row 4. |
| belter | [belter.md](belter.md) | yes | Corrected — specialist rows 3 and 5. |
| bureaucrat | [bureaucrat.md](bureaucrat.md) | yes | Match. |
| colonist | [colonist.md](colonist.md) | yes | Corrected — advanced-education row 2. |
| diplomat | [diplomat.md](diplomat.md) | yes | Match. |
| drifter | [drifter.md](drifter.md) | yes | Match, including `always-available`/`re-enterable`. |
| entertainer | [entertainer.md](entertainer.md) | yes | Match. |
| hunter | [hunter.md](hunter.md) | yes | Corrected — advanced-education row 5 ("Tactics", was "Animals"); row 6 settled as "Animals" (matches, resolving the prior fetch-tool ambiguity). |
| marine | [marine.md](marine.md) | yes | Corrected — a near-total rewrite: both non-matching throws, re-enlistment, one personal row, the entire service/specialist/most of the advanced-education tables, rank 0's title and grant, rank 1's grant, rank 3's title, the entire cash table, and two material rows. |
| maritime-system-defense | [maritime-system-defense.md](maritime-system-defense.md) | yes | Match. |
| mercenary | [mercenary.md](mercenary.md) | yes | Match. |
| merchant | [merchant.md](merchant.md) | yes | Corrected — personal row 4. |
| navy | [navy.md](navy.md) | yes | Corrected — the rank table. The source prints one rank column, 0-6, not the two overlapping columns the file previously carried; removed the invented "Petty Officer" rank and the invented specified specialty on Midshipman's grant. |
| noble | [noble.md](noble.md) | yes | Corrected — rank 0's title and bonus grant. |
| physician | [physician.md](physician.md) | yes | Match. |
| pirate | [pirate.md](pirate.md) | yes | Match, including cross-verification of the existing "Pilot" → "Piloting" correction against `skills.html`. |
| rogue | [rogue.md](rogue.md) | yes | Match. |
| scientist | [scientist.md](scientist.md) | yes | Match. |
| scout | [scout.md](scout.md) | yes | Match, including cross-verification of the existing "Pilot" → "Piloting" correction against `skills.html`. |
| surface-system-defense | [surface-system-defense.md](surface-system-defense.md) | yes | Match. |
| technician | [technician.md](technician.md) | yes | Match. |

## Summary

Twenty-four of twenty-four careers re-read; none partial. Nine careers' data files received a
correction: seven in the commit that follows this index (T087) — aerospace-system-defense,
barbarian, belter, colonist, marine, merchant, noble — and two more in convergence (T095, T096),
once the two open questions below were settled by reading the source's raw HTML directly instead
of through this session's summarizing fetch tool: Navy's rank table (a single 0-6 column, not the
two overlapping columns the file previously carried) and Hunter's advanced-education row 5
("Tactics", not "Animals"; row 6 was already correct). No `deviation` verdict was recorded against
any field in any artifact — every discrepancy found had a clear, evidence-backed correct value
under FR-024, none met its three narrow grounds for recording a deviation instead.
