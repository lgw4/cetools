# Contract: Universal Ship Description Format output

**Feature**: 011-universal-ship-format

The exact text `render_description(ship)` produces. Every template is quoted from the SRD's
Universal Ship Description Format section or from a Chapter 9 worked example; sources and the
decisions taken where they disagree are in [research.md](../research.md).

Notation: `{x}` is a substituted value; `{a|b}` is a form chosen by number agreement (FR-023);
`[…]` marks a clause that is dropped when it does not apply (FR-021). The helper names
(`count`, `tons`, `number`, `money`, `signed`, `join`, `article`, `tonnage_article`) are the
`prose.py` functions defined in [data-model.md §5](../data-model.md).

---

## Overall shape (FR-001)

```text
TL{tech_level} {name}
<blank line>
{sentence 1} {sentence 2} … {sentence n}
```

One heading line, one blank line, one paragraph. Sentences are separated by a single space and
never by a newline; the paragraph is not wrapped. No trailing newline — the CLI's `typer.echo`
supplies the one the terminal needs, exactly as the outgoing sheet worked.

- `{tech_level}` — `ship.tech_level`, always digits (FR-022a).
- `{name}` — `design.name`, or `"Unnamed Ship"` when the design has none (FR-029b). The same
  string appears in sentence 1.

Sentences appear in the FR-004 order below and in no other. A sentence marked *omittable*
disappears entirely when its condition holds; the rest of the paragraph is unchanged and stays
grammatical (FR-021).

---

## 1. Hull and purpose (FR-005) — never omitted

```text
Using {tonnage_article} {hull_tons}-ton hull ({hull_points} Hull, {structure_points} Structure), the {name} is {purpose}.
```

- `{hull_tons}`, `{hull_points}`, `{structure_points}` — digits always (FR-022a).
- `{tonnage_article}` — `"an"` when the tonnage's leading digit is 8, else `"a"`
  ("Using an 800-ton hull").
- `{purpose}` — `design.purpose` verbatim when supplied, otherwise the hull class:
  `"a starship"` or `"a small craft"` (FR-029a). Author prose carries no trailing period; the
  renderer supplies the sentence's.

## 2. Drives and performance (FR-006, FR-026) — never omitted

```text
It mounts {join(drive clauses)}[, giving a performance of {join(performance clauses)}].
```

Drive clauses, in this order, each present only when the drive is fitted:

| Clause | Condition |
|---|---|
| `jump drive {design.jump_code}` | starship (a small craft can never carry one) |
| `maneuver drive {design.maneuver_code}` | `maneuver_code is not None` |
| `power plant {design.power_code}` | always (the builder requires a power plant) |

Performance clauses, in this order:

| Clause | Condition |
|---|---|
| `Jump-{ship.jump_rating}` | starship |
| `{ship.maneuver_rating}-G acceleration` | `maneuver_code is not None` |

Both ratings are digits (FR-022a). The performance part is dropped whole when neither clause
applies (a power-plant-only hull). For a small craft this yields the SRD's non-jump form:
"It mounts maneuver drive sB and power plant sG, giving a performance of 1-G acceleration."

## 3. Fuel and endurance (FR-007, FR-026) — never omitted

Starship:

```text
Fuel tankage of {tons(f)} {ton|tons} supports the power plant for {count(w)} {week|weeks} and {count(j)} Jump-{r} {jump|jumps}.
```

Small craft:

```text
Fuel tankage of {tons(f)} {ton|tons} supports the power plant for {count(w)} {week|weeks}.
```

- `f` = `ship.jump_fuel + ship.power_fuel`.
- `w` = `design.power_weeks`.
- `j` = `ship.assumed_jump_distance // ship.jump_rating` — the jumps the tankage supports at
  the rated distance. Rendered `"zero"` when the design buys no jump fuel; the clause is kept
  (FR-007).
- `r` = `ship.jump_rating`, digits.

## 4. Computer (FR-008, FR-027) — omitted when no computer is fitted

```text
Adjacent to the {bridge|cockpit} is a computer Model {model}{suffix}.
```

- `bridge` for a starship, `cockpit` for a small craft (FR-027).
- `{model}` — `design.computer.model`, digits.
- `{suffix}` — `""`, `"/bis"` (jump control), `"/fib"` (hardened), or `"/bis/fib"` (both).

## 5. Sensors (FR-009, FR-030a) — never omitted

```text
The ship is equipped with {ElectronicsRow.name} sensors (DM{signed(dm)}).
```

