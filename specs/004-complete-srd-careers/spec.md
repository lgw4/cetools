# Feature Specification: Complete SRD Careers

**Feature Branch**: `004-complete-srd-careers`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "This feature completes the NPC generator's career content. The
package currently ships eight of the source's twenty-four careers; this adds the sixteen that
are missing and brings every career in the package into agreement with a single source of
truth, the published SRD at https://evolvedexperiment.github.io/cepheus-srd/. Its remit is
career content and the vocabularies careers draw on — skills and mustering-out benefits — not
the generation walk itself.

It is more than an addition, because an audit against that source found the shipped eight are
not one transcription. Navy matches the source closely. Scout and Drifter do not: they differ
in qualification target, re-enlistment target, rank-zero skill grant, mustering-out cash and
material tables, and service skills, and Drifter states an advanced-education requirement the
source applies uniformly to every career. The skill vocabulary likewise mixes source names with
names from another edition, and the benefit vocabulary lists items the source never awards. So
the scope is all twenty-four careers reconciled, plus both vocabularies rebuilt to exactly what
that source uses — every name its skill chapter defines or its career tables grant, and nothing
else.

Transcribing literally has consequences the current data shape cannot express, and the
decisions follow from refusing to paper over them. A rank may name no title, because six
careers print rank zero as a bare skill grant and Drifter prints nothing at all across every
rank row. A career's benefit tables run only as long as the source prints real rows, because
seven careers have no rank high enough to reach the seventh and the source leaves it blank.
Ship shares are a rolled quantity, not a single share. Cascade skills nest — a vehicle
specialty that is itself a cascade — and resolve through to a terminal skill rather than
stopping on a name no rule defines. The two skills that careers grant but the source's skill
chapter never defines are carried as vocabulary, with the discrepancy recorded where it lives.
Misspelled skill grants and one misspelled rank title are corrected, each correction noted in
the file carrying it. What binds these together, and what should survive into later work: the
existing data met the old shape by inventing rank titles and padding tables, and the rule from
here is that the data says what the source says and expresses absence as absence.

Noble ships. Its rank titles are rendered as ordinary rank titles, and the source's separate
Social-Standing nobility table remains unimplemented — with the fact that career data now
contains noble titles recorded explicitly, so that whoever implements those titles later knows
there is already data their rule must reconcile with. Benefit items are recorded as received —
counts of weapons, shares, memberships, a vessel — and their prose consequences belong to the
referee; that is a stated assumption, not an oversight, so that a sheet reading four ship
shares doesn't read as a missing feature. The three planetary-defense careers take the source's
long names, since that is how the source names them where it is naming rather than fitting a
column.

Because the content is transcribed from a published source rather than supplied by hand,
correctness rests on two things and no human diff review. First, invariants any correct career
must satisfy: every skill and benefit resolving in the vocabulary, ladders contiguous from
their base, and each career's benefit tables covering every row that career's own ranks can
reach. That coverage rule moves out of documentation and into the check users run, so a
house-rule author gets it too rather than discovering a short table partway through a batch.
Second, an independent re-read of every career — the sixteen new and the eight existing — that
begins from the source and compares against the committed file, never the reverse, since a
check that starts from the file will find confirmation. That direction is the difference
between a control and a formality, and it belongs in the requirements rather than in someone's
working habits.

Career selection draws from every career in force, so tripling the pool changes what every seed
produces. That is accepted as a breaking change for this release with no compatibility path:
anyone needing the old pool ships it as an override, and the release is the last one before any
of this is published. The pinned human-readable outputs are re-pinned in a behavior-preserving
step before any career content changes, then regenerated once afterward, so the regeneration is
attributable entirely to the pool growing rather than concealing a regression inside a large
diff.

