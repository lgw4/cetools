# Feature Specification: Acceptable Values at Interactive Ship Prompts

**Feature Branch**: `001-prompt-acceptable-values`

**Created**: 2026-07-29

**Status**: Draft

**Input**: User description: "The interactive ship generation mode needs to provide acceptable values where appropriate when prompting. For example, for armor, the prompt should show titanium steel, crystaliron, and bonded superdense as options, then any addtional options depending on the first selection, for example reflec, self-sealing, and stealth."

## Clarifications

### Session 2026-07-29

- Q: Naming all sixteen revisable answers takes about three lines, breaking the two-line prompt
  budget. Which way is that resolved? → A: The revise prompt is exempt from the two-line budget; it
  names all sixteen and wraps as far as it needs.
- Q: Where does a value's displayed spelling come from, given two of the thirty-five values are
  hyphenated in the SRD? → A: Derived mechanically from the stored key, underscore to space, always;
  the hyphenated spelling is still accepted as input.
- Q: How is "the displayed set is the accepted set" to be stated so it can be checked, given that
  prompts accept spellings and free-form parts they never display? → A: Over distinct values—each
  named once in the displayed spelling, nothing named refused—with alternate spellings, case, and
  the free parts of a compound answer outside the count.
- Q: Do the open questions—staterooms, name, purpose—name the `none` they accept? → A: A question
  names `none` unless Enter's advertised default is already `none`; staterooms and name name it,
  purpose does not.
- Q: Does the computer question, whose models are a closed table of 1 through 7, name them? → A:
  Yes; it names the models as a range and names `none`, like every other closed set.

## User Scenarios & Testing *(mandatory)*

The referee is designing a ship at the table with `cetools ship generate --interactive`. Today
every question shows only what pressing Enter does. A question with a closed set of answers—armour
material, hull configuration, electronics package, turret mount—gives no hint what those answers
are, so the referee either already knows the SRD tables by heart, guesses and reads the refusal to
learn the list, or leaves the field to the dice because pinning it costs more attention than it is
worth. The refusal already prints the acceptable values; this feature moves that knowledge to
where the decision is made.

### User Story 1 - Every closed question names its answers (Priority: P1)

A referee is asked about armour and reads, in the same line as the question, that the answers are
titanium steel, crystaliron, bonded superdense, or `none`. They pick one without leaving the
session, consulting the SRD, or spending a wrong answer to find out.

**Why this priority**: This is the reported gap, and it is the whole of the value for the majority
of questions in a session. Delivered alone it makes the wizard usable by a referee who does not
have the ship-design tables memorised, which is the population the wizard exists for.

**Independent Test**: Run an interactive session, press Enter through it, and read the prompts on
stderr. Every question whose answers come from a table names them. No other behaviour needs to
change for this to be verifiable and valuable.

**Acceptance Scenarios**:

1. **Given** an interactive session at the armour question, **When** the prompt is displayed,
   **Then** it names titanium steel, crystaliron and bonded superdense, names `none`, and says
   what Enter does.
2. **Given** an interactive session at the configuration question, **When** the prompt is
   displayed, **Then** it names distributed, standard and streamlined.
3. **Given** an interactive session at the electronics question, **When** the prompt is displayed,
   **Then** it names every tabulated package, including `standard`.
4. **Given** an interactive session at the fitting question, **When** the prompt is displayed,
   **Then** it names every fitting the question will accept and does **not** name the small craft
   hangar, which this question cannot install because it never asks for a vehicle's tonnage.
5. **Given** an interactive session at the computer question, **When** the prompt is displayed,
   **Then** it names the tabulated models as a range and names `none`.
6. **Given** a small-craft session, **When** the questions are displayed, **Then** the jump-rating
   and weapon-bay questions are absent as they are today, and no question names an answer that
   ruleset cannot take.
7. **Given** any question in a session, **When** an answer is refused, **Then** the reason is
   still given and the question asked again, exactly as today.

---

### User Story 2 - Hull-dependent questions name what this hull can take (Priority: P2)

A referee pinning a 40-ton small craft is asked for a manoeuvre rating and reads the ratings a
40-ton hull can actually carry beside a power plant and a cockpit—not the ratings the drive table
tabulates in the abstract. The same referee is asked for turrets and reads how many hardpoints
this hull has.

**Why this priority**: The narrowed sets are the answers most likely to be got wrong, because the
correct set is not in any single SRD table—it follows from the hull the referee chose a moment
ago. The engine already computes each of these sets in order to phrase its refusals; this shows
them before the mistake instead of after.

