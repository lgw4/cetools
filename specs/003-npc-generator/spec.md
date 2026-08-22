# Feature Specification: NPC Generator

**Feature Branch**: `003-npc-generator`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "Decisions brief: npc-generator. The third of five MVP features
for cetools builds the NPC generator: the engine that turns a seed into a finished Cepheus
Engine character by running the SRD's lifepath end to end, the character data model that
engine produces, the renderings of that model, and the `cetools npc` command. It sits on the
validated rules loader the previous feature delivered and consumes rules content exclusively
through it. It ships eight careers, enough to exercise every shape the engine has to handle;
the remaining sixteen or so are the next feature's job. The generator runs the full arc: roll
characteristics, take background skills, qualify for a career or be drafted, take basic
training, then loop through terms of survival, commission, advancement, skill acquisition, and
aging until re-enlistment fails or the seven-term cap is reached, then muster out. It is
genuinely multi-career: a character who leaves a career under the cap selects another and
qualifies again at a cumulative penalty. Everything the SRD hands to a player is decided by the
generator, most of it randomly, and a small remainder by rule. The organizing commitment is
that the generator always produces a living, coherent character, and it buys that with the
SRD's own rules rather than by re-rolling: a failed qualification routes to the draft or to
Drifter, a failed survival throw takes the SRD's optional Survival Mishaps table, and an aging
crisis becomes a debt settled out of mustering-out benefits. The consequence chain is cut at
everything that moves a number on the sheet and nowhere further. Rules content stays in data,
and the data set grows in three directions: the career schema, a directory of per-kind
universal chargen tables, and the characteristics and skills registries. Output follows the
SRD's Universal Character Format as the default human-readable rendering, with a fuller text
rendering carrying what that format cannot and machine-readable output carrying everything
unconditionally; the seed, the package version, and the provenance go to standard error so
that redirecting the command's output produces a file that is exactly a character sheet.
Explicitly out of scope: psionics and anagathics, world and homeworld generation, name
generation, non-human species and their traits, starting equipment, noble titles, a lethal
chargen mode, and forcing a specific career or a specific number of terms."

## Clarifications

### Session 2026-08-20 (name tables)

Requested after the specification was first written, and amended into it rather than deferred,
because the exclusion it overturns is stated in this specification and shipping a spec that
forbids what the next one requires would leave the two contradicting each other.

- Q: The decisions brief excluded name generation on the grounds that name lists are not source
  material and carry no license cover, and FR-047 accordingly required the name to be supplied
  by the caller. Should the generator name its characters after all? → A: Yes. The generator
  ships a table of given names and a set of surname tables and rolls a name for every character.
  The licensing reasoning survives the change rather than being set aside: name tables are not
  Open Game Content, they are ordinary project content under GPL-3.0, and this is the first time
  the package ships a data file that is not OGC. The consequence is that the licensing checks and
  the copyright notice chain must distinguish the two designations rather than requiring the OGC
  designation of every data file, which is what FR-042 previously assumed.
- Q: Does the generator name a character by default, or only when asked? → A: By default. Every
  generated character gets a rolled name, and a caller-supplied name overrides it. The batch is
  the case that actually needs names, and a batch is exactly the case where supplying them by
  hand is impossible.
- Q: Are given names organized by region as surnames are? → A: No. There is one table of given
  names, selected to be gender neutral, and one surname table per region. A character's given
  name and surname are rolled independently, so the two are not correlated and a name is not a
  claim about where a character is from.
- Q: When a surname is rolled, is every region equally likely, or is every surname equally
  likely? → A: Every region is equally likely. Each region's table is chosen first and a surname
  is drawn from within it, so how many entries a table holds does not decide how often that
  region appears. Under the alternative, table size would be a hidden weighting decision that
  authoring work could shift without anyone intending it.
- Q: The regions named are North America, Central America, South America, Africa, Asia, Europe,
  and indigenous peoples not covered by those. Is the last one region among seven? → A: Yes, one
  table weighted equally with the other six. Because it collects distinct and unrelated naming
  traditions rather than one, its entries must each name the people they come from, so that the
  data does not flatten them into a single undifferentiated category.

### Session 2026-08-21

- Q: When a character served more than one career and holds a rank on more than one ladder,
  which career's rank title gets attached to the rendered name? → A: The title from the most
  recently served career in which the character holds a rank the ladder names a title for.
  This is decidable from what the character already carries, whereas taking the highest rank
  would require comparing a rank on one ladder against a rank on another, and no shipped data
  declares how ladders compare.
- Q: Is each entry in the generation history a structured record with named parts, or a line of
  prose? → A: A structured record with named parts. The fuller text rendering formats a line from
  the parts and machine-readable output emits the parts themselves. Prose was rejected because
  SC-005's traceability check and SC-004's consistency audit would then have to parse sentences,
  and a machine-readable history of strings is one a consumer cannot query.
- Q: In default text mode, what goes between one character sheet and the next in a batch? → A: A
  single blank line and nothing else. The name line at the top of each sheet is what identifies
  it. A numbered or seed-bearing header was rejected because it would put text on standard output
  that belongs to no sheet, which is what FR-051 exists to prevent.
- Q: In machine-readable mode, does a batch emit a document shaped differently from a single
  character's, and where does the seed live? → A: One shape always. Every run emits a
  batch-shaped document carrying a list of characters, a list of one when one character was
  asked for. The master seed, the package version, and the provenance sit at the top level; each
  character carries the derived seed that reproduces it alone. A consumer therefore writes one
  code path rather than branching on how many characters it asked for.
- Q: Does the character carry its name as a single string or as separate parts? → A: Both, at
  different jobs. One name string is always present and is what renders. The given name, the
  surname, and the region the surname came from are recorded separately when the name was rolled,
  and are empty when the caller supplied the name. Splitting a supplied name on a space was
  rejected, because a supplied name may be one word or five and FR-047 requires it verbatim;
  recording only the string was rejected because SC-019's weighting check would then have to
  recover a region by splitting rendered text.

### Session 2026-08-21 (requirements readiness review)

Raised by the readiness checklist in `checklists/readiness.md`, which asked of each
requirement whether it was stated completely enough to build from. Twelve rules the design
had already settled turned out to be stated nowhere in the requirements, two statements in
this document contradicted each other, and four success criteria were unfalsifiable as
written. The answers below are the ones that change meaning; the rest are amended in place.

- Q: On a failed qualification, what decides between the draft and the always-available
  career? → A: A count, held in data. A character may be routed to the draft a fixed number
  of times, and beyond that a failed qualification routes to the always-available career
  instead. Leaving it open would have made the routing the generator's discretion, which is
  the one kind of decision this feature does not have.
- Q: Does a successful commission or advancement grant a further skill roll? → A: Yes, and
  FR-009 was wrong to read as though the per-term count were the whole rule. The source
  grants one on each. Both counts go into data, so FR-009's stricter reading stays reachable
  by editing a file rather than the engine.
- Q: An aging crisis becomes a debt. What does settling that debt buy? → A: The
  characteristics the crisis covered come back off the floor, to a score declared in data.
  The source pays for medical care that restores them; carrying the cost as a debt changes
  when it is paid, not what it buys. A crisis whose debt is never settled leaves them
  floored.
- Q: Is a pension earned across one career or across a life? → A: One career. Terms in
  different careers are not added together for it, so a character with three terms in each
  of two careers has served six and qualifies for nothing. That is the difference between a
  pension and a length-of-service award, and the requirement as first written would have
  paid the second.
- Q: Does a career have one rank ladder or several, and what does a commission do to a
  character's place on them? → A: Several, and a commission moves the character to the
  commissioned ladder at its lowest rank. The career file declares which ladder a character
  enters on and which one a commission moves them to, because "the officer ladder is the
  second one" is a rule held in engine code.
- Q: Does a seed reproduce a character across package versions? → A: No, and the
  requirements now say so. The order in which the walk draws is part of what a seed
  reproduces, so any change that reorders, adds, or removes a draw changes every character
  and is flagged in the changelog as breaking. A referee quoting a seed to another referee
  needs telling this.
- Q: Is a name supplied together with a count above one a command-line error, or a rejected
  request? → A: A rejected request. The library refuses it on the same terms and the command
  reports it as a usage error. FR-055 requires every capability reachable programmatically,
  and a rule enforced only at the command line is one a library consumer does not get.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a usable NPC from a seed (Priority: P1)

A referee needs a person: a patron, a rival, a ship's engineer. They run one command with a
seed and get back a finished character sheet in the format the source material prints, ready
to drop into play. Behind that sheet, a whole career history was rolled out under the SRD's
own rules, but nothing the referee has to read to use the character.

**Why this priority**: This is the feature. Everything else in it, the history, the batch, the
machine-readable form, exists to serve or explain the sheet this story produces. It is also
the only story that must ship for the feature to be worth anything: a referee who can generate
one usable NPC has the whole of the value even if no other story lands.

**Independent Test**: Fully tested by running the command with a fixed seed and comparing the
sheet byte for byte against a committed reference, then running the same seed again and
getting the same bytes, then running many seeds and confirming every one produces a living
character with an internally consistent sheet. Delivers value on its own as the tool the
feature exists to be.

