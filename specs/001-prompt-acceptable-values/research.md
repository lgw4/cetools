# Phase 0 Research: Acceptable Values at Interactive Ship Prompts

**Branch**: `001-prompt-acceptable-values` | **Date**: 2026-07-29

**Spec**: [spec.md](./spec.md)

All Technical Context unknowns are resolved here. Every decision below was checked against the
code in `src/cetools/`, not against memory.

---

## Decision 1: The engine publishes each question's value set; the CLI never reads a table

**Decision**: Add one accessor per closed-set question to `src/cetools/engine/ships/generator.py`
and export it from `src/cetools/engine/ships/__init__.py`. The CLI imports only from
`cetools.engine.ships`.

**Rationale**: Two constraints meet here.

- FR-003 requires the displayed set to come from the same rules data as the acceptance check, so
  that a table edit moves the prompt with no second edit (SC-006).
- Constitution II forbids game logic in `src/cetools/cli/` and requires callers to import from an
  engine package rather than reach into its modules. `src/cetools/engine/ships/tables.py` is *not*
  on the `cetools.engine.ships` public surface (verified: `__init__.py` exports no table).

An accessor satisfies both: it is one expression over the table that the paired validator already
reads, and it lives beside that validator.

**Alternatives considered**:

- *Export the tables (`FITTINGS`, `SCREENS`, …) from `cetools.engine.ships`.* Rejected. Two of the
  sets are not a table's keys: the fitting question excludes `vehicle_hangar`, and the small-craft
  weapon set is filtered by the power plant's energy allowance. Deciding those in the CLI puts
  game logic in `cli/`, which Constitution II forbids.
- *Have the CLI derive the set by feeding every table key through the validator in a
  `try`/`except`.* Rejected. It reads the table anyway (same import problem) and turns a data
  lookup into exception control flow.

**New engine surface** (11 functions; the accessor/validator pairing is the invariant that makes
FR-003 structural rather than a convention):

| Accessor | Returns | Reads | Paired validator |
|---|---|---|---|
| `hull_tonnages(hull_class)` | `tuple[int, ...]` | `HULLS` / `SMALL_CRAFT_HULLS` | `validate_hull_tons` |
| `armor_options()` | `tuple[str, ...]` | `ARMOR_OPTIONS` | `ArmorFit.__post_init__` |
| `computer_models()` | `tuple[int, ...]` | `COMPUTERS` | `ComputerFit.__post_init__` |
| `electronics_packages()` | `tuple[str, ...]` | `ELECTRONICS` | `validate_electronics` |
| `fitting_kinds()` | `tuple[str, ...]` | `FITTINGS` less vehicle-sized | `FittingFit.__post_init__` |
| `bay_kinds()` | `tuple[str, ...]` | `BAYS` | `BayFit.__post_init__` |
| `screen_kinds()` | `tuple[str, ...]` | `SCREENS` | `ScreenFit.__post_init__` |
| `turret_mounts()` | `tuple[str, ...]` | `TURRET_MOUNTS` | `validate_turret_mount` |
| `turret_weapons()` | `tuple[str, ...]` | `TURRET_WEAPONS` | `validate_turret_weapon` |
| `small_craft_weapons(hull_tons, power_rating, mount=None)` | `tuple[str, ...]` | `TURRET_WEAPONS` filtered by `_exceeds_energy_allowance` | `validate_small_craft_weapon` |
| `hardpoints(hull_class, hull_tons)` | `int` | none (exposes `_hardpoints_for`) | `validate_turret_count` |

No accessor is added for armour type, configuration or hull class: `ArmorType`, `Configuration`
and `HullClass` are already exported, and `[member.value for member in Enum]` is the set. Four
narrowing functions already exist and are reused unchanged: `available_ratings`,
`small_craft_maneuver_ratings`, `small_craft_power_ratings`, `power_floor`.

---

## Decision 2: A `cli/prompts.py` module holds the text composition

**Decision**: Add `src/cetools/cli/prompts.py` with four pure functions and mirror it with
`tests/test_prompts.py`. It imports nothing from the engine.

**Rationale**: Three of the four are non-trivial and independently testable: the underscore-to-space
spelling (FR-014), its inverse for input (FR-015), and the evenly-spaced-run collapsing (FR-005).
Testing run collapsing through a CLI session would need a hull tonnage table with the right shape;
testing it directly needs a list of integers. `src/cetools/cli/ship.py` is already 721 lines and
this feature touches nearly every reader in it.

