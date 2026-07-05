# Contract: `format_character` Mishap Output Extension

`format_character(character: Character) -> str` (`src/cetools/formatter.py`) gains one
new, conditional output line so a caller can satisfy FR-010/SC-002 (determine what
happened to a mishap-affected character) from the printed record alone, without
inspecting `character.mishap`/`character.debt` directly. This extends, and does not
replace, the existing grammar from `specs/006-universal-character-format/contracts/ucf-output.md`.

## Grammar addition

```
output  = line1 "\n" line2 "\n" line3 ["\n" line4] ["\n" mishap_line]

mishap_line = "Mishap: " outcome_desc ["; Debt Cr" debt]
```

`mishap_line` is present **only when** `character.mishap is not None`; omitted
entirely (not a blank line) otherwise — same convention as the existing
`equipment_list` line.

| Symbol | Source | Format |
|---|---|---|
| `outcome_desc` | `character.mishap.discharge_type`, `.imprisoned`, `.injury_reductions`, `.injury_crisis` | See table below |
| `debt` | `character.debt` | Thousands-separated integer; the `"; Debt Cr..."` clause is omitted entirely when `character.debt == 0` |

`outcome_desc` by `discharge_type`:

| `discharge_type` | Text |
|---|---|
| `"honorable"` | `"Honorably discharged"` |
| `"dishonorable"`, `imprisoned=False` | `"Dishonorably discharged"` |
| `"dishonorable"`, `imprisoned=True` | `"Dishonorably discharged (imprisoned)"` |
| `"medical"` | `"Medically discharged"` |
| `"none"` | `"Injured in action"` |

If `injury_reductions` is non-empty, append `", injured (<Stat> -N, ...)"` listing
each affected characteristic and its total reduction, sorted alphabetically by stat
name, e.g. `", injured (Endurance -2, Strength -1)"`. If `injury_crisis` is `True`,
append `", survived an injury crisis"` after the injury-reductions clause (if any).

## Examples

Dishonorable discharge with imprisonment, no injury:

```
Mishap: Dishonorably discharged (imprisoned)
```

Honorable discharge after a legal battle:

```
Mishap: Honorably discharged; Debt Cr10,000
```

Injured in action, no crisis:

```
Mishap: Injured in action, injured (Strength -3)
```

Medically discharged after an injury crisis:

```
Mishap: Medically discharged, injured (Dexterity -6), survived an injury crisis; Debt Cr40,000
```

## Non-goals

This contract only covers the CLI's plain-text rendering. It does not change
`Character`'s field shapes (see `data-model.md`) or introduce any new CLI flags —
existing `cetools character generate` invocations are unaffected except for this one
additional trailing line appearing only for mishap-affected characters.