**Acceptance Scenarios**:

1. **Given** a seed, **When** the generator runs, **Then** a complete character is produced,
   carrying a name, a score for every characteristic the registry declares, a skill list, one
   or more careers with terms and rank, an age, and mustering-out proceeds, and the character
   is alive.
2. **Given** the same seed and the same package version, **When** the generator runs twice,
   **Then** the two characters are identical in every field and their sheets are identical
   byte for byte.
3. **Given** any seed at all, **When** the generator runs, **Then** it produces a character
   rather than an error, a partial result, or a dead character, and it does so without
   discarding and re-rolling any part of the walk.
4. **Given** a generated character, **When** the default rendering is written, **Then**
   standard output carries exactly the character sheet and nothing else, while the seed, the
   package version, and the provenance of the rules data appear on standard error.
5. **Given** a character who never held a rank on any ladder, **When** the default rendering
   is written, **Then** the lines the format has nothing to put in are omitted entirely
   rather than emitted blank.
6. **Given** no name supplied by the caller, **When** the generator runs, **Then** the
   character carries a given name and a surname rolled from the shipped name tables, so that
   the sheet names a person rather than an anonymous profile.
7. **Given** the same seed run twice, once with a caller-supplied name and once without,
   **When** the two characters are compared, **Then** they differ in the name and in the name
   parts that record how a rolled name was composed, and in nothing else, so that naming a
   character does not change who they turned out to be.

---

### User Story 2 - Tell a wrong engine from interesting dice (Priority: P2)

Someone looks at a surprising sheet, a forty-two year old with one skill or an admiral with
no Tactics, and asks whether the generator is broken. They ask for the character's history and
read the walk that produced it: the throws, what each one meant, and the consequence that
followed. The question is answered from the output rather than from a debugger.

**Why this priority**: The always-living commitment means the generator absorbs every failure
into a consequence rather than a stop, so nothing about the walk is visible in the sheet by
default. Without the history, a real defect and an unlikely run of dice look exactly alike,
and the only tool for telling them apart is reading the engine. It ranks below the sheet
because a referee playing the NPC never needs it, and above everything else because whoever
maintains the engine always does.

**Independent Test**: Fully tested by generating a character, requesting the fuller rendering
and the machine-readable output, and confirming that every characteristic, skill, credit, and
career on the sheet traces to a recorded step that produced it. Delivers value on its own as
the audit trail for every other story's output.

**Acceptance Scenarios**:

1. **Given** a generated character, **When** the fuller text rendering is requested, **Then**
   it carries the generation history, any outstanding debt, and any pension, none of which
   the default format has anywhere to put.
2. **Given** a generated character, **When** machine-readable output is requested, **Then**
   the emitted document carries every field of the character, including the history, the
   debt, the pension, the seed, and the provenance, whether or not each is non-empty.
3. **Given** a character carrying a skill, **When** the history is read, **Then** it names the
   step that granted that skill and the career and term in which the step occurred.
4. **Given** a character whose characteristics were reduced, **When** the history is read,
   **Then** it names the mishap or aging effect that reduced them and whether the reduction
   was reversed by paying medical bills.
5. **Given** a character who entered more than one career, **When** the history is read,
   **Then** it shows why each career ended and how the next was entered.

---

### User Story 3 - Populate a table, a crew, or a ward in one go (Priority: P3)

A referee needs twelve people, not one: a starport bar, a ship's complement, a list of
contacts. They ask for a batch from a single seed and get twelve characters, and quoting that
one seed to another referee reproduces all twelve.

**Why this priority**: Generating twelve NPCs by running twelve commands with twelve seeds
works, but leaves the referee holding twelve seeds instead of one, which is the difference
between a reproducible table and a pile of paper. It ranks below the history because it adds
reach rather than correctness, and above the data growth because it is the shape most actual
use takes.

**Independent Test**: Fully tested by requesting a batch from a seed, requesting it again and
comparing, and confirming that the first characters of a larger batch equal a smaller batch
from the same seed. Delivers value on its own as the bulk form of Story 1.

**Acceptance Scenarios**:

1. **Given** a seed and a count, **When** the generator runs, **Then** that many characters
   are produced, and running the same seed and count again produces the same characters in
   the same order.
2. **Given** a seed, **When** a batch of a larger count is generated, **Then** its first
   characters are identical to a batch of a smaller count from the same seed, so a count is
   a request for more of one sequence rather than for a different sequence.
3. **Given** a batch and the default text rendering, **When** the output is written, **Then**
   standard output carries the character sheets and nothing else, one blank line between
   consecutive sheets and no other separating text, with the seed and provenance reporting on
   standard error.
4. **Given** a batch and machine-readable output, **When** the output is written, **Then** a
   single document carries all the characters as a list, consumable without splitting a stream,
   in the same shape a run of one character emits.

---

### User Story 4 - Change the rules without changing the code (Priority: P4)

A referee whose setting has no Marines, or whose aging is gentler, or whose Drifters get a
different mishap table, writes the data file that says so, points the tool at it, and
generates characters under their rules. Nobody edits any code, and the tool tells them their
characters came from modified data.

**Why this priority**: The project's data-driven principle promises exactly this, and the
generator is the first feature with enough rules content for the promise to be worth
anything. It ranks last because it is the previous feature's mechanism reaching a new body of
data rather than a new mechanism, and because a referee gets full value from the first three
stories without ever writing a data file.

**Independent Test**: Fully tested by generating a character from the packaged data, then
generating the same seed with an override that changes one value, and confirming the character
changes accordingly, the provenance reports the override, and no code was edited. Delivers
value on its own as the house-rule path for all character generation.

**Acceptance Scenarios**:

1. **Given** an override supplying a modified aging table, **When** a character is generated,
   **Then** the aging effects follow the supplied table and the provenance names the file as
   overridden.
2. **Given** an override supplying a career that did not ship, **When** characters are
   generated, **Then** that career can be entered, and the provenance reports it as an
   addition.
3. **Given** an override that changes the term cap, **When** characters are generated,
   **Then** the cap that governs is the supplied one, demonstrating that no rules constant is
   held in code.
4. **Given** an override whose data is inconsistent, such as a draft table naming a career
   that is not in force, **When** a character is generated, **Then** the run fails before any
   character is produced, naming what could not be resolved.

---

### Edge Cases

- What happens when a character fails their very first qualification throw? They are routed to
  the draft or become a Drifter, per the SRD, and their history records which. No character
  reaches mustering out having served no career.
- What happens when a character fails a survival throw? They take a result from the Survival
  Mishaps table rather than dying. They are injured, discharged, or disgraced, they leave the
  career, and the walk continues to the next career or to mustering out.
- What happens when a mishap ends a term early? The term counts toward the seven-term cap and
  toward the aging modifier, costs two years rather than four, and forfeits that term's
  benefit roll. A character whose terms all ended in mishap is therefore younger than a
  character with the same term count who served them out.
- What happens when a character suffers an aging crisis but has no money, which is every
  character before mustering out? The crisis becomes a debt, settled from mustering-out
  benefits when they arrive. It never kills the character.
- What happens when mustering-out proceeds do not cover the debt? The remainder is recorded as
  outstanding debt on the character, the characteristic reductions the unpaid bills would have
  reversed stand, and the fuller rendering and machine-readable output both carry it. The
  default format, which has nowhere to put it, does not.
- What happens when a character's funds would go negative? They do not. Debt is carried as
  debt, distinct from funds, so a character has a non-negative balance and a separate
  outstanding amount.
- What happens when a character reaches the seven-term cap while re-enlistment keeps
  succeeding? The cap forces mustering out. The cap and the re-enlistment throw are two
  separate ways a career ends and both must be honored.
- What happens when a character leaves a career under the cap? They select another career and
  qualify for it again at a penalty that grows with each career already entered. Only Drifter
  may be re-entered; any other career already entered is not available again.
- What happens when a character fails qualification for a second or third career? The same
  routing applies as for the first: the draft, or Drifter. A character is never left with
  nowhere to go.
- What happens when a career declares neither a commission throw nor an advancement throw?
  The character takes two skill rolls per term in that career rather than one. No flag says
  so; the absence of both throws is what says so.
- What happens when a character is already commissioned and the career offers a commission?
  The commission throw is not attempted again. A commission is entered once per career.
- What happens when a commission or an advancement throw succeeds? It is taken. Declining is
  not modeled, because declining is not a meaningful character choice and treating it as a
  coin flip would leave half of every officer corps at rank zero.
- What happens when a skill grant names a skill that has specialties but names none? The
  generator chooses one at random from the specialties the registry permits for that skill,
  and the history records the choice. This is the cascade rule, and the choice is the
  generator's because the SRD hands it to the player.
- What happens when a table the character rolls on is gated on a characteristic they do not
  meet? That table is not among the tables the roll may select, so a gate excludes rather
  than fails.
- What happens when a reduction would take a characteristic below the range the pseudo-hex
  letters cover? It takes it to the bottom of that range instead. The characteristics registry
  declares that bottom explicitly alongside the letters, so the covered range is data rather
  than an assumption, and the history records both the reduction the rule called for and the
  amount actually applied when the two differ. The rules can therefore never produce a score
  the letters do not cover, which is what makes the letters' coverage a property rather than a
  hope.