The package is `design.electronics`, or `"standard"` when the design names none — every ship
carries the Standard suite included in its bridge or cockpit. `signed` always prints a sign,
including `DM+0` for Basic Military.

## 6. Quarters (FR-010) — omitted when all three counts are zero

```text
There {is|are} {join(clauses)}.
```

Clauses, in this order, each present only when its count is non-zero:

- `{count(n)} {stateroom|staterooms}`
- `{count(n)} low {berth|berths}`
- `{count(n)} emergency low {berth|berths}`

`is` only when there is exactly one clause and its count is one; `are` otherwise.

## 7. Hardpoints and fire control (FR-011) — never omitted

```text
The ship has {count(h)} {hardpoint|hardpoints} and {tons(h)} {ton|tons} allocated to fire control[, but has no weapons installed].
```

`h` = `ship.hardpoints`. Fire-control tonnage is reported as the hardpoint count, which is what
every Chapter 9 example prints (research.md Part F); no computed value changes. The trailing
clause appears when `ship.hardpoints_used == 0`.

## 8. Installed weapons and ammunition (FR-012) — omitted when no turrets and no bays

```text
Installed on the {hardpoint|hardpoints} {is|are} {join(groups)}.
```

`hardpoint` / `is` when exactly one weapon system is installed.

Groups, bays first then turrets (research.md Part B), each in first-appearance order over the
design:

| Kind | Phrase |
|---|---|
| Bay, grouped by `kind` | `{count(n)} {BayRow.name\|plural}` — "one particle beam bay", "four missile bays" |
| Turret, grouped by `(mount, weapons)` | `{count(n)} {MountRow.name\|plural} armed with {join(weapon phrases)}` |

A turret's weapon phrases group its slots by weapon in slot order: a weapon filling one slot
renders `{article} {WeaponRow.name}` ("a pulse laser"); filling more than one it renders
`{WeaponRow.plural}` ("missiles"), with no count — matching "two triple turrets armed with
missiles".

Ammunition follows as its own sentence per `(kind, type)` group, aggregated across every
turret, in first-appearance order:

```text
{count(n)} {AmmoRow.name|plural} {is|are} carried as ammunition for the {WeaponRow.name} {turret|turrets}.
```

The weapon is `TURRET_WEAPONS[AmmoRow.weapon]`; the turret plural agrees with how many turrets
carry that weapon. "120 smart missiles are carried as ammunition for the missile turrets."

## 9. Screens (FR-013) — omitted when no screens are fitted

```text
This ship has {count(n)} {screen|screens}: {join(groups)}.
```

Groups by `kind` in first-appearance order: `{article} {ScreenRow.name}` at count one
("a meson screen"), `{count(n)} {ScreenRow.plural}` above.

## 10. Small craft hangars (FR-014) — omitted when no vehicle-sized fitting is installed

A hangar is any fitting whose row sets `tons_per_vehicle_ton` — never a key comparison
(FR-031). With one such fitting:

```text
There {is|are} {count(total)} small craft {hangar|hangars}[, each] holding {tons(v)} {ton|tons} of small craft.
```

`each` is dropped when `total == 1`. With more than one fitting entry:

```text
There are {count(total)} small craft hangars, {join(entry clauses)}.
```

Entry clause: `{count(quantity)} holding {tons(v)} {ton|tons} of small craft`. The noun comes
from the fitting row's `name` / `plural` ("small craft hangar" / "small craft hangars"), not
from the renderer.

## 11. Cargo (FR-015) — never omitted

```text
Cargo capacity is {tons(c)} {ton|tons}.
```

`c` = `ship.cargo_tons`. Zero renders "Cargo capacity is zero tons."; a fractional capacity
renders in digits, "Cargo capacity is 6.2 tons."

## 12. Hull configuration and armour (FR-016, FR-016a) — never omitted

No armour fitted:

```text
The hull is {ConfigurationRow.name}, and no additional armor has been installed.
```

Armour fitted, no options:

```text
The hull is {ConfigurationRow.name}, and is armored with {join(types)} ({p} points).
```

Armour fitted with options:

```text
The hull is {ConfigurationRow.name}, armored with {join(types)} ({p} points), and possesses {join(options)}.
```

- `types` — distinct `ArmorRow.name` values over `design.armor`, in first-appearance order.
  Two layers yield **one** clause and **one** rating (FR-016a): "armored with Titanium Steel
  and Crystaliron (6 points)".
- `p` — `ship.armor_protection`, digits, the ship's single total.
- `options` — distinct `ArmorOptionRow.name` values across every layer, in first-appearance
  order. Each name is its SRD noun phrase ("a stealth coating").

