# Research: Universal Character Format Output

## UCF field order and template (SRD-Fidelity)

**Decision**: Adopt the exact field order from the cited SRD page
(`character-creation.html#universal-character-format`), confirmed by fetching the page:

```
[Character Name, with rank and/or noble title, if appropriate]    [UPP]    Age [Age]
[Careers, with terms in parentheses]    Cr[Funds]
[Skill List, alphabetical, with levels]
[Species Traits, if not human; optional]
[Equipment, if available; significant property only]
```

Concrete SRD example:

```
Bruce Ayala	786A9A	Age 38
Entertainer (5 terms)	Cr70,000
Athletics-1, Admin-1, Advocate-1, Bribery-1, Carousing-3, Computer-2,
Gambling-0, Grav Vehicle-0, Liaison-2, Linguistics-0, Streetwise-0
High passage (x2)
```

**Rationale**: This is the sole authoritative source per Constitution Principle I. The spec's
FR-002 through FR-008 already mirror this structure field-for-field (rank+name/UPP/age,
career+terms+funds, skills, equipment), confirming the spec's line set is a faithful subset (the
species-traits line is always skipped per FR-008/Assumptions, since only human characters are
generated).

**Alternatives considered**: None — the format is externally specified and non-negotiable per
Constitution Principle I.

## Field delimiter within a line

**Decision**: Separate the three segments of line 1 (name-with-rank, UPP, age) and the two
segments of line 2 (career-with-terms, funds) with a single tab character (`\t`), matching the
SRD's own template rendering (tab-separated so the format pastes cleanly into a spreadsheet or
VTT import field, which is the whole point of a "universal" format per SC-003). Within a segment
(e.g. "Colonel Jane Ruiz", "Cr70,000"), use single spaces as normal prose.

**Rationale**: This is the most common community interpretation of UCF — the format exists so
character summaries can be pasted as tab-delimited data. No functional requirement in the spec
contradicts this, and it costs nothing over space-delimiting.

**Alternatives considered**: Space-delimiting every segment. Rejected because it degrades the
"paste into a spreadsheet/VTT" use case that motivates the format's existence (SC-003), and the
SRD's own template uses tabs.

## No blank lines between UCF lines

**Decision**: The 3–4 output lines are emitted back-to-back with no blank line separators (unlike
the current `format_character`, which inserts blank lines between sections).

**Rationale**: Neither the SRD template nor its concrete example contains blank lines between
fields; UCF is described as a "5-line format" (4 visible for a human character), which only holds
if there are no interstitial blank lines.

**Alternatives considered**: Keep a blank line between sections for readability. Rejected — it
would no longer be "exactly the UCF line set" as required by FR-002/SC-001, and breaks
copy-paste fidelity (SC-003).

## Random name selection mechanism

**Decision**: Add `src/cetools/engine/names.py` holding two data tuples, `FIRST_NAMES` and
`LAST_NAMES`, following the same data-driven convention as career/skill tables
(Constitution Principle V). A `generate_name(roller: DiceRoller) -> str` function selects one
entry from each list independently via `roller.roll(len(LIST))`, which the existing `DiceRoller`
protocol already supports for any `sides` value (not just 6) — `RandomDiceRoller.roll(sides)` is
`sum(random.randint(1, sides) for _ in range(count))`, i.e. a uniform pick in `[1, sides]` for
`count=1`. This keeps name generation fully deterministic under test via the existing
`ConstantRoller`/`SequenceRoller`/`SmartRoller` test doubles, with no new test infrastructure.

**Rationale**: Reuses the existing randomness-injection seam instead of introducing a second one
(e.g. a raw `random.choice` call), keeping `generate_character` fully testable and consistent with
Principle II (all game logic, including name assignment, lives in the engine and is
roller-driven).

**Alternatives considered**:
- `random.choice(LIST)` directly in `names.py` — rejected: bypasses the `DiceRoller` seam,
  making name assignment non-deterministic in tests and inconsistent with every other random
  draw in the engine.
- Pre-paired full-name list — rejected per spec clarification (two independent lists, drawn and
  combined).

## Where name generation happens in the generation pipeline

**Decision**: Generate the name once, near the end of `generate_character`, alongside the other
values passed into the final `Character(...)` construction (i.e., after mustering-out, right
before return). No name is generated on a `GenerationFailure` path (enlistment/survival failure).

**Rationale**: A `GenerationFailure` never reaches `format_character`, so a name would be wasted
work; placing the roll after all pass/fail branches also means it cannot perturb the roll sequence
consumed by earlier checks in any test using `SequenceRoller`/`ConstantRoller`/`SmartRoller` (all
existing failure-path tests return before that point).

**Alternatives considered**: Generate the name first (mirroring "characters have names before
they enlist"). Rejected — it would insert two extra roller calls ahead of every existing
qualification/survival/skill roll in the sequence, breaking every `SequenceRoller`-based test that
depends on exact call order, for no behavioral benefit (FR-010 forbids changing existing
mechanics).

## Impact on existing mechanics (FR-010)

**Decision**: No changes to `_check`, `_roll_skill`, `_muster_out`, `_apply_aging`,
`_pension`, or any career/rank/skill/benefit table. The only new engine behavior is the one
`generate_name` call described above; the only display behavior change is a full rewrite of
`format_character`.

**Rationale**: Directly satisfies FR-010 and SC-004 (zero regressions outside display/name).

**Alternatives considered**: None — this is a hard constraint from the spec, not a design choice.