- What happens when a characteristic reaches the bottom of that range, which the shipped data
  puts at zero? The reduction stands and is recorded; no death results, because no death path
  exists in this engine. Where the bottom was reached by aging, an aging crisis follows and
  settling its debt lifts the characteristic back off the floor. What a floored characteristic
  means in play is otherwise the referee's business and not the generator's.
- What happens when a score rises above the top of the declared range? The run fails naming
  the score and the range. This is unreachable from the shipped data and exists for an override
  that declares fewer letters than the rules shipped beside them can produce.
- What happens when a character has exactly one background skill to take? They take one
  homeworld skill, rather than the two the general rule would give or the none a strict
  reading would give.
- What happens when the draft table names a career that is not in force, because an override
  removed it or a shipped file was edited? The run fails before producing any character,
  naming the unresolvable career, rather than falling back to Drifter. A fallback here would
  be a rule in engine code that has no reason to exist once the data is complete.
- What happens when no name is supplied? A name is rolled: a given name from the given-names
  table and a surname from one of the regional surname tables. The rank title from the career
  ladder is attached to it if the character holds one.
- What happens when a name is supplied? It is used verbatim and no name is rolled. The character
  is otherwise identical to the one that seed produces unnamed, except that the fields recording
  which given name, surname, and region a rolled name came from are empty, there being no rolled
  name to record.
- What happens when a character holds a titled rank in two careers, such as a commissioned
  officer who later served as a Drifter? The title attached is the one from the most recent
  career that titled them, so the officer keeps the title and the untitled later career does not
  erase it. Ranks on different ladders are never compared, because nothing in the data says how
  they would compare.
- What happens when a batch is generated and two characters roll the same name? Nothing. A
  repeated name is not prevented, because preventing it would make each character depend on the
  ones generated before it, and a character in a batch must be reproducible from its own
  position alone.
- What happens when a caller supplies one name and asks for a batch of twelve? The supplied
  name is a usage error against a batch of more than one, rather than twelve identical names or
  eleven silently discarded requests.
- What happens when an override supplies a surname table for a region that shipped, or for a
  region that did not? The first replaces that region's table and the weighting is unchanged;
  the second adds an eighth region, which then carries the same weight as each of the others.
  Regional weighting is per table in force, not a fixed seventh share.
- What happens when an override supplies an empty name table? The run fails naming the file,
  rather than producing characters with no given name or drawing every surname from the
  remaining regions.
- What happens when a character's career grants a noble title? It is not rendered. Choosing
  between the source's printed forms requires a gender the source itself files as pure color,
  and emitting only one form would render every titled NPC a Baron and never a Baroness.
- What happens when the same seed is used on a machine with a different locale? The same
  bytes are produced, because the skill ordering the format requires is sorted
  locale-independently.
- What happens when a batch is requested with a count of zero or a negative count? It is a
  usage error naming the option, rather than a successful run producing nothing.
- What happens when the caller supplies an empty name, or one that is only whitespace? It is a
  usage error. Every character has a personal name and a supplied name is used verbatim, and an
  empty string honors the second requirement at the cost of the first. Rolling a name instead
  was rejected because it makes an empty string mean the opposite of what it says.
- What happens when a character is routed to the draft more times than the data allows? The
  further failed qualification routes them to the always-available career instead. The draft is
  a limited resource rather than an unlimited one, which is what keeps a character with a bad
  characteristic from being drafted into every career in the game.
- What happens when a character serves three terms in one career and three in another? They
  receive no pension. A pension is earned in a single career, and six terms spread over two
  careers is not five terms in one.
- What happens when two surname tables in force declare the same region, or when none is in
  force at all? Both fail the run before any character is produced, naming the files at fault.
  A duplicated region would quietly take two shares of a weighting taken over tables, and no
  table in force leaves no surname to draw.

## Requirements *(mandatory)*

### Functional Requirements

#### The generation arc

- **FR-001**: The system MUST generate a complete character from a seed by running the source
  material's lifepath end to end: rolling characteristics, taking background skills, entering a
  career, taking basic training, serving terms, and mustering out. No step may be skipped, and
  no step's result may be supplied from outside the walk.
- **FR-002**: Characteristics MUST be rolled at the start of the walk, one per characteristic
  declared in the characteristics registry, so that which characteristics exist is data rather
  than something the generator knows.
- **FR-003**: The system MUST take background skills according to the source material's rule,
  drawing over its background and homeworld skill tables directly. A character entitled to
  exactly one background skill MUST take one homeworld skill.
- **FR-004**: The system MUST attempt qualification for a career it selects at random from the
  careers in force. On failure it MUST route the character to the draft, and the history MUST
  record that it did. How many times one character may be routed to the draft MUST be a rules
  constant held in data; once a character has been drafted that many times, a further failed
  qualification MUST route them instead to a career declaring itself always available under
  FR-006, which the history MUST likewise record. Which of the two routes a failure takes is
  therefore decided by a count rather than left open, so that the routing is never the
  generator's discretion and a character is never left with nowhere to go.
- **FR-005**: The draft MUST resolve over the universal Draft table, whose row ordering is
  significant because the die that reads it is positional. Every career the Draft table names
  MUST resolve to a career in force, and a name that does not MUST fail the run before any
  character is produced.
- **FR-006**: Drifter MUST always be available as a fallback, declared as such in its own
  career file rather than known to the generator. When Drifter is selected by the ordinary
  random selection it MUST be qualified for by throw; when it is entered as the fallback,
  entry MUST be automatic.
- **FR-007**: On entering a career, the character MUST take that career's basic training, and
  MUST be granted the bonus attached to rank zero of the ladder they enter on. Granting the
  rank-zero bonus at entry is what makes it reachable at all; under any other reading it is
  data nothing can reach.
- **FR-007a**: Basic training MUST grant, on the character's first career, every entry of that
  career's service skill table at level zero, and on any later career a number of entries drawn
  from that same table. Both MUST be rules constants held in data rather than a distinction the
  engine knows, so that a referee whose setting trains later careers as fully as the first
  changes a value rather than a branch.
- **FR-007b**: A career MUST be able to declare more than one rank ladder, and MUST declare
  which ladder a character entering the career starts on and which ladder a successful
  commission moves them to. A character holds a rank on exactly one ladder at a time.
  Advancement moves them up their current ladder; a commission moves them to the commissioned
  ladder at the lowest rank that ladder declares. The bonus attached to a rank MUST be granted
  when the character reaches that rank, which is the same reading FR-007 gives the rank-zero
  bonus on entry. Which ladder is which MUST be declared in the career file: a rule that reads
  "the commissioned ladder is the second one listed" is a rule held in engine code.
- **FR-008**: Each term MUST run survival, then commission where the career offers one, the
  character is not already commissioned, and the character is not barred from attempting it
  under FR-012a, then advancement where the career offers one, then skill acquisition, then
  aging, in that order.
- **FR-008a**: An unmodified survival result at or below a threshold held in data MUST fail
  whatever the modifiers. A character with modifiers large enough to make survival arithmetically
  certain is a character for whom the survival throw is not a throw, and the source material
  guards against exactly that.
- **FR-009**: A character MUST take one skill roll per term, except in a career that declares
  neither a commission throw nor an advancement throw, where they MUST take two. No flag
  declares this; the absence of both throws declares it. In addition, a successful commission
  throw and a successful advancement throw MUST each grant a further skill roll in the term the
  throw succeeded in. All four counts (the ordinary per-term count, the count in a career
  declaring neither throw, and the two a successful throw grants) MUST be rules constants held
  in data, so that a referee who wants the stricter reading of the first sentence sets the last
  two to zero and gets it with no code edit.
- **FR-010**: Each skill roll MUST select at random among the tables the character is eligible
  for in that career, honoring any characteristic gate on a table, and MUST record the table
  it selected.
- **FR-011**: Where a granted skill has specialties in the registry and the grant names none,
  the system MUST choose one at random from those the registry permits for that skill, and
  MUST record the choice.
- **FR-012**: A successful commission throw and a successful advancement throw MUST be taken.
  Declining MUST NOT be modeled.
- **FR-012a**: A character who entered a career by the draft MUST NOT attempt that career's
  commission throw in their first term of it. Whether the bar applies MUST be a rules constant
  held in data, since it is a rule about how a career is entered rather than a shape of the
  walk.
- **FR-013**: Aging MUST be applied per the universal aging table once the character passes the
  point at which the source material begins aging, with the modifier taken from the number of
  terms served across all careers.
- **FR-014**: At the end of each term the system MUST decide at random whether the character
  wishes to continue serving. A character who wishes to continue MUST still pass the
  re-enlistment throw, and a character who has served the term cap MUST muster out regardless
  of either. Deciding continuation randomly is what spreads the ages; deciding it by rule
  would park every character at the cap.
