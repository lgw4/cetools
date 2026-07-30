# Quickstart: validating acceptable values at the ship prompts

**Branch**: `001-prompt-acceptable-values` | **Date**: 2026-07-29

Runnable scenarios that prove the feature works end to end, one per user story plus the success
criteria that need a session to check. Contract details live in
[contracts/prompt-contract.md](./contracts/prompt-contract.md); this file is how you *run* it.

## Prerequisites

```shell
uv sync
uv run pre-commit install --hook-type pre-push   # once per clone
```

## The gate

All five must pass before the change is committed (Constitution, Development Workflow):

```shell
uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

`pytest` enforces the 85% coverage floor on `src/cetools`.

---

## Scenario 1: every closed question names its answers (US1, SC-001)

Press Enter through a full starship session and read the prompts.

```shell
printf '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: every question below appears with its values in parentheses. Compare against
[contracts/prompt-contract.md](./contracts/prompt-contract.md) §1—the strings there are exact.

```text
Hull class (starship, small craft) [starship]:
Hull tonnage (100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000) [roll]:
Configuration (distributed, standard, streamlined) [roll]:
Jump rating (1-6 on some starship hull) [roll]:
Maneuver rating (1-6 on some starship hull) [roll]:
Power plant rating (1-6 on some starship hull) [roll]:
Armor (titanium steel, crystaliron, bonded superdense, each with a percent, or none) [roll]:
Computer model (1-7, none) [roll]:
Electronics (standard, basic civilian, basic military, advanced, very advanced, none) [roll]:
Staterooms (a count, or none) [roll]:
Fitting (armory, detention cell, fuel scoops, fuel processor, laboratory, library, luxuries, vault, none) [roll]:
Turrets (1-50 on some starship hull, none) [roll]:
Weapon bay (missile bank, particle, meson, fusion, none) [roll]:
Screen (meson screen, nuclear damper, none) [roll]:
Name (any text, or none) [roll]:
Purpose [none]:
```

Then the small-craft session, which must show two absences and no starship-only value:

```shell
printf '\n\n\n\n\n\n\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --small-craft --seed 42 2>&1 >/dev/null
```

**Expected**: `Hull tonnage (10-95 by 5)`; no `Jump rating` and no `Weapon bay` line at all
(AS 1.6); `Screen (meson screen, nuclear damper, none) [none]:`—the values plus the honest
default (FR-004, spec Edge Cases).

**Also check**: the fitting list does **not** name a small craft hangar (AS 1.4), and the computer
models appear as the range `1-7` rather than enumerated (AS 1.5, FR-005).

**Note the two prompts that carry no floor clause**: with no drive pinned, `power_floor` returns
`None` and the power-plant question reads `Power plant rating (1-6 on some starship hull) [roll]:`
with no `at least` (FR-013). The small-craft walk reads
`Turrets (1 on some small craft hull, none) [roll]:`, every small craft having exactly one
hardpoint.

## Scenario 2: hull-dependent questions name what this hull can take (US2, FR-009 to FR-013)

Pin a 40-ton small craft, then a 3-G drive:

```shell
printf 'small craft\n40\n\n3\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**:

- `Maneuver rating (1-3) [roll]:`—narrowed to what 40 tons carries beside a plant and a cockpit,
  not the `1-6` the drive table tabulates (AS 2.2).
- `Power plant rating (3, at least 3) [roll]:`—the plants available beside a 3-G drive, and the
  floor still stated (AS 2.3, FR-013).

Now a 200-ton starship, for hardpoints:

```shell
printf '\n200\n\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: `Turrets (1-2, none) [roll]:`—a 200-ton hull has two hardpoints (AS 2.5), the two
counts collapsed to a range because their step is 1 (FR-005).

And the unnarrowed case—Enter at hull tonnage:

```shell
printf '\n\n\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: `Jump rating (1-6 on some starship hull) [roll]:`—the phrase is what stops the
prompt implying the eventual hull can take all of them (AS 2.4, FR-011).

And the turret count in that same state, which is the one prompt whose accepted set *narrows* with
this feature:

```shell
printf '\n\n\n\n\n\n\n\n\n\n\n51\nnone\n\n\n\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: `Turrets (1-50 on some starship hull, none) [roll]:`, and `51` refused with
`available: 1-50, none` before the question is asked again (FR-011, FR-016). Today `51` is accepted
here, because a count is checked only when a tonnage is pinned.

And the empty case, reachable only through the revise loop
([research.md Decision 9](./research.md)): press Enter at hull tonnage, pin a manoeuvre rating the
whole ruleset allows, then revise `hull tons` to a tonnage that cannot carry it and revise
`power rating`.

```shell
printf 'small craft\n\n\n6\n\n\n\n\n\n\n\n\n\n\nrevise\nhull tons\n10\npower rating\n6\n\n' \
  | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: `Power plant rating (a 10-ton hull can carry none, at least 6) [roll]:`—no value
named, the floor still stated (FR-012, FR-013). Typing `1` is **refused** with that same reason
rather than accepted, because Enter is the only answer an empty set takes; pressing Enter leaves the
plant to generation.

## Scenario 3: answers may be typed the way they are shown (US3, FR-015)

Type each displayed spelling back:

```shell
printf '\n200\n\nbonded superdense 15\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --toml --seed 42
```

**Expected**: no refusal; the emitted TOML carries `type = "bonded_superdense"` (AS 3.1). Repeat
with `bonded_superdense 15` for an identical result (AS 3.2), and at a turret mount question try
`pop-up`, `pop up` and `pop_up`—all three accepted (AS 3.3).

Then a refusal, to check FR-016:

```shell
printf '\n200\n\nbonded superdence 15\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: the reason names the types with spaces, matching the prompt above it, and the armour
question is asked again (AS 3.5, AS 1.7).