Acceptance anchors to every career being demonstrably enterable and completable — for each, a
deterministic walk that qualifies in, serves a term, and musters out, exercising its skill
tables, its ladder, and its benefit rows — rather than to the data merely validating, since a
career nothing can traverse validates perfectly. Alongside that, the invariants pass and the
independent re-read has run for all twenty-four.

Out of scope: implementing the Social-Standing nobility titles; benefit prose semantics,
meaning once-only membership, a repeated weapon taken as skill instead, share valuation toward
a vessel, and vessel duty conditions; and the exclusions inherited from the previous feature —
psionics, anagathics, world generation, a lethal generation mode, and post-creation purchases.
The previous feature's specification is left intact as the record of what was decided then,
with a cross-reference added where its reasoning for excluding Noble is now superseded."

## Clarifications

### Session 2026-08-24

- Q: When the validator checks that a career's mustering-out tables are long enough (FR-020), which
  bonuses should it assume a character might have when rolling on those tables? → A: Every bonus the
  generation walk can apply to that career — rank bonuses for the material table, and the retirement
  bonus for the cash table. Cash tables therefore need every row up to the highest a retired
  character can roll; material tables may be shorter where ranks cannot reach.
- Q: Where should the source-first re-read of each career be recorded so that the verification
  record is inspectable? → A: A committed artifact under the feature directory — one file per
  career, or one table covering all 24 — listing the source's printed values field by field, then
  the committed file's values, then the verdict.
- Q: How should a character with no rank title appear in the machine-readable output, which today
  always emits a `title` field holding an empty string? → A: Keep the empty string. The field stays
  present and its shape unchanged; the placeholder FR-009 forbids is invented title text, not the
  empty marker the format already uses.
- Q: When a mustering-out row awards a rolled number of ship shares, how should the sheet record
  them? → A: Append the item once per share rolled, so the existing repeat-collapsing renderer shows
  "Ship Share (x3)" and the machine-readable benefits list holds three identical entries. No new
  benefit entry shape.
- Q: How should the per-career fields the source's career tables do not print — medical-care tier,
  always-available, re-enterable — be set for the sixteen new careers? → A: Transcribe them from
  wherever the source states them, including sections outside the career tables, and verify them in
  the re-read. Where the source is genuinely silent for a career, record the chosen default and its
  reason in that career's file.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a character from any career the source publishes (Priority: P1)

A referee generating NPCs wants the generator's career pool to be the source's career pool. Today
the pool is eight careers, so two-thirds of the source's professions can never appear: no matter
the seed, no batch produces a scholar, an entertainer, a pirate, or a noble. After this feature,
every career the source prints is in force, every one of them can be qualified into, served, and
mustered out of, and a batch drawn across many seeds reaches all of them.

**Why this priority**: It is the feature. Everything else here exists because transcribing the
remaining careers faithfully turned out to require it. A referee who gets nothing else still gets
the complete roster, which is the visible value.

**Independent Test**: Run a deterministic generation walk targeted at each career in turn and
confirm each one qualifies in, serves a term, and musters out with a sheet that names that career.
Fully testable without any of the later stories, because a complete roster is observable from CLI
output alone.

**Acceptance Scenarios**:

1. **Given** the shipped rules content, **When** the career roster is listed, **Then** exactly
   twenty-four careers are in force and their names are the names the source uses.
2. **Given** a deterministic walk constructed for a named career, **When** it runs, **Then** the
   character qualifies into that career, completes at least one term, and musters out with cash
   and material benefits drawn from that career's own tables.
3. **Given** a batch large enough to exercise career selection, **When** it runs, **Then** careers
   outside the previously shipped eight appear on generated sheets.
4. **Given** the same seed as the previous release, **When** a character is generated, **Then** the
   result may differ, and the changelog flags this as a breaking change with no compatibility path.

---

### User Story 2 - Data that says what the source says, including where it says nothing (Priority: P2)