- **FR-015**: A character who leaves a career while under the term cap MUST select another
  career and qualify for it again, at a penalty that accumulates with each career already
  **entered**. A career already entered MUST NOT be available again, except Drifter, which MUST
  be re-enterable because its own career file declares it so. "Entered" rather than "served" is
  deliberate and is used consistently wherever this specification gates re-entry or accumulates
  the penalty: a career the character was drafted into and mishapped out of was entered, and
  reading it the other way would make the draft a way to avoid the penalty.
- **FR-016**: On mustering out, the system MUST determine the number of benefit rolls from the
  terms served and the rank reached, following the specific mustering-out rule rather than the
  looser phrasing of the summary checklist, and MUST decide at random for each roll whether it
  is taken as cash or as a material benefit. How many of a character's rolls may be taken as
  cash MUST be capped, and a modifier on material benefit rolls MUST apply by the rank reached.
  The throw that decides cash against material MUST itself be a rules constant held in data,
  stated as a throw and a target exactly as the continuation decision of FR-014 is, because it
  is the same kind of decision: a random choice the source hands to the player, which this
  generator makes. A decision made at random by arithmetic the engine holds is a rules constant
  in code however evenly it falls, and a referee who wants characters to prefer cash MUST reach
  it by editing a file. All three MUST be rules constants held in data.
- **FR-017**: The cash benefit modifier that applies to a retired character MUST apply exactly
  when the character qualified for the pension, and MUST NOT be applied on any other reading of
  "retired".
- **FR-018**: A character qualifies for a pension by serving at least a minimum number of terms
  **in a single career**, and the amount MUST be a base plus an increment for each term served
  in that career above the minimum. The minimum, the base, and the increment MUST be rules
  constants held in data. Terms served in different careers MUST NOT be added together for this
  purpose: a character with three terms in each of two careers has served six terms and
  qualifies for nothing, which is the difference between a pension and a length-of-service
  award. A character who qualifies MUST receive it, and it MUST be carried on the character
  distinctly from funds, because it is an ongoing amount rather than a balance.

#### The always-living guarantee

- **FR-019**: A failed survival throw MUST resolve on the source material's optional Survival
  Mishaps table. The character MUST NOT die, MUST leave the career, and MUST carry the
  mishap's consequence.
- **FR-020**: A term ended by a mishap MUST cost two years rather than four, MUST count toward
  the term cap and toward the aging modifier, and MUST forfeit that term's benefit roll.
- **FR-021**: An aging crisis occurs when an aging effect reduces a characteristic to the
  bottom of the range the characteristics registry declares. Its cost MUST be a throw times a
  multiplier, both rules constants held in data, and MUST become a debt against the character,
  settled from mustering-out proceeds when they arrive, extending the way the source material
  already handles medical and anagathic costs. It MUST NOT kill the character, who has no money
  at the time the crisis occurs because money arrives at mustering out. Where the debt is
  settled, every characteristic the crisis covered MUST be restored to a score held in data;
  where it is not, they MUST stand where the reduction left them. Restoring them is what the
  payment buys in the source material, and carrying the cost as a debt changes when it is paid
  rather than what it is for.
- **FR-022**: The system MUST contain no path by which a character dies, and MUST NOT offer a
  lethal mode as an option. This is a stated non-goal rather than an oversight: a selectable
  death path would have to be built and tested in both output modes for a branch the shipped
  data never takes.
- **FR-023**: The system MUST NOT discard a partly generated character and start again for any
  reason. Every seed walks one fixed-length path to one character, which is what makes
  reproducibility a property of the design rather than a tendency of the output.

#### Consequences that move a number

- **FR-024**: A mishap MAY reduce characteristics directly, and MAY instead defer to an injury
  table that determines the reduction. Where it defers, the injury MUST be thrown for and
  recorded as a step of its own, so that a sheet showing a reduction the mishap's own row does
  not name still traces to the throw that produced it. A reduction arriving by either route
  MUST persist unless the character's medical bills are paid.
- **FR-025**: A character who leaves a career carrying a characteristic reduction from an
  injury MUST have medical bills raised against them. The share the employer pays MUST be
  determined by a throw against the medical tier the character's career declares, and the
  character MUST owe the remainder. The cost of restoring one point MUST be a rules constant
  held in data, so that the character's bill is that cost, times the points reduced, times the
  share they owe.
- **FR-025a**: The aging-crisis cost and the medical bill MUST both be recorded as debts when
  they arise, and MUST be settled from mustering-out proceeds in the order they arose. A debt
  proceeds do not cover MUST be carried under FR-026, and the characteristic points its payment
  would have restored MUST stand reduced. Where proceeds cover a medical bill only in part, the
  points restored MUST be those the covered amount pays for at the per-point cost, and the
  order in which points are considered MUST be a decision the walk makes and records rather
  than the order some collection happens to be traversed in, which FR-056 forbids as a source
  of variation. Funds MUST NOT go below zero at any point in this settlement.
- **FR-026**: Debt that mustering-out proceeds do not settle MUST be carried on the character
  as an outstanding amount, distinct from funds, and MUST be reported wherever the rendering
  has room for it.
- **FR-027**: A material benefit MUST be recorded as a named item and MUST NOT be modeled
  further. A ship share is a named item, not a loan schedule.
- **FR-028**: The consequence chain MUST stop at the numbers on the sheet. Nothing beyond
  injuries, medical bills and the debt they create, the aging-crisis payment, and the pension
  is carried into the character.

#### The character

- **FR-029**: The generated character MUST carry: the seed that reproduces it on its own, its
  name and, where the name was rolled, the parts it was composed from, the rank title FR-047c
  attaches to its rendered name, its characteristics with their
  current scores, its skills with their levels including level zero, every career it served
  with the terms served and rank reached in each, its age, its funds, its outstanding debt, its
  pension, its named benefit items, and its generation history. This list is exhaustive, and
  every field on it is a field FR-050 requires machine-readable output to emit unconditionally.
- **FR-030**: The generation history MUST record every step of the walk in the order it
  occurred, each step naming what was decided or thrown and what followed. The history is what
  makes a surprising sheet diagnosable as a wrong engine rather than interesting dice, and it
  MUST be complete enough that every characteristic, skill, career, credit, and item on the
  sheet traces to a step that produced it.
- **FR-030a**: Each history step MUST be a structured record whose parts are separately
  addressable: at minimum which kind of step it was, the career and term it occurred in where
  those apply, what was thrown or decided, and what followed. A step MUST NOT be recorded only as
  a line of prose. Machine-readable output MUST emit the parts, and the fuller text rendering
  MUST compose its line from them, so that the text form is a rendering of the record rather than
  the record itself. No field of a step may hold a line composed from the step's other parts.
  That is what makes "the text form is a rendering of the record" checkable from the record's
  shape rather than by someone reading a stored string and judging whether it looks composed.
  Under any other reading, SC-004's consistency audit and SC-005's traceability check would have
  to parse sentences, and a consumer of the machine-readable history could not query it.
- **FR-031**: The character MUST be reachable programmatically as a value, so that a consumer
  can read it without parsing any rendering of it.

#### Rules data this feature adds

- **FR-032**: The system MUST ship eight careers: the six the Draft table names, plus Drifter,
  plus one career from the professional tier. This is the smallest set in which the draft is
  the source material's own roll over six real careers, every name in the shipped data
  resolves, and the loader's strict validation needs no exception. A reduced draft table with a
  smaller die, or a tolerant draft falling through to Drifter, were both rejected: the second
  writes a rule into the engine that has no reason to exist once the data is complete.
- **FR-033**: Between them, the shipped careers MUST exercise every shape the engine handles:
  a career with a commission and a career without, all three medical tiers, Drifter's
  always-available and re-enterable flags, and every row of the Draft table.
- **FR-034**: The career schema MUST gain the facts the generator needs and the loader does not
  yet carry: the medical-bills tier, and the flags that mark a career always available as a
  fallback and re-enterable. Facts about one career live in that career's file; facts that
  order or span careers live in universal data.
- **FR-035**: The advancement throw MUST become optional in the career schema, absent for a
  career that offers no advancement, which together with an absent commission throw is what
  FR-009 reads as two skill rolls a term.
- **FR-036**: The career schema version MUST be raised, and the shipped career that predates
  this feature MUST be brought to the new version. Per-kind schema versioning exists for
  exactly this: a user-supplied file of an untouched kind MUST NOT be invalidated by this
  change.
- **FR-037**: The universal chargen tables MUST be shipped as per-kind files in a directory of
  their own, one kind per file, rather than combined into one file. Because an override
  replaces whole files, a referee with a house aging table MUST NOT have to restate the draft
  table to get it. The kinds this feature adds are the Draft table, the aging table, the
  Survival Mishaps table, the background and homeworld skill tables, the medical-bill tiers,
  and the scalar chargen parameters that order the walk.
