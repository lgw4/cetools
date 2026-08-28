<!-- Open Game Content per OGL 1.0a; see LICENSE-OGL.txt -->

# Verification: Roster (FR-023b)

Roster-level check, independent of the per-career field verification: establishes that no career
the source publishes is missing from the package, and no career the package ships is one the
source never publishes. A per-career re-read cannot establish either of these on its own, since it
starts from a career already on the roster.

Source: <https://evolvedexperiment.github.io/cepheus-srd/character-creation.html>, read fresh for
this check (not taken from research.md or tasks.md, which record the transcription pass this
verifies).

## Source's published roster (fresh read)

**From the careers narrative** (the prose introducing the careers section, before the tables),
twenty-four names:

Aerospace System Defense, Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat,
Drifter, Entertainer, Hunter, Marine, Maritime System Defense, Mercenary, Merchant, Navy, Noble,
Physician, Pirate, Rogue, Scientist, Scout, Surface System Defense, Technician.

**From the four Career Tables tabs**, six career columns each (confirmed as a second, independent
enumeration):

| Tab | Careers |
|---|---|
| Athlete–Bureaucrat | Athlete, Aerospace Defense, Agent, Barbarian, Belter, Bureaucrat |
| Colonist–Marine | Colonist, Diplomat, Drifter, Entertainer, Hunter, Marine |
| Maritime Defense–Physician | Maritime Defense, Mercenary, Merchant, Navy, Noble, Physician |
| Pirate–Technician | Pirate, Rogue, Scientist, Scout, Surface Defense, Technician |

The three system-defense careers appear under their short table-column headers here ("Aerospace
Defense", "Maritime Defense", "Surface Defense") rather than the narrative's long form — the same
abbreviated-header-versus-career-descriptions-list distinction FR-005/R2 already resolves in favor
of the long form. Set membership is otherwise identical between the two enumerations: 6 + 6 + 6 +
6 = 24 careers, matching the narrative's 24 one-for-one.

## Package's shipped roster

`load_rules().careers` reports exactly twenty-four entries (confirmed via `uv run cetools
validate`, `Files: 42`, and iterating `.name` on every loaded career):

Aerospace System Defense, Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat,
Drifter, Entertainer, Hunter, Marine, Maritime System Defense, Mercenary, Merchant, Navy, Noble,
Physician, Pirate, Rogue, Scientist, Scout, Surface System Defense, Technician.

## Comparison

| Check | Result |
|---|---|
| Careers in the source's set but missing from the package | none |
| Careers in the package's set that the source never publishes | none |
| Set sizes | 24 (source) = 24 (package) |

**Conclusion**: every career the source publishes is shipped, and none shipped is invented. The
source's published set and the package's shipped set are identical, name for name. This governs
the count of twenty-four in spec.md's Assumptions section, per FR-023b, rather than being checked
against it.
