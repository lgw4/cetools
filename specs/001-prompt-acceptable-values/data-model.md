# Phase 1 Data Model: Acceptable Values at Interactive Ship Prompts

**Branch**: `001-prompt-acceptable-values` | **Date**: 2026-07-29

**Spec**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

This feature adds no persisted data and no new record to the design format. What it adds is one
new *derived* value—a question's acceptable set—and one presentation rule for spelling it. The
entities the spec names map onto existing code as follows.

---

## Entity: Acceptable value set

**What it is**: The answers one question will take, drawn from a rules table and narrowed by the
answers already given.

**Representation**: A plain `tuple[str, ...]` or `tuple[int, ...]` returned by an engine accessor.
No record is introduced: the set has no behaviour of its own, and a tuple is what every existing
narrowing function (`available_ratings`, `small_craft_maneuver_ratings`) already returns.

**Where it lives**: `src/cetools/engine/ships/generator.py`, exported from
`cetools.engine.ships`. See [research.md Decision 1](./research.md) for the eleven accessors and
the validator each pairs with.

**Invariant (FR-002, FR-003, SC-002)**: for every closed-set question,

```text
set(accessor(...)) == { every value the question's reader accepts }
```

Enforced by the contract test in [contracts/prompt-contract.md](./contracts/prompt-contract.md),
not by a runtime assertion.

**Narrowing inputs**: which answers already given narrow a set.

| Set | Narrowed by | Requirement |
|---|---|---|
| Hull tonnage | hull class | FR-009 |
| Jump / manoeuvre / power rating | hull class, hull tonnage | FR-010, FR-011 |
| Power plant rating | plus the pinned manoeuvre rating (small craft) | FR-010 |
| Turret count | hull class, hull tonnage (hardpoints)—or, with no tonnage pinned, the ruleset's largest hardpoint count | FR-010, FR-011 |
| Small-craft turret weapon | hull tonnage, power rating, mount | FR-010 |

**States**: a narrowed set is *narrowed* (a hull tonnage is pinned), *unnarrowed* (tonnage left to
the dice—FR-011 requires the prompt to say so with a qualifier naming the ruleset), or *empty*
(FR-012 requires the prompt to name no value, say which hull can take none of them, and accept only
Enter, refusing any typed answer with that reason; see
[research.md Decision 9](./research.md) for reachability).

**When it is computed**: at the moment its question is asked, from the answers standing then—not once
per session. This is what makes a question re-asked in the revise loop name the set its *new* tonnage
allows, and each turret's weapon set narrow by that turret's own mount (FR-010).

---

## Entity: Value spelling

**What it is**: Each value has a spelling shown to the referee and a spelling stored in the design.

**Representation**: Two pure functions in `src/cetools/cli/prompts.py`, not a record. The stored
key is the single source; the displayed spelling is derived from it.

| Direction | Function | Rule | Requirement |
|---|---|---|---|
| stored → displayed | `spell(key)` | each `_` becomes a space | FR-014 |
| typed → stored | `key(answer)` | lowercase; each space or `-` becomes `_` | FR-015 |
| typed → several stored | `split_values(answer, known)` | greedy longest-match over words separated by whitespace or commas | FR-015, FR-018 |

**Invariant**: `key(spell(k)) == k` for every published **word** value. This is what makes "displayed
verbatim is accepted" (SC-002) a property rather than a list of cases. Asserted exhaustively over
all 39 of them—the 31 table keys the accessors publish plus the 8 members of `ArmorType`,
`Configuration` and `HullClass`. The numeric sets are outside it: `key(spell(100))` is the string
`"100"`, not the integer, and a numeric answer is read with `int()` rather than spelled.

**A value may contain a space, so a multi-value answer cannot be split before it is matched.**
`self sealing` at the armour-options question and `hull class` at the revise question are one value
each; matching word by word would turn them into unknown tokens and make the prompt refuse a
spelling it displayed. `split_values` is the one place that is decided
([research.md Decision 2](./research.md)).

**Accepted input forms** for a value displayed as `pop up`: `pop up`, `pop_up`, `pop-up`, and any
case of each. `spell` is total over the published keys, so a value added to a rules table displays
and parses correctly with no second edit (SC-006).

**Note on the two hyphenated SRD terms**: `pop_up` and `self_sealing` are spelled with a space at
the prompt, per the spec's clarification, and the hyphen remains an accepted input. The SRD's own
hyphenated spelling survives untouched in `TURRET_MOUNTS["pop_up"].name` (`"pop-up turret"`) and
`ARMOR_OPTIONS["self_sealing"].name` (`"a self-sealing hull"`), which the *description* renderer
uses. Those display names are not what a prompt shows and are not changed by this feature.

---

## Entity: Prompt

**What it is**: One question in the session—its text, its acceptable set where the set is closed,
and what pressing Enter does.

**Representation**: No record. A prompt is composed at the call site by
`prompts.offer(question, values, note=...)` and handed to the existing
`_ask_until_understood(question, interpret, default_label)`. The default label is already a
parameter there; the values are new.

**Rationale for adding no record**: a `Prompt` dataclass would carry no behaviour the two existing
functions do not already provide, and Constitution V forbids an abstraction the task does not
require. The full per-question table is the contract, not a type.

**Composed form**: `{question} ({values}{note}) [{default}]: `, written to stderr only (FR-008,
already true of `_ask`). Measured against SC-005 in
[research.md Decision 6](./research.md).

---

## Entity: Armour options

**What it is**: The once-only additions to an armour layer—reflec, self sealing, stealth.

**Representation**: `ArmorFit.options: tuple[str, ...]`, which **already exists** at
`src/cetools/engine/ships/models.py:104`. No model change.

**Already in place, verified** (see [research.md Decision 7](./research.md)):

- `_validate_armor_fit` refuses an unknown option and a repeated one (models.py:91-95)—FR-018.
- `_select_armor` passes a pinned fit through whole—FR-020.
- `builder.py:104` charges `cost_per_ton`; `description.py:408` names the options.
- `design.py:174` loads `options`; `design.py:417` dumps it—FR-020's round trip.

**What changes**: `src/cetools/cli/ship.py` gains a reader for the options answer and asks it after
an armour type is pinned. `DesignConstraints` is unchanged, so `_REVISABLE` stays at sixteen names.

**Validation rules** (all pre-existing, surfaced at the prompt for the first time):

| Rule | Where | Requirement |
|---|---|---|
| Each option must be a key of `ARMOR_OPTIONS` | `_validate_armor_fit` | FR-018 |
| No option may repeat | `_validate_armor_fit` | FR-018, AS 4.6 |
| Any number of options, including none | `tuple` default `()` | FR-018, AS 4.3 |

**State transitions**: the options question is asked only when the armour question produced an
`ArmorFit`. Answering `none` at armour yields `ABSENT` and pressing Enter yields `None`; in both
cases the options question is skipped (FR-019, AS 4.4 and 4.5). Revising `armor` re-asks the pair
(FR-021, AS 4.7).

---

## Entity: Revisable answer

**What it is**: One of the sixteen `DesignConstraints` field names the revise question accepts.

**Representation**: `_REVISABLE`, already `tuple(field.name for field in fields(DesignConstraints))`
in `src/cetools/cli/ship.py`. Unchanged.

**What changes**: the *display* is now spaced (`hull class`) and `_read_fields` matches multi-word
names by greedy scan while still accepting the underscored form. See
[research.md Decision 4](./research.md).

**Invariant**: derived from `fields(DesignConstraints)`, so a field added to the record appears at
the prompt with no edit (SC-006). The greedy scan's span limit is derived the same way.