- **FR-038**: Every rules constant the walk depends on MUST live in data and MUST NOT be held
  in engine code. The full list this feature binds is: the characteristic roll; the background
  skill count rule and the characteristic it reads; how many background skills come from the
  homeworld lists before the education list is reached; the term cap; the years a served term
  costs; the years a mishap-ended term costs; the age at which the walk begins; the age at
  which aging begins; the qualification penalty per career already entered; how many times one
  character may be routed to the draft (FR-004); what basic training grants on a first career
  and on a later one (FR-007a); the unmodified survival result that always fails (FR-008a); the
  four skill-roll counts of FR-009; whether a drafted character is barred from a first-term
  commission (FR-012a); the continuation throw and its target; the benefit-roll count rule and
  its rank thresholds; the die the benefit tables are read with; the throw and target that
  decide whether a roll is taken as cash or as a material benefit (FR-016); the cap on rolls
  taken as cash and the rank modifier on material rolls (FR-016); the cash benefit modifier;
  the pension minimum, base, and per-term increment
  (FR-018); the aging-crisis throw, its multiplier, and the score settling it restores to
  (FR-021); and the per-point cost of restoring a characteristic (FR-025). The list is stated
  in full rather than as examples because a constant it omits is a constant SC-013 does not
  reach: an enumeration is what gives a check something to fail against, and any constant the
  walk turns out to need that is not on this list is itself a defect in this requirement.
  The die a universal chargen table is read with — the Draft table's, the aging table's, the
  Survival Mishaps table's, the medical tiers' — is not enumerated here because it is declared
  by that table's own file as part of that table's shape, which FR-037 already puts in data. The
  distinction is which file a constant lives in, never whether it lives in one: no die anywhere
  in the walk is held in engine code, and a table whose die the engine supplied would fail this
  requirement as surely as a term cap would.
- **FR-039**: The characteristics registry MUST gain the characteristic modifier bands, the
  pseudo-hex letters, the bottom of the range those letters cover, and a class for each
  characteristic (the shipped data distinguishes physical from mental), all of which are facts
  about characteristics rather than about chargen or about task resolution. The class is
  load-bearing rather than decorative: a table that reduces "three physical characteristics" or
  "one mental characteristic" cannot resolve without it, and FR-038 forbids holding it in
  engine code. The bottom of the range is what a reduction floors at. The modifier bands MUST
  move out of the task parameters, both affected kinds MUST have their schema versions raised,
  and no task check result may change as a consequence.
- **FR-040**: The skills registry MUST gain the skills the background and homeworld tables
  name and the specialties the cascade rule chooses among, so that every skill any shipped
  table can grant resolves.
- **FR-040a**: Every characteristic class any table in force names MUST resolve to a class the
  characteristics registry declares, and a name that does not MUST fail the run before any
  character is produced, naming it. Without this rule an effect reading "reduce one physical
  characteristic" against a registry that spells the class differently reaches no
  characteristic and silently does nothing, which is a wrong character rather than a failed
  run.
- **FR-041**: Every packaged data file's basename MUST be unique across the whole packaged
  tree at any depth, because an override file is positioned by its basename regardless of the
  directory it sits in. This constraint binds every file this feature adds and every file the
  feature after it adds.
- **FR-042**: Every data file this feature ships MUST carry a licensing designation, and the
  designation MUST match what the file actually is. A file derived from the source material
  carries the Open Game Content designation and MUST be covered by the copyright notice chain
  that travels with the package, which MUST be adjusted in the same change that adds the files
  so that it covers every Open Game Content file and nothing else. Because the chain as it
  stands claims every data file the package ships, that adjustment is a **narrowing**: it must
  describe what it covers precisely enough to exclude the name tables while still reaching every
  file derived from the source material. A
  file that is not derived from the source material, which the name tables of FR-043a are the
  first of, MUST carry the project's own GPL-3.0 designation, MUST NOT carry the Open Game
  Content designation, and MUST NOT be claimed by the notice chain. No data file this feature
  ships may contain either Product Identity string, whatever its designation.
  These designation rules bind **shipped** files only. A file supplied as an override carries
  neither designation and MUST NOT be required to carry one: this project's licensing
  obligations are about what it redistributes, and a house rule redistributes nothing.
- **FR-042a**: The automated licensing checks MUST distinguish the two designations rather than
  requiring the Open Game Content designation of every data file. Until this feature every
  shipped data file was Open Game Content, so the existing checks read "every data file" and
  "every Open Game Content file" as the same set. They stop being the same set here, and a check
  that keeps the old reading either fails on the name tables or, if relaxed to pass them, stops
  proving the designation for the files that genuinely need it.
- **FR-043**: The generator MUST consume rules content exclusively through the validated
  loader, and MUST NOT read, search, or fall back to any content the loader did not supply.
  Name tables are content the loader supplies, held to the same validation, override, and
  provenance rules as any other data file, and the generator MUST NOT reach them by any other
  route.

#### Names

- **FR-043a**: The system MUST ship one table of given names and one table of surnames per
  region, as data files under the loader's ordinary rules, so that a referee replaces or adds
  a name table exactly as they replace or add any other rules data.
- **FR-043b**: The given names table MUST hold names that are gender neutral, meaning names
  commonly borne across genders or not gender-marked in the languages they come from. The
  system MUST NOT model a character's gender at any point, and no name table may carry a gender
  field, so that a later reading cannot reintroduce a distinction this table exists to avoid.
- **FR-043c**: The shipped surname regions MUST be North America, Central America, South
  America, Africa, Asia, Europe, and indigenous peoples not covered by the other six. Each
  region MUST be its own file, because an override replaces whole files and a referee changing
  one region's surnames MUST NOT have to restate the other six.
- **FR-043d**: Each entry in the indigenous-peoples surname table MUST name the people it comes
  from. That table collects distinct and unrelated naming traditions rather than one, and
  without the attribution the file is a list labelled with a category that describes none of
  its entries.
- **FR-043e**: Every name table MUST record the source its entries were drawn from, identified
  precisely enough that a reviewer can find that source and read its terms. An admissible source
  is one whose terms permit redistribution of the names without a restriction this project's own
  GPL-3.0 designation would contradict: a public-domain or open-data name list, a government or
  census release, or a source under a license permitting redistribution. A source that forbids
  redistribution, or whose terms cannot be established, MUST NOT be used. This is the same
  obligation the Open Game Content designation discharges for the source material, applied to
  content that designation does not reach. The criterion is stated rather than left as an
  adjective because the check it enables is a review one, in which a reviewer follows the
  recorded source and reads its terms, and a review needs something definite to apply.
- **FR-043f**: A rolled surname MUST be drawn by selecting a region first, with every surname
  table in force equally likely, and then a surname from within that region. How many entries a
  table holds MUST NOT decide how often that region appears. Weighting MUST be over the tables
  in force rather than over the shipped seven, so that an override adding a region gives it the
  same weight as each of the others.
- **FR-043g**: The given name and the surname MUST be rolled independently of one another, and
  neither MUST be correlated with any other fact about the character. A name is not a claim
  about where a character is from, what career they served, or anything else on the sheet.
- **FR-043h**: The system MUST reject a name table with no entries, naming the file, rather
  than producing a character with no given name or silently redistributing a region's weight
  among the others.
- **FR-043i**: The given names table MUST hold at least sixty entries and each surname table at
  least forty, so that a batch of the size a referee actually asks for does not read as a list
  of repetitions. These are floors on the shipped tables and MUST NOT be imposed on an override,
  which is the referee's business to size.
- **FR-043j**: No two surname tables in force may declare the same region, and at least one
  surname table MUST be in force. Either condition MUST fail the run before any character is
  produced, naming the files at fault. A duplicated region would quietly take two shares of a
  weighting FR-043f takes over tables rather than over names, which is the silent failure
  FR-043f exists to prevent; no table in force leaves no surname to draw at all.

#### Rendering

- **FR-044**: The default human-readable rendering MUST be the source material's Universal
  Character Format, with a line the character has nothing to put in omitted entirely rather
  than emitted blank. Its lines are enumerated here rather than left as "its defined lines",
  because a rendering SC-009 pins byte for byte cannot have its shape held only in a document
  this specification does not ship: the name with any attached rank title, then the
  characteristic profile, then the age; the careers, then the funds; the skills; the species
  traits; and the significant property. Fields within a line are tab separated.
- **FR-044a**: The species-traits line MUST never be emitted, every generated character being
  human, so it is the line that is always inapplicable. The significant-property line MUST
  carry the character's named benefit items and MUST be omitted entirely when the character
  holds none, so it is the line that varies and the one SC-009 requires a reference with and a
  reference without.
- **FR-045**: The default rendering MUST show skills of level zero, and MUST write funds with
  the currency prefix and with thousands separators.
- **FR-046**: Where the format is silent or contradicts its own single example, the rendering
  MUST resolve it as follows, and these resolutions MUST hold in both text renderings: skills
  in alphabetical order as the format states rather than in the example's order, sorted
  locale-independently so that a seed renders identically on any machine; careers separated by
  comma in the order they were entered; a cascade specialization written qualified by its
  parent skill so a reader can find it in the registry; the benefit items on the
  significant-property line separated the same way as the skills, with repeats collapsed to the
  item's name and a count and the line sorted by the same locale-independent key, so that it is
  as stable across machines as the skills line is; and exactly one tab between fields.
- **FR-047**: Every character MUST have a personal name. A name supplied by the caller MUST be
  used verbatim; where none is supplied, one MUST be rolled per FR-043a through FR-043j. The
  rank title from the ladder the character reached MUST be attached to the rendered name, since
  that is the difference between a named officer and an anonymous profile. The title MUST be
  written before the name and separated from it by a single space, and a character holding no
  title MUST have the line begin with the name itself and no leading separator. The title MUST
  be attached whether the name was rolled or supplied: it is a fact about the career the
  character served, not about how they came to be named.