Presentation, not rules, so `cli/` is the right side of the seam: Constitution II describes the CLI
as "parse arguments, call the engine, format output".

**Alternatives considered**:

- *Keep it all in `ship.py`.* Rejected on testability, not size: run collapsing deserves a unit
  test with a list of integers rather than a scripted session.
- *Put it in the engine.* Rejected. Nothing here consults a rule, and a library caller passes
  stored keys, so an engine that spells values for a terminal would be spelling them for nobody.

**Surface**:

- `spell(key: str | int) -> str`—`"bonded_superdense"` → `"bonded superdense"` (FR-014).
- `key(answer: str) -> str`—lowercase, and space or hyphen to underscore (FR-015).
- `numbers(values: Sequence[int]) -> list[str]`—collapse each evenly spaced run into
  `"first-last"`, or `"first-last by step"` when the step is not 1. A run of three or more always
  collapses; a run of exactly two collapses only when its step is 1, so a 200-ton hull's hardpoints
  give `1-2` while a two-element gapped run stays `1, 3` rather than becoming the longer `1-3 by 2`
  (FR-005, clarified in the checklist review).
- `offer(question: str, values: Iterable[str], *, note: str = "") -> str`—compose
  `"{question} ({values}{note})"`, returning `question` unchanged when `values` is empty and no
  note is given.

---

## Decision 3: The CLI owns the refusal message for closed-set questions

**Decision**: Each closed-set reader checks membership against the accessor's set and raises its
own `ValueError` naming the values in the displayed spelling; the accepted key is then handed to
the engine record or validator as it is today.

**Rationale**: FR-016 requires the refusal to name values in the spelling the prompt used. The
engine's own messages (`_validate_key`: `f"unknown {what} {name!r}; known: {sorted(table)}"`) are
shared with library callers, who must pass the *stored* key—respelling those with spaces would
name spellings a library caller cannot use. So the respelling belongs where the spaced spelling
was shown.

The engine remains the authority: the CLI's check is a pre-filter over the engine's own published
set, and Decision 5's contract test is what keeps the two from drifting. This is input-domain
validation against an engine-published set, not a rule, so it does not breach Constitution II.

**Alternatives considered**:

- *Change the engine's messages to spaced spelling.* Rejected: it degrades the library-facing
  message and rewrites engine tests for a prompt's benefit.
- *Have `_ask_until_understood` rewrite the engine's message.* Rejected: it would have to
  pattern-match arbitrary prose.

---

## Decision 4: The revise prompt spaces its names, and `_read_fields` is rewritten

**Decision**: The "Revise which answers" prompt names the sixteen `DesignConstraints` fields in
spaced spelling (`hull class`, `jump rating`, …). `_read_fields` is rewritten to match multi-word
names by greedy scan, and must still accept today's `hull_class hull_tons`.

**Rationale**: Confirmed with the user 2026-07-29. FR-014 is read uniformly rather than scoped to
rules-table values, so FR-002 and FR-015 then require the parser to accept what the prompt shows.
Today's `answer.replace(",", " ").split()` would see `"hull class"` as two unknown tokens.

A greedy longest-match scan over whitespace-and-comma-separated words is unambiguous here: the
five two-word names are `hull class`, `hull tons`, `jump rating`, `maneuver rating`,
`power rating`, and none of their first words (`hull`, `jump`, `maneuver`, `power`) is itself a
field name. The span limit is derived from the names (`max(name.count("_") + 1 ...)`), so a
three-word field would need no edit.