**Independent Test**: Pin a hull class and tonnage, then read the rating, turret-count and
small-craft weapon questions. Each names a set narrowed by that hull, and each set matches what
the question then accepts.

**Acceptance Scenarios**:

1. **Given** a session with hull tonnage pinned, **When** the hull-tonnage question was displayed,
   **Then** it named the tabulated tonnages for the chosen ruleset.
2. **Given** a small-craft session with a tonnage pinned, **When** the manoeuvre-rating question
   is displayed, **Then** it names only the ratings that tonnage can carry beside a plant and a
   cockpit.
3. **Given** a small-craft session with a manoeuvre rating pinned, **When** the power-plant
   question is displayed, **Then** it names only the plant ratings available beside that drive,
   and still states the floor the drives require.
4. **Given** a session where the referee pressed Enter at hull tonnage, **When** a rating question
   is displayed, **Then** it names the ratings available across the whole ruleset and says so,
   rather than implying the eventual hull can take all of them.
5. **Given** a 200-ton starship, **When** the turret question is displayed, **Then** it names the
   counts up to the hull's hardpoints and `none`.
6. **Given** a session that asks which answers to revise, **When** that question is displayed,
   **Then** it names the answers that may be revised.

---

### User Story 3 - Answers may be typed the way they are shown (Priority: P3)

The referee reads "bonded superdense" at the prompt and types "bonded superdense". It is accepted.
So is "bonded_superdense", which is what a design file contains and what a referee who has worked
with the TOML format will reach for.

**Why this priority**: A prompt that displays a value it will not accept is worse than a prompt
that displays nothing, because it invites a refusal the referee cannot diagnose. This story is
what makes Story 1 honest, but it is separable: shown-as-stored spellings would already deliver
Story 1's value, less pleasantly.

**Independent Test**: For every value displayed at every prompt, type it back verbatim and confirm
it is accepted; then type its stored spelling and confirm that is accepted too.

**Acceptance Scenarios**:

1. **Given** the armour question, **When** the referee answers "bonded superdense 15", **Then** it
   is accepted as the bonded-superdense layer.
2. **Given** the armour question, **When** the referee answers "bonded_superdense 15", **Then** it
   is accepted identically.
3. **Given** the turret-mount question, **When** the referee answers "pop-up", "pop up" or
   "pop_up", **Then** all three are accepted identically.
4. **Given** any question, **When** the referee answers in a different case than displayed,
   **Then** it is accepted, as it is today.
5. **Given** an unrecognised answer, **When** it is refused, **Then** the reason names the
   acceptable values in the same spelling the prompt displayed them.

---

### User Story 4 - Armour options can be pinned (Priority: P4)

Having pinned crystaliron at 10%, the referee is asked which armour options to add, and reads
reflec, self sealing and stealth. They answer "reflec stealth" and get both. Pressing Enter adds
none.

**Why this priority**: This is new capability rather than new visibility—these three options exist
in the rules and in the design format but no prompt has ever offered them, so a referee who wants
a stealth-coated hull must abandon the wizard and hand-author TOML. It is last because the other
three stories improve every session, while this one serves the sessions that reach for an option.

**Independent Test**: Pin an armour type and options at the wizard, emit the design as TOML, and
confirm the options are recorded. Nothing in stories 1–3 depends on this.

**Acceptance Scenarios**:

1. **Given** an armour type has just been pinned, **When** the next question is displayed,
   **Then** it names reflec, self sealing and stealth and says Enter adds none.
2. **Given** the armour-options question, **When** the referee answers "reflec stealth", **Then**
   the design carries both options.
3. **Given** the armour-options question, **When** the referee presses Enter, **Then** the design
   carries the armour layer with no options.
4. **Given** the armour question was answered `none`, **When** the session continues, **Then** the
   armour-options question is not asked at all.
5. **Given** the armour question was answered with Enter, **When** the session continues, **Then**
   the armour-options question is not asked, because there is no pinned layer to attach options to
   and the rolled layer is the dice's to furnish.
6. **Given** the armour-options question, **When** the referee names the same option twice,
   **Then** it is refused with the reason and asked again.
7. **Given** a session in which armour was revised, **When** the armour question is re-asked,
   **Then** the options question follows it under the same rules.

---

### Edge Cases

- **A hull with nothing to offer**: if a narrowed set turns out to be empty for the hull the
  referee pinned, the question must not display an empty list as though it were a choice. It says
  the hull can take none of them and leaves the field to generation.