A rules author reading a shipped career file wants it to be a transcription, not an adaptation.
Today the data shape forces every rank to carry a title and every mustering-out table to run seven
rows, so files invent titles the source never printed and pad tables past the last row the source
filled. After this feature, a rank with no printed title carries no title, a benefit table stops
where the source stops, a ship-share award is the rolled quantity the source prints rather than a
single share, and a cascade skill that resolves into another cascade resolves through to a terminal
skill.

**Why this priority**: The remaining sixteen careers cannot be transcribed faithfully until the
data can express these things, so this gates Story 1's correctness even though Story 1 carries the
visible value. It is also the rule that outlives this feature: absence is expressed as absence.

**Independent Test**: Take the shipped careers, remove the invented titles and the padded rows, and
confirm the files load, validate, and generate; confirm a character holding an untitled rank
renders without a title and a benefit roll never lands past a career's last real row.

**Acceptance Scenarios**:

1. **Given** a career whose source rank row prints a skill grant and no title, **When** the file is
   loaded, **Then** it validates with that rank carrying a grant and no title.
2. **Given** a career whose every rank row prints no title at all, **When** a character serves in it
   and is rendered, **Then** no rank title is attached to the name and no placeholder is emitted.
3. **Given** a career whose ranks cannot reach the seventh material benefit row, **When** the file is
   loaded, **Then** it validates with a material table shorter than seven rows, and no generated
   character ever rolls a row that career does not print.
4. **Given** a benefit award of ship shares, **When** a character receives it, **Then** the sheet
   records the rolled number of shares as that many receipts of the item, the human-readable output
   reports the total through its existing repeat display, and the number is determined by the seed.
5. **Given** a skill grant naming a cascade whose chosen specialty is itself a cascade, **When** the
   grant is resolved, **Then** resolution continues until a terminal skill is reached and the sheet
   never records a name that no rule defines.

---

### User Story 3 - One vocabulary, drawn from one source (Priority: P3)

A house-rule author writing their own career wants the skill and benefit vocabularies to tell them
exactly what names are available. Today the skills registry mixes names from the source with names
from a different edition, and the benefits registry lists items the source never awards, so the
vocabulary is not a reliable answer to "what can I write here?". After this feature, both
vocabularies contain exactly what the source uses and nothing else.

**Why this priority**: It is a prerequisite for the transcription being checkable at all — an
invariant that every grant resolves in the vocabulary means nothing if the vocabulary is a
superset assembled from two editions. Lower than Story 2 because it changes no shapes, only
contents.

**Independent Test**: Compare each registry's contents against the source's skill chapter and the
set of items its career tables award, and confirm the two sets match exactly in both directions.

**Acceptance Scenarios**:

1. **Given** the skills registry, **When** it is compared against the source, **Then** every entry
   is a skill the source's skill chapter defines or a career table grants, and every such name has
   an entry.
2. **Given** the benefits registry, **When** it is compared against the source, **Then** every entry
   is an item some career's mustering-out table awards, and no entry names an item the source never
   awards.
3. **Given** a skill that careers grant but the source's skill chapter never defines, **When** the
   registry is read, **Then** the name is present and the discrepancy is recorded in the registry
   file itself.
4. **Given** a misspelled skill grant or rank title in existing career data, **When** the file is
   read after this feature, **Then** the spelling is corrected and the correction is noted in the
   file carrying it.

---

### User Story 4 - The checks users run enforce what correct career data means (Priority: P4)

A house-rule author shipping a career override wants to learn their file is wrong when they
validate it, not partway through a batch when a benefit roll finds no row. After this feature, the
rules-validation command enforces the invariants any correct career must satisfy, including that a
career's benefit tables cover every row that career's own ranks can reach.

**Why this priority**: It converts a documented convention into an enforced one, and it is what
makes the shortened benefit tables of Story 2 safe rather than a new class of runtime failure. It
serves override authors, a narrower audience than Stories 1–3, hence the lower priority.