- **FR-047a**: A rolled name MUST be written as the given name, a single space, and the
  surname, and MUST NOT be reordered, abbreviated, or otherwise adjusted to suit the naming
  conventions of the region a surname came from. The generator composes two independently drawn
  parts and does not claim to be modelling any one tradition's name order.
- **FR-047b**: Whether a character's name was supplied or rolled MUST NOT change any field of
  that character for a given seed other than the name itself and the name parts of FR-047d, which
  record how a rolled name was composed and are empty for a supplied one. A caller who names a
  character gets the character that seed produces, named; not a different character.
- **FR-047c**: Where a character holds a titled rank on more than one ladder, the title attached
  MUST be the one from the most recently served career in which the character holds a rank the
  ladder names a title for. A career that left the character untitled MUST NOT erase a title an
  earlier career granted. The rule MUST NOT compare a rank on one ladder against a rank on
  another, because no shipped data declares how ladders compare and any such comparison would be
  a rule held in engine code.
- **FR-047d**: The character MUST carry one name string that is always present and is what every
  rendering writes. Where the name was rolled, the character MUST additionally carry the given
  name, the surname, and the region the surname was drawn from, recorded separately. Where the
  caller supplied the name, those three MUST be empty, and the supplied name MUST NOT be split,
  reordered, or otherwise decomposed to fill them, since a supplied name may be one word or
  several and FR-047 requires it verbatim. The rank title MUST be carried as a field of its own
  and MUST NOT be part of the name string, so that a consumer can render the name without the
  title and so that SC-018's field-by-field comparison has a field to compare rather than a
  prefix to strip. Machine-readable output MUST carry all five fields
  unconditionally per FR-050, the three name parts present and empty for a supplied name and
  the title present and empty for a character no career titled.
- **FR-048**: Noble titles MUST NOT be rendered, on either the name or elsewhere.
- **FR-048a**: In either text rendering, consecutive character sheets in a batch MUST be
  separated by exactly one blank line and by nothing else. No index, count, seed, or other header
  may be written between or above sheets, because every byte on standard output in text mode
  belongs to some sheet. Rendering a batch of one MUST therefore produce exactly the bytes that
  rendering the single character generated from the same seed produces, with no separator
  before it and none after it.
- **FR-049**: The system MUST provide a second, fuller text rendering that carries what the
  Universal Character Format has nowhere to put: the outstanding debt, the pension, and the
  generation history.
- **FR-050**: Machine-readable output MUST carry every field of the character unconditionally,
  including the history, the debt, the pension, the seed, and the provenance, present whether
  or not each is non-empty, so that a consumer never has to infer a field's absence.
- **FR-050a**: Machine-readable output MUST have one shape whatever the count. Every run MUST
  emit a single document carrying the characters as a list, a list of one when one character was
  asked for, so that a consumer writes one code path rather than branching on how many characters
  it requested. The master seed and the provenance MUST sit at the top level of that document,
  and the package version MUST be reachable from the top level without descending into any
  character: the provenance object already carries it, and carrying it there rather than
  beside it keeps one version in the document rather than two that can disagree. Each
  character MUST carry the derived seed that reproduces that character alone, so that a consumer can tell the seed a referee quotes for the table from the
  seed that regenerates one person.
- **FR-051**: In text mode, standard output MUST carry exactly the character sheet and nothing
  else, and the seed, the package version, and the provenance MUST be written to standard
  error. Redirecting the command's output MUST therefore produce a file that is a character
  sheet, while both the rule that generators echo their seed and the rule that provenance
  always renders are still satisfied. The seed written there is the master seed and only the
  master seed. The derived seeds FR-050a puts on each character MUST NOT be written to standard
  error, because a batch of twelve would put twelve seeds there and the one a referee quotes
  for the table is the master.

#### Command-line surface

- **FR-052**: The system MUST provide an `npc` command that generates characters.
- **FR-053**: That command MUST accept a seed, a count, a name, an override location for rules
  data, a choice of human-readable or machine-readable output, and a choice between the default
  and the fuller text rendering.
- **FR-053a**: A supplied name together with a count greater than one MUST be refused, since a
  name names one character. Applying it to all of them
  or to the first alone would each silently discard part of what was asked for. The refusal MUST
  be a property of the capability rather than of the command line: the library MUST reject the
  combination on the same terms, and the command MUST report it as a usage error naming both
  options. FR-055 requires every capability reachable programmatically, and a rule enforced only
  at the command line is a rule a library consumer does not get.
- **FR-053b**: Where no seed is supplied, the system MUST draw one from a source outside the
  seeded generator and MUST report it wherever FR-051 and FR-050a report a seed. That draw is
  the one point in this feature exempt from FR-056, and the exemption is what makes it useful: a
  caller who wants a different character each run omits the seed, and reproduces any run by
  quoting back the seed it reported.
- **FR-053c**: A supplied name MUST be non-empty and MUST NOT consist only of whitespace, and
  one that is MUST be refused as a usage error naming the option. FR-047 requires every
  character to carry a personal name and requires a supplied name verbatim, and an empty string
  honors the second at the cost of the first. Rolling a name instead was rejected because it
  makes an empty string mean the opposite of what it says.
- **FR-053d**: Requesting machine-readable output together with the fuller text rendering MUST
  be accepted and MUST NOT change the emitted document. Machine-readable output already carries
  every field unconditionally under FR-050, so the fuller rendering has nothing to add to it and
  there is no wrong outcome to protect a caller from. This is the one place a request for more
  than the tool can distinguish is accepted rather than refused, and it is accepted because both
  readings deliver everything.
- **FR-054**: That command MUST exit zero when it produces characters and non-zero when it
  cannot, with the choice of output mode affecting neither outcome, and MUST report the reason
  on standard error when it cannot. A run that cannot produce characters MUST write nothing at
  all to standard output: no partial sheet, no empty document, and no sheet carrying a caveat.
  Redirecting a failed run's output MUST therefore produce an empty file rather than a file that
  reads as a character sheet, which is the same commitment FR-051 makes for a successful one.
- **FR-055**: Every capability in this feature MUST be reachable programmatically without
  invoking the command line, so that the command remains a thin consumer of the library.

#### Reproducibility

- **FR-056**: A seed, a package version, and a data set MUST together determine a character
  exactly. No part of the walk may draw on any source of variation outside the seeded
  generator, including the clock, the environment, the locale, or the order in which any
  unordered collection happens to be traversed.
- **FR-056a**: A rolled name MUST be drawn from the seeded generator like every other decision
  in the walk, and MUST satisfy FR-047b: for a given seed, the character produced with a
  supplied name and the character produced with none MUST be identical in every field but the
  name and the name parts. The requirement is the property, not any particular arrangement that
  delivers it. The failure it exists to forbid is worth naming because it is what the obvious
  implementation does: rolling the name from the walk's own draws makes supplying a name shift
  every draw after it, so the same seed yields a different person depending on whether it was
  named.
- **FR-056b**: The order in which the walk draws from the seeded generator is part of what a
  seed reproduces. A change that reorders two draws, adds one, or removes one changes the
  character every seed produces. Such a change is permitted, and MUST be flagged in the
  changelog as breaking. A seed therefore reproduces a character within one package version and
  one data set and promises nothing across versions, which is what a referee quoting a seed to
  another referee has to be told, and what SC-001's "one package version" already assumes
  without saying.
- **FR-057**: A seed and a count MUST determine a batch exactly, and the first characters of a
  larger batch MUST equal a smaller batch from the same seed, so that a count is a request for
  more of one sequence rather than for a different sequence. The character at the first position
  of a batch MUST be the same character, field for field, as the single character that seed
  produces on its own. FR-048a states the consequence for the rendered bytes; this states the
  property those bytes follow from, so that the identity is testable on the characters
  themselves and not only on a rendering of them.
- **FR-058**: A run whose rules data came from an override MUST report that provenance
  alongside the seed, so that a character produced under house rules is never mistaken for one
  a seed and a package version alone would reproduce.

### Key Entities

- **Character**: The finished person the generator produces. Carries the seed that reproduces
  it alone; a name, always present and
  always what renders, together with the given name, surname, and surname region it was composed
  from when the name was rolled and empty when the caller supplied it; the rank title attached
  to the rendered name, carried separately from the name string; characteristics,
  skills with levels, the careers served with terms and rank in each, age, funds, outstanding
  debt, pension, named benefit items, and the generation history. Always named, always alive,
  always internally consistent.
- **Generation history**: The ordered record of the walk that produced a character. Every step
  is a structured record with separately addressable parts naming which kind of step it was, the
  career and term it fell in where those apply, what was decided or thrown, and what followed. It
  is the evidence by which a surprising sheet is diagnosed, and every number on the sheet traces
  to a step in it. The text rendering of a step is a rendering of the record, never the record.