- **Tonnage left to the dice**: the ratings question then covers every hull of the ruleset. The
  prompt must not present that wider set as this ship's, since generation may still refuse the
  answer once a hull is drawn—the existing behaviour, now stated where the referee decides.
- **A long list**: the tabulated hull tonnages and the fittings are the longest sets a two-line
  prompt has to carry. A prompt must stay readable rather than wrap into a paragraph, so evenly
  spaced numeric runs are shown as a range rather than enumerated item by item. The revise
  question's sixteen answers are longer than either and cannot be shortened without taking away an
  answer the referee may revise, so that one prompt wraps instead.
- **A value the input layer accepts but assembly refuses**: fuel scoops on a distributed hull, for
  instance. These remain listed, because they are legal answers to the question; the rules refusal
  arrives at assembly with its reason and the revise loop, exactly as today. The prompt's list is a
  statement about what the question accepts, not a promise that the ship will build.
- **A question with no closed set**: staterooms, name and purpose take an open answer. These
  questions gain no list, and must not gain a misleading partial one. They still name the `none`
  they accept where Enter does not already advertise it, since that is one answer rather than a
  partial list.
- **Values pre-answered by a flag**: `--hull` and `--small-craft` suppress their questions, so
  there is no prompt to list values at. When `--hull` disagrees with a chosen hull class, the
  existing message is printed and the question is then asked *with* its list.
- **Screens on a small craft**: the question is still asked and still defaults to `none` rather
  than a roll, and names the screens that may be pinned.

## Requirements *(mandatory)*

### Functional Requirements

**Showing the values**

- **FR-001**: Every interactive question whose acceptable answers form a closed, knowable set MUST
  name that set in the prompt, alongside what pressing Enter does. The computer question counts as
  one of these: its models are a table like any other, and it MUST name them.
- **FR-002**: The values a prompt names MUST be exactly the distinct values that prompt accepts:
  each named once, in the displayed spelling, with no value the question would refuse and no
  acceptable value omitted. Alternate spellings of a named value, letter case, and the free part of
  a compound answer—the percent in "crystaliron 10", a turret count, a stateroom count—lie outside
  this count and are governed by FR-015 and FR-006. A question that accepts the literal `none`, or
  a count of zero spelled `none`, MUST say so.
- **FR-003**: The values a prompt names MUST be derived from the same rules data and the same
  checks that decide whether an answer is accepted, so that a change to the tables changes the
  prompt without a second edit.
- **FR-004**: A prompt MUST continue to state what Enter does, and MUST continue to state it
  truthfully for the questions where Enter does something other than roll (purpose, and a screen
  on a small craft, both of which pin absence).
- **FR-005**: A prompt naming three or more values in an evenly spaced numeric run MUST render
  that run as a range rather than enumerate it, so the question stays readable.
- **FR-006**: Questions whose answers are open—stateroom count, name, purpose—MUST NOT name a set
  of values. They MUST still name the `none` they accept, unless Enter's advertised default is
  already `none`: the stateroom and name questions name it, because there `none` pins something
  Enter does not and nothing else in the prompt reveals it; the purpose question does not, because
  its Enter label already says `none`.
- **FR-007**: The question asking which answers to revise MUST name every answer that can be
  revised, and is the one prompt exempt from the length budget of SC-005: it wraps onto as many
  lines as the full list takes rather than shortening or omitting it.
- **FR-008**: All prompts MUST continue to be written to stderr only, so that `--interactive`
  composes with `--toml` and `--out` and stdout remains a design a pipe can read.

**Narrowing to the ship in hand**

- **FR-009**: A question whose acceptable set depends on the hull class MUST name only the values
  that ruleset accepts.
- **FR-010**: A question whose acceptable set depends on a hull tonnage the referee has pinned
  MUST name the set narrowed to that tonnage—the manoeuvre ratings the hull can carry beside a
  plant and a cockpit, the plant ratings available beside a pinned drive, the turret counts within
  the hull's hardpoints, and the weapons a small craft's plant can run.
- **FR-011**: When the hull tonnage was left to generation, a hull-dependent question MUST name
  the set for the whole ruleset and MUST make clear the set is not narrowed to a chosen hull.
- **FR-012**: When a narrowed set is empty, the question MUST say the hull can take none of the
  values instead of displaying an empty choice.
- **FR-013**: The power-plant question MUST continue to state the floor its pinned drives require,
  in addition to naming the available ratings.

**Spelling**