**Independent Test**: Feed the validator a career file that violates each invariant in turn and
confirm it reports the specific problem with the file and location; feed it every shipped career
and confirm it reports none.

**Acceptance Scenarios**:

1. **Given** a career file granting a skill or benefit that is not in the vocabulary, **When** it is
   validated, **Then** validation fails naming the file, the location, and the unresolvable name.
2. **Given** a career file whose rank ladder skips a position or does not start at its base, **When**
   it is validated, **Then** validation fails naming the gap.
3. **Given** a career file a character serving in it can roll past the end of — whether through rank
   on the material table or through the retirement bonus on the cash table — **When** it is
   validated, **Then** validation fails naming the shortfall and the missing row.
4. **Given** every career shipped in the package, **When** validation runs over the whole rules set,
   **Then** it reports no problems and exits successfully.

---

### User Story 5 - Transcription verified against the source, not against itself (Priority: P5)

Whoever accepts this work needs confidence that twenty-four transcriptions are right, and no human
is going to read a diff of that size usefully. After this feature, every career — the sixteen new
and the eight existing — has been re-read independently in the direction that can actually find an
error: starting from the source's printed tables and comparing them against the committed file.

**Why this priority**: It is a control on the work rather than a capability users exercise, so it
ranks last; but it is stated as a requirement rather than left to working habit, because a check
performed in the convenient direction is a formality.

**Independent Test**: For each career, open the committed verification artifact in the feature
directory and confirm it shows the re-read began from the source's tables, enumerated every field,
and that any discrepancy it found was resolved in the file rather than explained away.

**Acceptance Scenarios**:

1. **Given** any of the twenty-four careers, **When** the verification record is inspected, **Then**
   it shows the source's printed values enumerated first and the committed file compared against
   them, not the reverse.
2. **Given** a discrepancy found by a re-read, **When** it is resolved, **Then** the committed file
   changes to match the source, or the deviation is recorded in the file with its reason.
3. **Given** the full set of careers, **When** acceptance is assessed, **Then** all twenty-four have
   a completed re-read.

---

### Edge Cases

- What happens when a character's only rank is on a ladder that names no titles? No title is
  attached to the rendered name and no placeholder stands in for it, which is the previously
  established rule that a title comes from the most recent career whose ladder names one.
- What happens when a benefit roll would land past a career's last printed row? It cannot: the
  validated coverage invariant guarantees no rank that career can reach produces such a roll, and
  a house-rule file that breaks the guarantee is rejected at validation rather than at generation.
- What happens when a career's benefit table is shorter than another's? Nothing is padded and no
  row is duplicated to fill the gap; the table ends where the source ends it. Which tables can end
  early is not uniform: the material table may stop short in a career whose ranks cannot reach the
  last row, while the cash table must run to the row a retired character reaches, because the
  retirement bonus applies in every career.
- What happens when a cascade specialty is itself a cascade? Resolution continues until a terminal
  skill is reached. A cycle in the vocabulary is a data error, reported at validation.
- What happens when a career grants a skill the source's skill chapter never defines? The name is
  carried in the vocabulary so the grant resolves, and the discrepancy is recorded in the registry
  rather than silently normalized to something the chapter does define.
- What happens to a character sheet that records four ship shares, a membership, and two weapons?
  It records them as received. What they are worth, whether a repeat is taken as a skill instead,
  and what duties attach to a vessel are the referee's, by stated assumption.
- What happens to a Noble character's rank title? It renders as an ordinary rank title, because it
  is one. The source's separate Social-Standing nobility table is still unimplemented, and the fact
  that career data now contains noble titles is recorded so a later implementation reconciles with
  it rather than duplicating it.
- What happens to someone relying on a seed from the previous release? They get a different
  character. There is no compatibility path; the old pool can be reproduced only by shipping it as
  an override.
- What happens when the pinned human-readable outputs change? They are re-pinned once in a
  behavior-preserving step before any career content changes, and regenerated once afterward, so
  the second change is attributable entirely to the career pool growing.