Then the numeric refusals, which must match the prompt's *notation* and not a bare list (FR-016):

```shell
printf '\n150\n200\n\n\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**: `150 tons is not a tabulated hull size; valid: 100-1000 by 100, 1200-2000 by 200,
3000-5000 by 1000`—the same runs the prompt collapsed, not the eighteen numbers the engine's own
message lists for library callers.

## Scenario 4: armour options can be pinned (US4, FR-017 to FR-021)

```shell
printf '\n200\n\ncrystaliron 10\nreflec stealth\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --toml --out /tmp/pinned.toml --seed 42
```

**Expected**:

- `Armor options (reflec, self sealing, stealth) [none]:` appears directly after the armour
  question (AS 4.1).
- `/tmp/pinned.toml` carries `options = ["reflec", "stealth"]` under `[[armor]]` (AS 4.2, FR-020).

Round-trip it, which is the whole of FR-020:

```shell
uv run cetools ship build /tmp/pinned.toml --toml | diff - /tmp/pinned.toml && echo "round-trips"
uv run cetools ship build /tmp/pinned.toml | grep -i -e reflec -e stealth
```

**Expected**: identical TOML, and the description names a reflec coating and a stealth coating.

Then the three negative cases:

| Answer at armour | Expect |
|---|---|
| `none` | the options question is **not** asked (AS 4.4, FR-019) |
| Enter | the options question is **not** asked (AS 4.5, FR-019) |
| `crystaliron 10` then `reflec reflec` | refused with the reason, asked again (AS 4.6, FR-018) |
| `crystaliron 10` then Enter | armour layer with no options (AS 4.3) |
| `crystaliron 10` then `none` | armour layer with no options—the literal `none` is accepted though the prompt does not name it (FR-018) |
| `crystaliron 10` then `reflec, stealth` | both options—commas separate as well as spaces (FR-018) |
| `crystaliron 10` then `self sealing` | the two-word option, typed exactly as displayed, is **one** option and not two unknown words (FR-018) |
| `crystaliron 10` then `reflec self sealing` | both options—the greedy scan takes the longest run that names a value (FR-015) |
| `crystaliron 10` then `reflec bogus` | refused **whole**, pinning neither, and asked again (FR-018, spec Edge Cases) |

One more revise case, for FR-021's second half: pin `crystaliron 10` and `reflec`, revise `armor`,
and answer `none` at the re-asked armour question. The options go with the layer they belonged
to—there is no armour left for them to attach to, and FR-019 leaves no question to carry them.

## Scenario 5: the revise loop (FR-007, FR-021)

Force a shortfall, then read the revise prompt and answer it in each accepted form:

```shell
printf '\n100\n\n\n\n\ncrystaliron 90\n\n\n\n\n\n\n\n\n\nrevise\narmor\ncrystaliron 5\n\n' \
  | uv run cetools ship generate --interactive --seed 42 2>&1 >/dev/null
```

**Expected**:

- `Revise which answers (hull class, hull tons, …, purpose) [all]:` names all sixteen, wrapping
  onto three lines (FR-007, SC-005's exemption).
- `armor`, `hull tons`, `hull_tons` and `hull tons, jump rating` are each accepted (FR-015,
  [research.md Decision 4](./research.md)).
- Revising `armor` re-asks the options question under the same rules (AS 4.7); revising
  `configuration` alone leaves pinned options in place (FR-021).

## Scenario 6: the prompt budget (SC-005)

Read every prompt at 80 columns and confirm none takes more than two lines, save the revise
question. The measured lengths are tabulated in [research.md Decision 6](./research.md); the
regression check is a test that asserts each prompt string's length rather than a manual read.

```shell
uv run pytest tests/test_cli.py -k prompt_length -v --no-cov
```

## Scenario 7: nothing else moved (SC-007, FR-008)

Seed parity: a session answering nothing must produce the ship generation produces without the flag.

```shell
printf '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --seed 42 > /tmp/via-wizard.txt
uv run cetools ship generate --seed 42 > /tmp/direct.txt
diff /tmp/via-wizard.txt /tmp/direct.txt && echo "seed parity holds"
```

Stream discipline: stdout must carry only the design.

```shell
printf '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' | uv run cetools ship generate --interactive --toml --seed 42 2>/dev/null | head -3
```

**Expected**: valid TOML from the first line—no question text (FR-008).

## Scenario 8: the invariant, exhaustively (SC-002, SC-006)

The claim "the displayed set is the accepted set" is a test, not a read-through:

```shell
uv run pytest tests/test_cli.py -k acceptable_values -v --no-cov
uv run pytest tests/test_prompts.py -v --no-cov
uv run pytest tests/test_ship_generator.py -k accessor -v --no-cov
```

**Expected**: the parametrised contract test covers every closed-set prompt in
[contracts/prompt-contract.md](./contracts/prompt-contract.md) §1, and fails if a prompt is added
without a row.

For SC-006, add a throwaway row to a rules table and confirm the prompt changes with no edit to
`ship.py`:

```shell
uv run python -c "
from cetools.engine.ships import screen_kinds
from cetools.engine.ships import tables
tables.SCREENS['test_screen'] = tables.SCREENS['meson_screen']
print(screen_kinds())
"
```

**Expected**: `test_screen` in the result, and—run through a session—`test screen` at the
prompt, spelled from the key with no second edit.

## Documentation (FR-022)

The README's interactive section (currently lines 315-323 and 340) says a refusal is how a referee
learns the acceptable values. That must change to describe what a prompt now shows, and the armour
paragraph must mention the options question. `scripts/check_docs.py` is part of the gate, so the
prose is checked with the code.
