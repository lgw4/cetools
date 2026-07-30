# Contract: The interactive session's prompt surface

**Branch**: `001-prompt-acceptable-values` | **Date**: 2026-07-29

The user-facing contract of a CLI tool is the text it writes and the answers it takes. This file
fixes both for `cetools ship generate --interactive`, in the order the session asks them. Every
string here is what a test asserts and what the README must describe (FR-022).

**Stream**: every line below goes to **stderr** and never stdout (FR-008). Trailing form is
`{question} ({values}) [{default}]: ` with no newline, exactly as `_ask` writes it today.

---

## 1. Prompts with a closed set of values

The value column is the set as displayed. `none` closes each list that accepts it—it is always the
last value, per FR-002's ordering rule (FR-002, [research.md Decision 8](../research.md)). Words
appear in rules-table order and numbers ascending. Values are spaced, never underscored (FR-014).

| # | Prompt as displayed | Value source | Default | Asked when |
|---|---|---|---|---|
| 1 | `Hull class (starship, small craft) [starship]: ` | `HullClass` | `starship` | no `--small-craft` |
| 2 | `Hull tonnage (100-1000 by 100, 1200-2000 by 200, 3000-5000 by 1000) [roll]: ` | `hull_tonnages(STARSHIP)` | `roll` | starship, no usable `--hull` |
| 2′ | `Hull tonnage (10-95 by 5) [roll]: ` | `hull_tonnages(SMALL_CRAFT)` | `roll` | small craft |
| 3 | `Configuration (distributed, standard, streamlined) [roll]: ` | `Configuration` | `roll` | always |
| 4 | `Jump rating (1-6) [roll]: ` | `available_ratings` | `roll` | starship only |
| 5 | `Maneuver rating (1-3) [roll]: ` | `small_craft_maneuver_ratings` / `available_ratings` | `roll` | always |
| 6 | `Power plant rating (3-5, at least 3) [roll]: ` | `small_craft_power_ratings` / `available_ratings`, `power_floor` | `roll` | always |
| 7 | `Armor (titanium steel, crystaliron, bonded superdense, each with a percent, or none) [roll]: ` | `ArmorType` | `roll` | always |
| 8 | `Armor options (reflec, self sealing, stealth) [none]: ` | `armor_options()` | `none` | **new**—after a pinned armour type only |
| 9 | `Computer model (1-7, none) [roll]: ` | `computer_models()` | `roll` | always |
| 10 | `Electronics (standard, basic civilian, basic military, advanced, very advanced, none) [roll]: ` | `electronics_packages()` | `roll` | always |
| 12 | `Fitting (armory, detention cell, fuel scoops, fuel processor, laboratory, library, luxuries, vault, none) [roll]: ` | `fitting_kinds()` | `roll` | always |
| 13 | `Turrets (1-2, none) [roll]: ` | `hardpoints()` | `roll` | always |
| 13a | `Turret 1 mount (single, double, triple, pop up, fixed) [roll]: ` | `turret_mounts()` | `roll` | per turret |
| 13b | `Turret 1 weapon (missile rack, pulse laser, sandcaster, particle beam) [roll]: ` | `turret_weapons()` / `small_craft_weapons()` | `roll` | per turret |
| 14 | `Weapon bay (missile bank, particle, meson, fusion, none) [roll]: ` | `bay_kinds()` | `roll` | starship only |
| 15 | `Screen (meson screen, nuclear damper, none) [roll]: ` | `screen_kinds()` | `roll`, or `none` on a small craft | always |

**Note on #7**: the percent is the free part of a compound answer and lies outside FR-002's count.
The prompt states its shape so a referee need not spend a refusal to learn it (SC-003).

**Note on #8**: the answer takes any number of the three, separated by spaces or commas, and also
takes the literal `none`. `none` is *not* named here—the only closed-set list that omits it—because
the Enter label already says it, which is the rule FR-006 applies to `purpose` (FR-018). An answer
mixing a good option with an unknown or repeated one is refused whole.

**Note on #13**: the counts are a closed set (1 to the hull's hardpoints) and `none` for the
deliberately unarmed ship; the digit `0` is accepted as an alternate spelling of `none` and is not
named (FR-002).

**Note on #13b**: on a small craft with tonnage *and* power rating pinned, the set is narrowed by
the plant's energy allowance and the mount already answered, so a `particle beam` may be absent
where a `sandcaster` is not.

## 2. Prompts with an open answer (FR-006)

| # | Prompt as displayed | Names a set? | Names `none`? |
|---|---|---|---|
| 11 | `Staterooms (a count, or none) [roll]: ` | no | yes—`none` pins a deliberate zero that `[roll]` does not |
| 16 | `Name (any text, or none) [roll]: ` | no | yes—`none` pins an unnamed ship |
| 17 | `Purpose [none]: ` | no | **no**—the `[none]` default already says it |

## 3. Prompts outside the design walk