## Requirements *(mandatory)*

### Functional Requirements

#### Career roster

- **FR-001**: The package MUST ship career content for all twenty-four careers the source
  publishes, comprising the eight already shipped and the sixteen currently missing.
- **FR-002**: Every shipped career's throws, skill tables, rank ladders, and mustering-out tables
  MUST agree with the single source of truth named in Assumptions, and no career may be transcribed
  from any other edition or from illustrative values in this project's own design documents.
- **FR-003**: The existing Scout and Drifter careers MUST be reconciled against the source across
  every field the audit found differing, including qualification target, re-enlistment target,
  rank-zero skill grant, mustering-out cash table, mustering-out material table, and service skills.
- **FR-004**: The advanced-education table requirement MUST be applied uniformly across all careers
  as the source applies it, rather than one career declaring a different requirement.
- **FR-005**: Each career's display name MUST be the name the source uses when naming the career,
  which for the three planetary-defense careers means the source's long names rather than an
  abbreviated column label.
- **FR-006**: The Noble career MUST ship, with its rank titles carried as ordinary rank titles.
- **FR-006a**: The per-career fields the source's career tables do not print — the medical-care
  tier, and the flags marking a career always available or re-enterable — MUST be transcribed from
  wherever the source does state them, including sections outside the career tables, and MUST be
  covered by the re-read in FR-023. Where the source is genuinely silent for a career, the value
  chosen MUST be recorded in that career's file together with the reason, rather than set silently.

#### Faithful data shape

- **FR-007**: A rank MUST be able to carry no title. Career data MUST NOT invent a title for a rank
  whose source row prints none, and a rank row that prints only a skill grant MUST be recorded as a
  grant with no title.
- **FR-008**: A career whose source rank rows print no titles at all MUST be recorded with no titles
  on any rank.
- **FR-009**: A character holding only untitled ranks MUST be rendered with no rank title and no
  invented text standing in for one, in every output rendering. In human-readable output the name
  appears with no title and no dangling separator. In machine-readable output the title field
  remains present and carries the empty string, which is the existing marker for "no title"; the
  field is not removed and does not become a null.
- **FR-010**: A career's mustering-out cash and material tables MUST be permitted to run fewer rows
  than the maximum, ending at the last row the source prints, and MUST NOT be padded or have a final
  row duplicated to reach a fixed length. A table shorter than the coverage rule in FR-020 demands
  is a defect in the transcription, not a licence to pad: it is resolved by re-reading the source,
  and if the source truly prints no such row, by recording the deviation under FR-024.
- **FR-011**: A mustering-out award of ship shares MUST be a quantity determined by a roll rather
  than a fixed single share, MUST be expressed in data rather than hard-coded, and MUST be derived
  solely from the seeded generator. The award MUST be recorded as that many separate receipts of the
  same item, so that the existing repeat-collapsing display reports the total and the
  machine-readable benefits list stays a list of plain item names with no quantity field.
- **FR-012**: Resolution of a cascade skill whose selected specialty is itself a cascade MUST
  continue until a terminal skill is reached, so that no recorded skill is a name for which no rule
  defines a level.
- **FR-013**: Career data MUST express absence as absence. Where the source prints nothing, the data
  MUST record nothing, rather than satisfying a shape requirement with invented content.

#### Vocabularies

- **FR-014**: The skills vocabulary MUST contain exactly the skill names the source's skill chapter
  defines together with any name a source career table grants, and MUST NOT contain names drawn from
  another edition or names the source never uses.
- **FR-015**: The mustering-out benefits vocabulary MUST contain exactly the items the source's
  career tables award, and MUST NOT contain items the source never awards.
- **FR-016**: A skill that career tables grant but the source's skill chapter never defines MUST be
  carried in the vocabulary so grants resolve, and the discrepancy MUST be recorded in the
  vocabulary file that carries the name.
