# Contract: `format_character` UCF Output

`format_character(character: Character) -> str` (`src/cetools/formatter.py`) is the sole public
contract this feature changes. It is called by the CLI (`cetools generate`) today and is the
interface any future delivery layer (HTTP API, TUI, etc.) would also call — Principle II requires
it stay usable without a CLI in the loop.

## Grammar

```
line1   = [rank_title " "] name "\t" upp "\t" "Age " age
line2   = career " (" terms_served " terms)" "\t" "Cr" funds
line3   = skill_list
line4   = equipment_list            ; OMITTED (no line, not a blank line) when equipment_list is empty

output  = line1 "\n" line2 "\n" line3 ["\n" line4]
```

Where:

| Symbol | Source | Format |
|---|---|---|
| `rank_title` | `character.rank_title` | Literal, omitted (with its trailing space) if empty |
| `name` | `character.name` | Literal, `"<first> <last>"` |
| `upp` | `character.upp` | Literal, existing 6-char pseudohex string, unchanged |
| `age` | `character.age` | Integer, no formatting |
| `career` | `character.career` | Literal |
| `terms_served` | `character.terms_served` | Integer |
| `funds` | `sum(cash benefit amounts)` | Thousands-separated integer, `0` when no cash benefits |
| `skill_list` | `character.skills` | `"<Name>-<Level>"` per entry, sorted alphabetically by name, joined `", "`; empty string when no skills (line still present) |
| `equipment_list` | `character.benefits` where `kind == "material"` | `material_name` per entry, joined `", "`, in benefit-list order |

## Examples

Fully-populated character:

```
Commodore Bruce Ayala	7A6B85	Age 46
Navy (7 terms)	Cr80,000
Engineering-2, Gunnery-1, Navigation-2, Tactics-1, Zero-G-1
High Passage, Explorers' Society
```

No cash benefits, no material benefits, no skills:

```
Starman Alex Kade	5A5555	Age 22
Navy (1 terms)	Cr0

```

(Line 3 is present and empty; there is no line 4.)

## Compatibility notes

- This is a breaking change to the previous multi-section output (`UPP:`, `Characteristics:`,
  `Mustering-Out Benefits:`, `Retirement Pension:` headers, blank-line separators, `(Drafted)`
  annotation) — FR-009 requires the old shape to disappear entirely from default output. There is
  no versioned/legacy output mode; this is a full replacement, not an additive one.
- `character.pension` and `character.drafted` remain valid `Character` fields (see data-model.md)
  — only their rendering is removed.
