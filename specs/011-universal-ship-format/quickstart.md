# Quickstart: Universal Ship Description Format

**Feature**: 011-universal-ship-format

Runnable checks that prove the feature works end to end. Each maps to a user story or success
criterion in [spec.md](./spec.md). Expected text is fully specified by
[contracts/description-format.md](./contracts/description-format.md); this guide says what to
run and what to look for, not how to build it.

## Prerequisites

```bash
uv sync
uv run pre-commit install --hook-type pre-push   # one-time per clone
```

---

## 1. A generated ship reads as an SRD vessel (User Story 1, SC-002)

```bash
uv run cetools ship generate --seed 42
```

**Expect**: a `TL<n> <name>` heading, a blank line, and exactly one unwrapped paragraph.
Read it beside any vessel in
[Chapter 9: Common Vessels](https://evolvedexperiment.github.io/cepheus-srd/common-vessels.html)
— the sentences appear in the same order and use the same wording patterns. The seed is
reported on stderr and appears nowhere in the paragraph (FR-003).

**Also expect**: no sentence for equipment the ship lacks, no placeholder text, no empty
parentheses, no doubled spaces, and no dangling commas or "and" (SC-001).

## 2. The same ship renders identically every time (SC-003, FR-003)

```bash
uv run cetools ship generate --seed 42 > /tmp/a.txt
uv run cetools ship generate --seed 42 > /tmp/b.txt
diff /tmp/a.txt /tmp/b.txt && echo "byte-identical"
```

**Expect**: `byte-identical`. Repeat with `--hull 300` and `--small-craft --hull 40`.

## 3. A hand-authored design (User Story 2)

```bash
uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml
```

**Expect** the paragraph worked out in full at the end of
[description-format.md](./contracts/description-format.md):
heading `TL8 Beowulf`; first sentence "Using a 200-ton hull (4 Hull, 4 Structure), the Beowulf
is a starship."; crew sentence "The ship requires a crew of five: one pilot, one navigator, one
engineer, one medic and one steward."; closing sentence "The ship costs MCr29.772 (including
discounts and fees) and takes 44 weeks to build."

Then build each remaining example and read it:

```bash
for f in specs/010-starship-generator/examples/*.toml specs/011-universal-ship-format/examples/*.toml
do uv run cetools ship build "$f"; echo; done
```

**Expect**: every one is a well-formed heading plus one paragraph naming that design's own
components (SC-001).

## 4. An author-supplied purpose and tech level (User Story 2, FR-028b, FR-029)

```bash
uv run cetools ship build specs/011-universal-ship-format/examples/subsidized-merchant.toml
```

**Expect**: the authored purpose completes the first sentence, and the heading shows the
authored tech level even though it is higher than the derived one — an explicit tech level is
used as given and never re-checked.

Remove both keys from a copy and rebuild: the first sentence must still be grammatical, ending
"is a starship." (FR-029a), and the heading must show the derived value (FR-028).

## 5. Omission (User Story 3, FR-021)

```bash
uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml
```

**Expect** — the Beowulf carries no weapons, screens or hangars:

- No "Installed on the hardpoints are …" sentence.
- No screens sentence, and no "This ship has zero screens".
- No hangars sentence.
- The hardpoint sentence **is** present and reads "The ship has two hardpoints and two tons
  allocated to fire control, but has no weapons installed."
- "The hull is standard, and no additional armor has been installed." — never "armored with
  nothing (0 points)".

## 6. A small craft (User Story 4, FR-026, FR-027)

```bash
uv run cetools ship build specs/010-starship-generator/examples/fighter.toml
```

**Expect**: no jump drive, no Jump rating and no jump wording anywhere; the drives sentence
names only the maneuver drive and power plant and states G-acceleration alone; the fuel sentence
states power-plant weeks only; the computer sentence, when a computer is fitted, says
"Adjacent to the cockpit"; and cargo renders in digits ("Cargo capacity is 6.2 tons").

## 7. Edge cases (spec Edge Cases)

Build the fixtures added for these and confirm each reads correctly:

| Case | Expect |
|---|---|
| Zero cargo | "Cargo capacity is zero tons." |
| Unnamed design (`ship generate`) | "Unnamed Ship" in both the heading and the first sentence |
| Multiple armour layers | one armour clause naming every layer and **one** total: "armored with Titanium Steel and Crystaliron (6 points)" |
| Three identical triple turrets | "three triple turrets armed with missiles", not three clauses |
| Crew of one | "a crew of one: one pilot" |
| Zero non-crew staterooms | "The ship cannot carry any additional passengers." |
| Fractional cost | full precision, no scientific notation, no dangling decimal point |

## 8. Round trip still lossless (FR-033, SC-005)

```bash
uv run cetools ship build specs/011-universal-ship-format/examples/subsidized-merchant.toml --toml --out /tmp/rt.toml
uv run cetools ship build /tmp/rt.toml
diff <(uv run cetools ship build /tmp/rt.toml) \
     <(uv run cetools ship build specs/011-universal-ship-format/examples/subsidized-merchant.toml) \
  && echo "round trip clean"
```

**Expect**: `round trip clean`, and `/tmp/rt.toml` carries both `purpose` and `tech_level`.

## 9. Nothing computed changed (FR-032, SC-005)

```bash
uv run pytest
```

**Expect**: green, coverage at or above 85%. Every pre-existing builder, generator, TOML
round-trip and cost test passes unmodified — only the rendering tests are replaced.

## 10. Adding a component row needs no renderer change (SC-007)

Add one row to a table in `src/cetools/engine/ships/tables.py` — a new screen, say, with its
SRD `name`, `plural` and `tl` — and fit it in a design. Its wording appears in the screens
sentence and its tech level in the derived heading, with **no** edit to
`description.py` or `builder.py`.

This walkthrough proves the property once, by hand. The permanent guard is the SC-007
regression test (tasks.md T051), which injects a synthetic row and asserts the same thing on
every run — a manual check cannot stop a later change from quietly re-hardcoding component
wording.

## 11. Quality gate

```bash
uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

**Expect**: all four green. The docs check is load-bearing here: `render_sheet` is renamed to
`render_description`, so README's worked output, CONTRIBUTING's module map and CONTEXT.md's
ship vocabulary must move with it or the gate fails.