This accepts all four forms a referee may reach for: `hull class, hull tons` (as displayed),
`hull class hull tons`, `hull_class hull_tons` (today's, and what a design file suggests), and any
case.

**Alternative considered**: *Keep the names underscored, change no parser.* Rejected by the user.
It was defensible—FR-014's own rationale speaks of "the underscored keys of the design format"
and "a value added to a rules table", and a field name is neither—but the uniform reading was
chosen.

**Length**: this prompt is 199 characters, three lines at 80 columns. FR-007 exempts it from
SC-005; every other prompt was measured against the budget (Decision 6).

---

## Decision 5: `displayed == accepted` is enforced by a table-driven contract test

**Decision**: One parametrised test walks every closed-set question, and for each asserts that
every displayed value is accepted when typed back verbatim, that its stored spelling and its
hyphenated spelling are accepted, and that the displayed set equals the accessor's set.

**Rationale**: SC-002 states two counts of exceptions that must both be zero. Written per question
by hand, a question added later escapes the check silently—the same failure mode
`scripts/check_docs.py` exists to prevent for docs. Driven from one table of
`(question, accessor, reader)` triples, adding a question means adding a row or failing the test.

The `parse`/`spell` round-trip (`key(spell(k)) == k` for every published value) is the property
that makes FR-014 and FR-015 one fact instead of two, and it is cheap to assert exhaustively over
all 39 published word values.

---

## Decision 6: The prompt format is `question (values) [default]:`, and it fits

**Decision**: Values go in parentheses between the question and the existing `[default]`. Measured
against every table in the repository, every prompt fits SC-005's two lines at 80 columns; only the
revise prompt (FR-007, exempt) exceeds it.

**Rationale**: SC-005 is a hard budget, so the format was measured before being chosen rather
than after. Measured lengths, longest first:

Re-measured after the checklist review, which found this table predated the armour prompt's final
wording (the shape note FR-002 now requires) and the `none`-last ordering. Every prompt is the exact
string the session writes, trailing space included (SC-005's measurement basis).

| Prompt | Chars | Lines |
|---|---|---|
| `Revise which answers (hull class, …, purpose) [all]: ` | 199 | 3 (exempt) |
| `Fitting (armory, detention cell, fuel scoops, fuel processor, laboratory, library, luxuries, vault, none) [roll]: ` | 114 | 2 |
| `Electronics (standard, basic civilian, basic military, advanced, very advanced, none) [roll]: ` | 94 | 2 |
| `Armor (titanium steel, crystaliron, bonded superdense, each with a percent, or none) [roll]: ` | 93 | 2 |
| `Turret 1 weapon (missile rack, pulse laser, sandcaster, particle beam) [roll]: ` | 79 | 1 |
| `Hull tonnage (100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000) [roll]: ` | 76 | 1 |
| `Power plant rating (a 10-ton hull can carry none, at least 4) [roll]: ` | 70 | 1 |
| `Weapon bay (missile bank, particle, meson, fusion, none) [roll]: ` | 65 | 1 |
| `Turret 1 mount (single, double, triple, pop up, fixed) [roll]: ` | 63 | 1 |
| `Configuration (distributed, standard, streamlined) [roll]: ` | 59 | 1 |
| `Armor options (reflec, self sealing, stealth) [none]: ` | 54 | 1 |
| `Screen (meson screen, nuclear damper, none) [roll]: ` | 52 | 1 |
| `Maneuver rating (1-6 on some starship hull) [roll]: ` | 52 | 1 |
| `Hull class (starship, small craft) [starship]: ` | 47 | 1 |
| `Power plant rating (3-5, at least 3) [roll]: ` | 45 | 1 |
| `Staterooms (a count, or none) [roll]: ` | 38 | 1 |
| `Computer model (1-7, none) [roll]: ` | 35 | 1 |
| `Hull tonnage (10-95 by 5) [roll]: ` | 34 | 1 |
| `Name (any text, or none) [roll]: ` | 33 | 1 |
| `Turrets (1-50, none) [roll]: ` | 29 | 1 |
| `Purpose [none]: ` | 16 | 1 |

The longest prompt inside the budget is the fitting question at 114 characters, so the budget holds
with 46 characters of headroom on two lines. Run collapsing is what keeps hull tonnage (18 values)
and turret counts (up to 50) inside it: without it, hull tonnage alone is 180 characters.

**Rating prompts** need a phrase rather than only a list, because the same list means two different
things (FR-010 vs FR-011). Narrowed: `Maneuver rating (1-6) [roll]: `. Not narrowed, the qualifier
naming the ruleset rather than a hull: `Maneuver rating (1-6 on some starship hull) [roll]: `. The
power plant keeps its floor inside the same parentheses rather than gaining a second group, in all
three narrowing states (FR-013).

**Alternative considered**: *Values on a second line of their own.* Rejected: it doubles every
prompt's height for no gain, since the one-parenthesis form already fits.

---

## Decision 7: Armour options live inside the `armor` field; `DesignConstraints` is unchanged

**Decision**: `_read_armor` keeps returning an `ArmorFit`; the options question follows it and
rebuilds that fit as `ArmorFit(type=…, percent=…, options=…)`. No field is added to
`DesignConstraints`.

**Rationale**: FR-021 comes free. Revising `armor` re-asks the pair because they are one field;
revising anything else leaves the options untouched because `answered("armor", …)` carries the
whole fit. A separate `armor_options` field would need explicit coupling in both directions, and
would make `_REVISABLE` seventeen names where the spec says sixteen (confirmed:
`fields(DesignConstraints)` is 16).

Everything downstream already works, verified rather than assumed:

- `ArmorFit.options` exists with a default of `()`, and `_validate_armor_fit` already refuses an
  unknown option and a repeated one—so FR-018's two refusals need no new code, only the
  reasons already raised.
- `_select_armor` passes a pinned fit through `_pin_or_draw` whole, so options reach `build_ship`.
- `builder.py` charges `ARMOR_OPTIONS[option].cost_per_ton` and `description.py` names them.
- `design.py` reads `options` on load (line 174) and writes it on dump (line 417).

So FR-020 (reach the ship, round-trip through TOML) is already satisfied by the format and needs
a test rather than an implementation.

**Alternatives considered**:

- *A separate `armor_options` field on `DesignConstraints`.* Rejected as above.
- *Extend `_read_armor` to take options in the same answer (`crystaliron 10 reflec`).* Rejected:
  the spec's Assumptions section fixes the options as a question of their own.

---

## Decision 8: `none` is named inside the value list, not as separate prose

**Decision**: For a closed-set question that accepts `none`, `none` is the last value in the list—
`Turrets (1-2, none)`, not `(none, 1-2)`. FR-002 now states this ordering as a requirement.
The two open questions that must name it (staterooms, name) name it in a short note instead, since
they have no list; `purpose` names nothing, because its `[none]` default already says it (FR-006).

**Rationale**: FR-002 requires a question accepting the literal `none` to say so, and the list is
where the referee is already reading. It also keeps the screen question honest on a small craft,
where the default is `[none]` and the list still names the two screens plus `none`.

Which questions accept `none` was read off the code rather than assumed: `_read_armor`,
`_read_computer`, `_read_electronics`, `_read_fitting`, `_read_bay`, `_read_screen`,
`_read_name` (pins an unnamed ship), `_read_purpose`, and the two counts `_read_staterooms` and
`_read_turret_count` (where it means a deliberate zero). Hull class, configuration, the three
ratings, and the turret mount and weapon questions do not.

---

## Decision 9: FR-012's empty narrowed set is reachable on exactly one path

**Finding**: Enumerating every tabulated hull, no manoeuvre-rating set and no turret-count set is
ever empty (`small_craft_maneuver_ratings` is non-empty for all 18 small-craft tonnages;
`HULLS` starts at 100 tons, so a starship always has at least one hardpoint, and a small craft
always has exactly one).

The power-plant set *can* be empty—there are 58 `(tonnage, rating)` pairs where
`small_craft_power_ratings` returns `()`—but only for a manoeuvre rating the manoeuvre question
would itself have refused. The one reachable route is the revise loop: press Enter at hull tonnage,
pin a manoeuvre rating checked only against the whole ruleset, then revise `hull tons` (which does
not re-ask `maneuver rating`) to a tonnage that cannot carry it, and revise `power rating`.

**Decision**: Implement FR-012's guard generically in the prompt composition—an empty set yields
the "can take none of them" phrasing for any question—and test it through that one reachable
session rather than only at unit level. Stating it here so the test is not mistaken for dead code.

---

## Decision 10: Existing prompt-text tests are rewritten, not extended

**Finding**: `tests/test_cli.py` asserts exact prompt strings in 29 places (e.g.
`assert "Armor [roll]:" in result.stderr`, and a `("configuration", "Configuration [roll]:", …)`
parametrisation table at line 1033). Every one of them changes.

**Decision**: Rewrite them to the new text, as the spec's Assumptions anticipate. Under
Constitution III each rewritten assertion must be seen to fail against the current implementation
before the implementation moves—a test rewritten to the new string and passing immediately would
mean the prompt never changed.

**Scope check**: stdout is untouched. No design file, emitted TOML, or ship description changes,
so `tests/test_ship_design.py`, `tests/test_ship_builder.py` and `tests/test_ship_description.py`
need no edits beyond the new armour-options round-trip test (FR-020).