- **Career service**: One character's time in one career: which career, how many terms, which
  ladder they were on and what rank they reached, whether they were commissioned, how they
  entered, how the service ended, and what it earned at
  mustering out. A career may declare more than one ladder; a character is on one at a time,
  entering on the ladder the career names for entry and moving to the commissioned ladder if a
  commission succeeds. A character has one or more services, in the order they were entered.
- **Term**: One period of service, comprising a survival throw, a commission and advancement
  attempt where the career offers them, one or two skill rolls, and aging. Counts toward the
  cap whether served out or ended by a mishap, and costs a different number of years in each
  case.
- **Mishap**: The consequence of a failed survival throw, drawn from the Survival Mishaps
  table. Ends the term and the career, may reduce characteristics, and never kills.
- **Debt**: An amount the character owes, arising from an aging crisis or from medical bills.
  Settled from mustering-out proceeds; whatever remains is carried on the character, separate
  from funds, which never go negative.
- **Benefit item**: A material mustering-out benefit, recorded as a name and nothing more. Not
  modeled, not priced, not converted.
- **Universal chargen table**: A rules table that orders or spans careers rather than
  belonging to one: the Draft table, the aging table, the Survival Mishaps table, the
  background and homeworld skill tables, the medical-bill tiers, and the scalar parameters of
  the walk. One kind per file, so that overriding one does not require restating the others.
- **Career definition**: Extended from the previous feature by the medical tier it charges at,
  whether it is always available as a fallback, and whether it may be re-entered. Its
  advancement throw becomes optional, and a career declaring neither commission nor advancement
  is by that fact a career granting two skill rolls a term.
- **Name table**: A shipped list of names, either the one table of given names or one region's
  table of surnames. Not derived from the source material, and so the first shipped data the
  Open Game Content designation does not cover. Records the source its entries came from;
  carries no gender field; and, for the indigenous-peoples table, names the people each entry
  comes from.
- **Universal Character Format**: The source material's printed character sheet, and the
  default human-readable rendering. Five tab-separated lines, inapplicable lines omitted,
  level-zero skills shown, funds prefixed and separated. Has nowhere to put debt, pension, or
  history, which is why a fuller rendering exists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

Every criterion below is verified in the project's complete test run. A criterion whose check
is excluded from the selection run routinely, because it is slow, MUST still run in the
complete one, and a check that is skipped rather than run does not satisfy the criterion it
belongs to. This is stated once here because two of the criteria below fix sample sizes large
enough that the question arises, and because a criterion nothing is obliged to run is a
criterion that proves nothing.

- **SC-001**: One seed, one package version, and one data set produce one character, verified
  by generating the same seed repeatedly and comparing every field and both rendered forms byte
  for byte, with zero differences across every seed tested.
- **SC-002**: One seed and one count produce one batch, and the first characters of a batch of
  any size equal a batch of any smaller size from the same seed, verified across several
  seeds and several count pairs.
- **SC-003**: Over a large sample of seeds, one thousand or more, every seed produces a living
  character, and none produces an error, a partial character, or a character missing any
  required field. No seed is excluded from the sample for any reason.
- **SC-004**: Over that same sample, every character's sheet is internally consistent, verified
  as an automated audit rather than by inspection: age matches the terms served and how each
  ended, every rank held exists on a ladder of a career the character actually joined, every
  skill traces to a table the character could reach in a term they served or to a grant they
  were entitled to, the benefit rolls taken match the terms served and the rank reached, a
  pension where one was received matches the terms served in a single career rather than the
  terms served in all of them, funds
  are non-negative, and no consequence appears that no step in the history produced.
- **SC-005**: Every characteristic, skill, career, credit, and item on a generated sheet traces
  to a recorded step in that character's history, verified as an automated check over the
  sample that reads the steps' named parts rather than parsing any rendered text, so that a
  surprising sheet can be diagnosed from output alone.
- **SC-006**: Over that same sample, ages are spread rather than parked at the cap: characters
  finish with a range of term counts, at least five distinct counts occur, and no more than one
  character in four reaches the term cap. The cap is read from the chargen parameters rather
  than written as seven here, for the reason SC-008 gives for the medical tiers: FR-038 puts it
  in a file a referee may edit, and a criterion that hard-codes it would contradict the
  requirement it is checking and would fail on a data set it has no business judging.
- **SC-007**: Over that same sample, multi-career characters occur, with characters carrying
  two careers and characters carrying three both present, so that the multi-career path is
  exercised by ordinary generation rather than only by a contrived seed.
- **SC-008**: The eight shipped careers between them exercise every shape the engine handles,
  evidenced over the sample: a career with a commission and a career without, every medical
  tier the shipped data declares, Drifter entered as a fallback and Drifter re-entered, and
  every row of the Draft table reached. A shape no shipped career exercises is a shape nothing
  proves. The tiers are counted from the data rather than fixed at three here, because FR-037
  puts their definitions in a file a referee may extend and a criterion that hard-codes their
  number would contradict the requirement it is checking.
- **SC-009**: The default rendering is byte-faithful Universal Character Format, verified
  against committed reference outputs covering, between them, a character with and without each
  omissible line, a character holding a rank title, a character holding none, a
  multi-career character, a multi-career character holding a titled rank in an earlier career
  and none in a later one, and a character carrying a cascade specialization.
- **SC-010**: The fuller text rendering carries the outstanding debt, the pension, and the
  history for a character that has all three, and the machine-readable output carries every
  field unconditionally, verified against a character for which several of those fields are
  empty. A run of one character and a run of twelve emit the same document shape, verified by
  checking both against one contract, and the derived seed a batch reports for a character
  regenerates that character alone.
- **SC-011**: Redirecting the command's standard output produces a file that is exactly a
  character sheet, containing no seed line, no version, and no provenance, while all three
  appear on standard error in the same run. The same holds for a batch, whose redirected output
  is exactly its sheets with one blank line between consecutive sheets and no other text,
  verified against a committed batch reference.
- **SC-012**: The output cannot depend on the machine's locale, verified two ways, both
  required. First, an automated check asserts that no part of the library consults the
  platform's locale at all; this check runs wherever the suite runs and is what makes the
  criterion unfalsifiable by omission. Second, the same seed is generated under at least one
  locale whose collation differs from the default and the bytes are compared. Where no such
  locale is installed the comparison reports that it could not run, and a comparison that did
  not run does **not** satisfy this criterion; the first check carries it alone. Stating this
  matters because the obvious reading, a single cross-locale comparison, is satisfied by a test
  that skips on every machine that runs it.
- **SC-013**: Changing a value in a shipped data file changes the generator's behavior
  accordingly with no code edit, demonstrated for a Draft table row, an aging table entry, a
  Survival Mishaps entry, a career's medical tier, and the term cap.
- **SC-014**: Every seed and check that produced a given task resolution before the
  characteristic modifier bands moved produces an identical one after, compared field by field
  against the reference outputs committed with the previous feature, so that a data
  reorganization changes no result.
- **SC-015**: Every data file this feature adds carries the licensing designation that matches
  what it is, verified by automated checks against the files as read from the installed package:
  every file derived from the source material carries the Open Game Content designation and is
  covered by the shipped copyright notice chain, every name table carries the project's GPL-3.0
  designation and is claimed by neither, no data file contains either Product Identity string,
  and no file carries both designations or none. Every packaged data file's basename remains
  unique across the whole tree.
- **SC-015a**: Adding a data file under either designation without extending the corresponding
  check fails the suite, demonstrated by adding a file of each kind in turn to a copy of the
  package. A check that passes unchanged when a file is added is a check that will pass while a
  name table travels under an Open Game Content notice that does not cover it, or while a career
  table travels under no notice at all.
- **SC-015b**: Every name the generator can produce comes from a table that records where its
  entries were drawn from, every entry in the indigenous-peoples table names the people it comes
  from, no name table carries a gender field, the given names table holds at least sixty entries
  and each surname table at least forty, verified by automated check so that an entry added
  later without its attribution fails the suite.
- **SC-016**: Every behavior in the functional requirements has a test whose expected values
  were written before the implementation existed, evidenced by those values being committed in
  a change that precedes the implementing change and by the test being observed to fail before
  it passes.
- **SC-017**: Every capability in this feature is exercised by at least one test that uses the
  library directly without invoking the command line.
- **SC-018**: Every generated character has a name, verified over the same sample as SC-003
  with no character rendering nameless, and a seed run with and without a caller-supplied name
  produces characters that differ in the name and its recorded parts alone, compared field by
  field.
- **SC-019**: Over a sample of ten thousand rolled names, each surname region's share of the
  sample falls within ten percent, relatively, of an equal share: with seven regions in force,
  between 0.9/7 and 1.1/7 of the sample. The band is stated as a number rather than as
  "narrow" because a tolerance no one has written down is a tolerance the check picks for
  itself. Ten percent is roughly four standard deviations at this sample size, so the criterion
  fails on a weighting mistake rather than on the dice. The check counts the surname region each
  character records (FR-047d) rather than
  recovering it by splitting a rendered name. The shipped tables MUST differ in size by enough
  that weighting taken over names rather than over regions would put at least one region's
  expected share outside that band, so that the mistake this criterion exists to catch fails it
  rather than passing by coincidence.