| Prompt as displayed | Accepts | Change |
|---|---|---|
| `Accept this ship or revise [accept]: ` | `accept`, `a`, `revise`, `r` | **none.** Its two values are already named in the question text, each once; `a` and `r` are alternate spellings, which FR-002 excludes from the count. |
| `Revise which answers (hull class, hull tons, configuration, jump rating, maneuver rating, power rating, armor, computer, electronics, staterooms, fitting, turrets, bay, screen, name, purpose) [all]: ` | the sixteen names, spaced, underscored or hyphenated, comma- or space-separated, any case | names all sixteen (FR-007). 199 chars, three lines—the one prompt exempt from SC-005. |

## 4. Narrowing and its two special phrasings

A hull-dependent prompt (#4, #5, #6, #13, #13b) takes one of three forms:

| State | Form | Accepts | Requirement |
|---|---|---|---|
| Narrowed—a tonnage is pinned | `Maneuver rating (1-6) [roll]: ` | the named values, or Enter | FR-010 |
| Unnarrowed—tonnage left to the dice | `Maneuver rating (1-6 on some starship hull) [roll]: ` | the named values, or Enter | FR-011 |
| Empty—this hull can take none | `Power plant rating (a 10-ton hull can carry none, at least 4) [roll]: ` | **Enter only** | FR-012 |

The power plant keeps its floor clause inside the same parentheses in all three forms (FR-013),
including the empty one: the floor its drives require holds whether or not this hull can meet it.

In the empty form the parenthesised group names **no value**, and any typed answer is refused with
the same reason the prompt gave (FR-012). The unnarrowed form's qualifier names the *ruleset*, never
a hull, so a prompt without one reads as a claim about the hull in hand.

A narrowed set is computed from the answers standing when the question is asked, so a question
re-asked in the revise loop after its tonnage changed names the new tonnage's set, and turret 2's
weapon set is narrowed by turret 2's own mount (FR-010).

## 5. Answer forms every closed-set prompt accepts (FR-015)

For a value displayed as `pop up`, all of the following are one answer:

```text
pop up      pop_up      pop-up      Pop Up      POP_UP
```

`key(answer)` is the whole of it: lowercase, then space or `-` to `_`. A value's stored spelling is
therefore always accepted, so an answer copied out of a design file works.

## 6. Refusals (FR-016)

A refused answer names the acceptable values **in the spelling the prompt used**, then the question
is asked again—unchanged behaviour, new spelling:

```text
Fitting (armory, detention cell, …, vault, none) [roll]: bridge
bridge is not a known fitting; known: armory, detention cell, fuel scoops, fuel processor,
laboratory, library, luxuries, vault, none
Fitting (armory, detention cell, …, vault, none) [roll]:
```

The refusal names the same set the prompt named—`none` included, and in the same order—so the two
cannot read as different sets (FR-016). The `…` above is this document abbreviating; the prompt names
every value.

The engine's own messages keep their stored spelling, because a library caller passes stored keys
([research.md Decision 3](../research.md)).

## 7. The invariant, and the test that holds it

For every closed-set prompt in §1:

```text
set of values displayed  ==  set of values the reader accepts  ==  set(accessor(...))
```

One parametrised test over a table of `(prompt, accessor, reader)` rows asserts, per row:

1. every displayed value, typed back verbatim, is accepted (SC-002 first count);
2. every displayed value's stored and hyphenated spellings are accepted (FR-015);
3. `set(displayed) == set(accessor(...))` (SC-002 second count, FR-003);
4. a value not in the set is refused, and the refusal names the set in displayed spelling (FR-016).

"Displayed value" means a value the prompt names, expanded where the prompt named it as notation: a
`1-6` contributes six values to the comparison and the string `1-6` contributes none. The Enter
label, the narrowing qualifier, the floor clause and a compound answer's shape note are likewise
excluded (FR-002). `0` is checked as an accepted alternate spelling at the two count questions, not
as a member of the displayed set.

Adding a question means adding a row. A question added without one fails §7's completeness check,
which asserts the table covers every closed-set reader in `ship.py`
([research.md Decision 5](../research.md)).

## 8. What does not change

- stdout: still a design a pipe can read; `--toml` and `--out` compose exactly as today (FR-008).
- Enter at every question: same ship from the same seed as generation without `--interactive`
  (SC-007).
- A refused answer still costs a line, not the session (AS 1.7).
- `--hull` and `--small-craft` still pre-answer and suppress their questions. A `--hull` that
  disagrees with the chosen class still prints its message, and the question is then asked *with*
  its list.
- Small craft still skip #4 and #14 entirely, and no prompt names a value that ruleset refuses
  (AS 1.6).
- Turret mounts are **not** narrowed on a small craft: `_SMALL_CRAFT_TURRET_MOUNTS` narrows what is
  *drawn*, not what may be pinned, so all five are named (verified at generator.py:268-274).