- **FR-017**: Misspelled skill grants and the misspelled rank title found by the audit MUST be
  corrected, and each correction MUST be noted in the file that carries it.

#### Enforced invariants

- **FR-018**: The rules-validation the CLI exposes to users MUST reject a career whose skill or
  benefit grant does not resolve in the corresponding vocabulary, naming the file, the location, and
  the unresolvable name.
- **FR-019**: The same validation MUST reject a rank ladder whose rank positions are not contiguous
  from that ladder's base position.
- **FR-020**: The same validation MUST reject a career whose mustering-out tables do not cover every
  row a character serving in that career can reach, naming the shortfall. Reachability MUST account
  for every bonus the generation walk can apply to a roll on that career's tables, not rank alone:
  the material table MUST cover every row the career's own rank ladders can reach, and the cash
  table MUST additionally cover the rows a retired character reaches through the retirement bonus,
  which applies to every career regardless of rank.
- **FR-021**: The coverage rule in FR-020 MUST be enforced by the validation users run, not stated
  only in documentation, so that an author of override career data is subject to it.
- **FR-022**: Every career shipped in the package MUST pass validation with no reported problems.

#### Verification

- **FR-023**: Every one of the twenty-four careers MUST receive an independent re-read that begins
  from the source's printed tables and compares them against the committed file, never beginning
  from the file.
- **FR-023a**: Each re-read MUST leave a committed verification artifact under this feature's
  directory — one file per career, or one table covering all twenty-four — that enumerates the
  source's printed values field by field, records the committed file's corresponding values, and
  states a verdict per field. The artifact MUST be inspectable after the fact, so that "the re-read
  was done" is a checkable claim rather than a recollection.
- **FR-024**: A discrepancy found by a re-read MUST be resolved by changing the committed file to
  match the source, or by recording the deliberate deviation and its reason in the file itself.
- **FR-025**: Acceptance MUST NOT rest on a human review of the content diff.

#### Traversal acceptance

- **FR-026**: Each of the twenty-four careers MUST have a deterministic walk demonstrating that a
  character qualifies into it, serves at least one term, and musters out of it.
- **FR-027**: Each such walk MUST exercise that career's skill tables, its rank ladder, and its
  mustering-out benefit rows, so that a career which validates but cannot be traversed fails
  acceptance.

#### Release handling

- **FR-028**: Career selection MUST draw from every career in force, so the enlarged pool applies to
  all generation.
- **FR-029**: The change in generated output for a given seed MUST be released as a breaking change
  with no compatibility path, flagged prominently in the changelog.
- **FR-030**: The pinned human-readable outputs MUST be re-pinned once in a behavior-preserving step
  before any career content changes, and regenerated once after those changes, so that the second
  regeneration is attributable entirely to the enlarged career pool.
- **FR-031**: The fact that career data now contains noble titles MUST be recorded explicitly, so
  that a later implementation of the source's Social-Standing nobility table reconciles with the
  existing data rather than duplicating or contradicting it.
- **FR-032**: The previous feature's specification MUST be left intact as the record of what was
  decided then, with a cross-reference added at the point where its reasoning for excluding Noble is
  superseded by this feature.

### Key Entities

- **Career**: One profession from the source. Carries qualification, survival, and re-enlistment
  throws, optional commission and promotion throws, skill tables, one or more rank ladders, and
  mustering-out cash and material tables. It also carries a medical-care tier and the flags marking
  it always available or re-enterable, which the source states outside its career tables.
  Twenty-four exist.
- **Rank**: A position on a ladder. Carries a position, an optional title, and an optional skill
  grant. A rank with neither a title nor a grant is possible where the source prints an empty row.
- **Rank ladder**: An ordered, contiguous run of ranks from a base position. A career has an entry
  ladder and may have a commissioned ladder.