- **SC-020**: A referee generating an NPC for play needs one command and no follow-up
  question, checked as two automated assertions over the same sample rather than as a
  judgement about how a sheet reads. Completeness: every field the default rendering is
  required to carry is non-empty on every sampled character, so no sheet sends a referee back
  for something the format had a place for. Absence of internals: the default rendering emits
  no seed, no package version, no provenance, no history step, no step kind, no throw, and no
  debt or pension figure — the sample's rendered sheets are searched for each and none is
  found. Stated this way because "everything needed to run the character in a scene" is a
  claim about play that no test can settle, while "the format's own lines are filled and
  nothing from the walk leaks onto them" is the part of it this generator is answerable for,
  and a criterion nothing can fail is a criterion the preamble above already forbids.

## Out of Scope

Each exclusion is deliberate. The reasons are recorded because they determine what later
features must add.

- **The remaining careers**: excluded. Eight ship here because eight is what exercises every
  shape the engine handles; the other sixteen or so are the next feature's job and add data
  rather than behavior.
- **A lethal chargen mode**: excluded, and not selectable. Making it selectable would require
  building and testing an entire death path, in both output modes, for a branch the shipped
  data never takes. The always-living reading is also what makes the seed-to-character walk a
  single fixed-length path, which is what makes reproducibility a property rather than a
  tendency.
- **Psionics and anagathics**: excluded. Both extend the walk with steps and consequences that
  nothing else in the MVP consumes.
- **World and homeworld generation**: excluded. Background skills are therefore drawn over the
  source's tables directly, and the trade-code row is kept as flavor rather than derived from a
  world that was generated.
- **Culturally coherent names**: excluded, while name generation itself is in. The given name
  and the surname are drawn independently and the result is not adjusted to any one tradition's
  name order, conventions, or pairings. Modelling that would require the generator to hold a
  position on which traditions go together, which is a claim about people rather than a rule
  about characters, and the source material supplies nothing to ground it.
- **Any correlation between a name and the rest of the character**: excluded. A name says
  nothing about homeworld, species, career, or anything else on the sheet, and nothing on the
  sheet constrains a name. Homeworld generation is out of scope in any case, so there is nothing
  for a name to be consistent with.
- **Gendered names, gendered titles, and gender itself**: excluded. The given names table is
  gender neutral and the generator models no gender, for the same reason noble titles are
  excluded: the source files gender as pure color, and a generator that picked one would be
  inventing a fact about every character it produced.
- **Non-human species and their traits**: excluded. Every generated character is human.
- **Noble titles**: excluded. Choosing between the source's printed forms requires a gender the
  source itself files as pure color, and emitting only the unparenthesized form would render
  every titled NPC a Baron and never a Baroness.
- **Starting equipment and equipment purchase**: excluded. The consequence chain is cut at what
  moves a number on the sheet, and buying gear is a step past that line.
- **Modeling material benefits**: excluded. A benefit is a named item; a ship share is not a
  loan schedule and a weapon is not a stat block.
- **Forcing a specific career or a specific number of terms**: excluded. Every choice the
  source hands to a player is the generator's, decided randomly or by rule, and an option to
  fix one would add a second walk to test for every one the seed already determines.
- **Editing or re-rolling a generated character**: excluded. The output is a character, not a
  session; a caller who wants a different character uses a different seed.

## Assumptions

House readings, recorded as assumptions rather than as source-material rules, because they are
this project's answers and not the source's:

- **An aging crisis is a debt**, settled from mustering-out proceeds, extending the way the
  source already handles medical and anagathic costs. The alternative reading kills a character
  for want of money they cannot have yet, since money arrives at mustering out. Settling the
  debt buys what the source's payment buys: the characteristics the crisis covered come back off
  the floor. A crisis whose debt is never settled leaves them floored, which is the always-living
  reading's price and is recorded on the character rather than hidden.
- **Debts settle in the order they arose**, and a medical bill only partly covered restores the
  points the covered amount pays for. Which points those are is a decision the walk makes and
  records, rather than the order a collection happens to be traversed in, because FR-056 forbids
  the second and a partly restored character has to be reproducible like any other.
- **A Survival mishap costs two years rather than four**, while still counting toward the term
  cap and toward the aging modifier, and forfeiting that term's benefit roll. A term cut short
  should cost less time than one served out.
- **The rank-zero bonus skill is granted on entering a career.** Under any other reading it is
  data nothing can reach.

Places this project departs from the source material deliberately. Each is a rule the source
prints and this generator does not follow, collected so that review can tell a departure from
an oversight and so that a later feature does not "fix" one back:

- **No character dies.** A failed survival throw resolves on the optional Survival Mishaps
  table rather than killing (FR-019), and an aging crisis becomes a debt rather than a death
  (FR-021). This is the organizing commitment of the feature.
- **A characteristic floors rather than killing or going negative** (FR-039, and the edge cases
  above). The source separately forbids a score dropping permanently below one, so the floor is
  looser than the source's own rule rather than tighter.
- **A mishap-ended term costs two years, not four**, while still counting toward the term cap
  and the aging modifier and still forfeiting that term's benefit roll (FR-020).
- **A natural result on the re-enlistment throw does not override the term cap.** The source
  lets one force a further term; FR-014 musters the character out regardless. A cap that
  something overrides is not a cap, and the override would put characters past the point the
  aging table's own arithmetic covers.
- **Noble titles are never rendered** (FR-048), and **gender is not modeled at all** (FR-043b),
  for the same reason: the source files both as color, and a generator picking one would be
  inventing a fact about every character it produced.

Places the source material is silent or contradicts itself, resolved here:

- **One background skill means one homeworld skill**, rather than the two the general rule
  would give or the none a strict reading would give.
- **Drifter is thrown for when selected normally and automatic when entered as the fallback**,
  so that the fallback is a floor rather than a second chance at the same throw.
- **"Retired" on the cash benefit modifier means having qualified for the pension**, which is
  the only reading under which the modifier has a determinate trigger.
- **The specific mustering-out rule governs the benefit count** over the looser phrasing of the
  summary checklist, on the general principle that the specific governs the general.
- **The qualification penalty counts careers entered, not careers served.** The source says
  "entered" in one place and "in which you have served" in another. Entered wins, and this
  specification uses that word throughout (FR-015, FR-038).
- **A pension is earned in a single career.** The source's wording is "5 or more terms in a
  single service", and the reading that adds terms across careers would pay a character who
  never stayed anywhere long enough to be pensioned by anyone.

Defaults chosen where the decisions brief did not specify:

- **The continuation decision is an even chance each term**, held as a parameter in the chargen
  data rather than in code, so a referee who wants longer or shorter careers can tune it. The
  brief requires only that it be random; an even chance is the simplest random and the one that
  spreads ages without preferring either end.
- **Per-character seeds in a batch are derived deterministically from the master seed and the
  character's position**, which is what makes FR-057's prefix property hold and what lets a
  referee quote one seed for a whole table. The derived seed is reported on each character in
  machine-readable output (FR-050a), so a referee who wants one person out of a table has the
  seed that reproduces that person alone.
- **In machine-readable mode the emitted document carries the seed, the version, and the
  provenance in-document**, and they are not additionally echoed to standard error, so that the
  document is self-contained and the stream is not split. FR-051's routing to standard error
  is a text-mode arrangement, made so that a redirected sheet is exactly a sheet.
- **Sixty given names and forty surnames per region are the shipped floors**, chosen so that a
  batch of the size a referee actually asks for reads as a list of people rather than a list of
  repetitions: with seven regions those floors put roughly sixteen thousand full names in reach,
  at which a batch of twelve repeats a name well under one time in a hundred. The floors bind
  the shipped tables only. Larger tables are welcome and no maximum is imposed.
- **The seventh region is a collection rather than a place.** "Indigenous peoples not covered by
  the other six" is the category the request named, and it is kept because the alternative, a
  continental bucket per tradition, would need a partition of the world's naming traditions that
  this project has no standing to draw. Requiring each entry to name its people (FR-043d) is
  what keeps the category from flattening what it holds. If authoring the table shows a better
  partition, adopting it changes the shipped region list and nothing else in this specification,
  because FR-043f weights over the tables in force rather than over a fixed seven.
- **Oceania and Australia are reached through the seventh table** rather than through regions of
  their own, since the six named regions omit them. This follows from the request's own list and
  is recorded because it is the omission most likely to be read as an oversight.
- **The professional-tier career that ships is chosen during planning**, constrained only by
  FR-033: it must be whichever career completes the coverage the other seven leave incomplete.
- **The medical-tier definitions are universal data** while the tier a career charges at is in
  that career's file, following the brief's own principle that a fact about one career lives in
  that career's file and a fact that spans careers lives in universal data.
- **Rules data is trusted input**, inherited from the previous feature: an override is named
  deliberately by the person running the tool, so validation catches mistakes rather than
  defending against a hostile file.

Dependencies:

- **The validated rules loader from the previous feature is in place** and is the only route by
  which this feature reaches rules content, including its override composition, its strict
  validation, and its provenance reporting.
- **The seeded generator and the dice engine from the first feature are in place** and are the
  only source of randomness in the walk.