- **FR-014**: Values MUST be displayed as words separated by spaces rather than as the underscored
  keys of the design format. The displayed spelling MUST be derived from the stored key by
  replacing each underscore with a space, so that a value added to a rules table displays
  correctly without a second edit. Where the SRD hyphenates a term the prompt shows it with a
  space—"pop up", "self sealing"—and the hyphenated spelling remains an accepted answer.
- **FR-015**: Every displayed value MUST be accepted verbatim when typed back; the stored
  underscored spelling MUST continue to be accepted, so answers copied from a design file work;
  and a hyphen MUST be accepted wherever the displayed spelling has a space, so that `pop_up`,
  "pop up" and "pop-up" are one answer. Answers MUST remain case-insensitive.
- **FR-016**: A refusal MUST name the acceptable values in the same spelling the prompt used, so
  that the prompt and the refusal do not appear to describe different sets.

**Armour options**

- **FR-017**: After an armour type is pinned, the session MUST ask which armour options to add and
  MUST name the available options.
- **FR-018**: The armour-options question MUST accept any number of the named options in one
  answer, including none, and MUST refuse a repeated option and an unrecognised one with the
  reason.
- **FR-019**: The armour-options question MUST NOT be asked when armour was pinned absent or left
  to generation.
- **FR-020**: Armour options pinned at the wizard MUST reach the built ship and MUST round-trip
  through the emitted design format, as an armour layer authored by hand does.
- **FR-021**: Revising armour MUST re-ask its options under the same rules; revising any other
  answer MUST leave a pinned set of armour options untouched.

**Documentation**

- **FR-022**: The user-facing documentation of the interactive session MUST be updated to describe
  what a prompt now shows, and MUST no longer imply that a refusal is how a referee learns the
  acceptable values.

### Key Entities

- **Prompt**: One question in the session. Carries the question text, the set of values it accepts
  where that set is closed, and what pressing Enter does.
- **Acceptable value set**: The answers one question will take, drawn from the rules tables and
  narrowed by the answers already given. Each value has a spelling shown to the referee and a
  spelling stored in the design.
- **Armour options**: The once-only additions to an armour layer (reflec, self sealing, stealth),
  already part of an armour layer in the design format and newly reachable from the session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every interactive question with a closed set of answers names that set. Counted over
  a full starship session and a full small-craft session, the number of such questions that do not
  is zero.
- **SC-002**: For every value displayed at every prompt, typing it back verbatim is accepted; and
  for every distinct value a prompt accepts, the prompt named it. Both counts of exceptions are
  zero. Alternate spellings of a named value and the free part of a compound answer are not
  counted.
- **SC-003**: A referee can complete an interactive session pinning armour, configuration,
  electronics, a computer, a fitting, a turret and a screen without consulting the SRD, the README,
  or a refusal message to learn what to type.
- **SC-004**: All three armour options are reachable from the interactive session, where none is
  today.
- **SC-005**: No prompt occupies more than two lines in an 80-column terminal, save the question
  asking which answers to revise, which names all sixteen and takes the lines it needs.
- **SC-006**: Adding, renaming or removing a value in a rules table changes what the corresponding
  prompt offers with no edit to the prompt itself.
- **SC-007**: A session in which the referee presses Enter at every question produces the same ship
  from the same seed as generation without `--interactive`, unchanged from today.

## Assumptions

- The scope is the interactive session's prompts. The rules, the tables, generation and assembly
  are unchanged, except that a pinned set of armour options now reaches them from one more
  direction.
- Where a value is knowable but a *rules* refusal is only decidable at assembly, the prompt lists
  it and the refusal arrives at assembly as it does today. Assembly remains the sole authority on
  rules legality; no rule is duplicated outward into the prompts to shorten a list.
- Armour options are asked as a question of their own, following the type-and-percent question,
  taking any number of options in one answer. Quantity, vehicle tonnage, software, computer
  hardening and jump control remain out of the session's scope and stay reachable through
  hand-authored design files.
- The prompt format is the question, then the acceptable values and what Enter does. This changes
  the text of nearly every prompt, so the existing tests that assert exact prompt strings will be
  rewritten as part of the work; the change is to prompt text on stderr only and no design file,
  emitted TOML, or ship description changes.
- The small craft hangar is excluded from the fitting question's list because the question cannot
  supply the vehicle tonnage that fitting requires. This makes explicit a refusal that already
  happens; it removes no capability.
- The README's description of the interactive session is the user-facing documentation this
  feature updates.