- **Mustering-out table**: An ordered run of rows, cash or material, ending at the last row the
  source prints. Its length is a fact about the career, not a fixed constant, and must still reach
  every row a character in that career can roll (FR-020).
- **Benefit item**: A named award recorded as received — a passage, a weapon, a membership, a
  quantity of ship shares, a vessel, a characteristic adjustment. Its prose consequences are the
  referee's.
- **Skill vocabulary**: The complete set of skill names in force, with each name's permitted
  specialties. A specialty may itself name a cascade.
- **Benefit vocabulary**: The complete set of mustering-out item names in force.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 24 of the source's careers are in force, and each one has a deterministic walk
  that qualifies in, serves a term, and musters out, exercising that career's skill tables, ladder,
  and benefit rows — 24 of 24 passing.
- **SC-002**: Validation over the complete shipped rules content reports zero problems, and each
  invariant in FR-018 through FR-020 is demonstrated to reject a violating file with a message
  naming the file and location.
- **SC-003**: The independent source-first re-read is complete for 24 of 24 careers, each evidenced
  by a committed verification artifact in the feature directory, and every discrepancy it raised is
  either fixed in the file or recorded there with its reason.
- **SC-004**: The skill and benefit vocabularies match the source exactly in both directions: zero
  entries absent from the source, zero source names absent from the vocabulary.
- **SC-005**: No shipped career contains an invented rank title or a padded mustering-out row; every
  rank title and every table row traces to a printed row in the source.
- **SC-006**: Pinned human-readable outputs change exactly twice: once in a step that changes no
  behavior, and once attributable entirely to the enlarged career pool.
- **SC-007**: A generated batch large enough to sample the pool produces characters from careers
  outside the previously shipped eight, confirming the enlarged pool reaches new content.
- **SC-008**: The release notes flag the seed-output change as breaking, and state that reproducing
  the previous pool requires shipping it as an override.

## Assumptions

- **The single source of truth** is the published SRD at
  https://evolvedexperiment.github.io/cepheus-srd/. Where an earlier transcription, another
  edition, or this project's own design documents disagree with it, it wins.
- **Twenty-four is the source's career count**, and the sixteen to be added are exactly those the
  source publishes and the package does not yet ship. The specific roster is enumerated during
  planning by reading the source, not assumed here.
- **Benefit prose semantics belong to the referee.** A sheet records what was received — counts of
  weapons, shares, memberships, a vessel. Once-only membership, a repeated weapon taken as a skill
  instead, share valuation toward a vessel, and vessel duty conditions are deliberately not
  modeled, and a sheet reading four ship shares is complete, not missing a feature.
- **The generation walk is unchanged in intent.** This feature changes career content, the
  vocabularies careers draw on, and the minimum data-shape and validation changes those require. It
  does not redesign qualification, terms, aging, or mustering-out procedure.
- **The three planetary-defense careers' display names change** to the source's long names. Where
  file naming and display naming can differ, the requirement in FR-005 is about the name users see.
- **This release is the last before publication**, which is why the breaking seed-output change is
  accepted with no compatibility path.
- **Rules content remains data.** Every value added here lives in shipped data files under the
  project's existing licensing designation for source-derived content; no career, skill, or benefit
  content is hard-coded in engine code.
- **The existing rule for attaching a rank title to a rendered name still holds**: the title comes
  from the most recently served career whose ladder names a title for the rank held. Untitled
  ladders simply never supply one, so FR-009 follows from the existing rule rather than replacing
  it.

## Out of Scope

- Implementing the source's Social-Standing nobility titles. The Noble career ships; the separate
  nobility table does not.
- Benefit prose semantics: once-only membership, a repeated weapon taken as skill instead, share
  valuation toward a vessel, and vessel duty conditions.
- Inherited from the previous feature and still excluded: psionics, anagathics, world and homeworld
  generation, a lethal generation mode, and post-creation equipment purchases.
- Redesigning the generation walk itself.