## 13. Special features (FR-017) — omitted when there are no non-hangar fittings

```text
Special features include {join(clauses)}.
```

One clause per fitting entry, in design order, excluding hangars (rendered by sentence 10):

| Row | Clause |
|---|---|
| `counted_in_tons` and `unrefined_fuel_per_ton` set | `{tons(q)} {ton\|tons} of {plural} (processes {tons(q × rate)} tons of unrefined fuel into refined fuel per day)` |
| `counted_in_tons` only | `{tons(q)} {ton\|tons} of {plural}` — "two tons of luxuries" |
| otherwise, `quantity == 1` | `{name}` — the row's name carries its article: "an armory", "fuel scoops" |
| otherwise | `{count(q)} {plural}` — "four detention cells", "six armories" |

## 14. Crew (FR-018) — never omitted

```text
The ship requires a crew of {count(total)}: {join(clauses)}.
```

One clause per `CREW_POSITIONS` row whose count is non-zero, in table order:
`{count(n)} {name|plural}`. A crew of one renders "a crew of one: one pilot." (edge case), not
"a crew of 1: 1 pilots".

## 15. Passengers (FR-019) — never omitted

Both capacities zero:

```text
The ship cannot carry any additional passengers.
```

Otherwise:

```text
The ship can carry up to {join(clauses)}.
```

Clauses, each present only when non-zero:

- `{count(2s)} additional {passenger|passengers} at double occupancy`, where
  `s = max(0, design.staterooms - ship.crew.total)`
- `{count(design.low_berths)} low {passenger|passengers}`

Emergency low berths are survival equipment and are not offered as passenger capacity
(research.md Part F).

## 16. Cost and build time (FR-020) — never omitted

```text
The ship costs MCr{money(cost)} (including discounts and fees) and takes {count(weeks)} {week|weeks} to build.
```

`money` renders full precision with thousands separators, trailing zeros stripped, never
scientific notation: `MCr33.219`, `MCr2,768.145`, `MCr29.772` (FR-025).

---

## Worked example — `specs/010-starship-generator/examples/free-trader.toml`

```console
$ uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml
TL8 Beowulf

Using a 200-ton hull (4 Hull, 4 Structure), the Beowulf is a starship. It mounts jump drive A, \
maneuver drive A and power plant A, giving a performance of Jump-1 and 1-G acceleration. Fuel \
tankage of 22 tons supports the power plant for two weeks and one Jump-1 jump. Adjacent to the \
bridge is a computer Model 1. The ship is equipped with Standard sensors (DM-4). There are four \
staterooms. The ship has two hardpoints and two tons allocated to fire control, but has no \
weapons installed. Cargo capacity is 135 tons. The hull is standard, and no additional armor has \
been installed. Special features include one ton of fuel processors (processes 20 tons of \
unrefined fuel into refined fuel per day). The ship requires a crew of five: one pilot, one \
navigator, one engineer, one medic and one steward. The ship cannot carry any additional \
passengers. The ship costs MCr29.772 (including discounts and fees) and takes 44 weeks to build.
```

(The paragraph is one unwrapped line; `\` marks continuations added for this document only.)
`TL8` is derived: the design's Model 1 computer is TL 7 and its Standard sensors are TL 8, and
no other fitted component carries one. Sentences 8, 9, 10 are absent — the ship has no weapons,
screens or hangars.

---

## Determinism (FR-003, SC-003)

`render_description` reads only `ship`, `ship.design` and the static tables. It reads no clock,
no seed, no environment, no locale. Every grouping iterates an ordered tuple in
first-appearance order, never a `set` or a dict keyed on unordered input. Therefore
`render_description(a) == render_description(b)` whenever `a == b`, byte for byte, in any
process.

## Totality (SC-001)

`render_description` raises for no `Ship` that `build_ship` can return. No sentence can emit
placeholder text, an empty parenthesis, a doubled space, or a dangling comma or conjunction:
every list goes through `join`, which is defined on lists of one, and every omittable sentence
is dropped whole rather than emitted empty.

## CLI (FR-002)

`cetools ship build FILE` and `cetools ship generate` print this text instead of the
label-per-line sheet. `--toml` is unchanged and still emits the round-trippable design;
`--out` still requires `--toml`. Exit codes are unchanged: 0 on success, 1 with the message on
stderr for an unreadable file, malformed TOML, or a rules-illegal design. `generate` still
reports its seed on stderr, which is why the seed never reaches the paragraph.
