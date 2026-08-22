# Contract: Command-Line Surface

**Feature**: `003-npc-generator`

Extends the surface the two previous features established. Only the additions are given
here; `cetools roll`, `cetools check`, and `cetools validate` are untouched in every
respect, and none of their golden files changes.

## `cetools npc`

```text
cetools npc [--seed SEED] [--count N] [--name NAME]
            [--rules-data PATH] [--full] [--json]
```

| Option | Meaning |
|---|---|
| `--seed SEED` | Integer or arbitrary text, as everywhere else. Omitted: drawn from `secrets`. |
| `--count N` | How many characters. Default 1. |
| `--name NAME` | A personal name for the character, used verbatim. Omitted: one is rolled. |
| `--rules-data PATH` | Override location, a directory or a single file, composed exactly as a library load composes it. |
| `--full` | The fuller text rendering instead of the default one. |
| `--json` | Machine-readable output instead of text. |

### Exit codes

| Code | When |
|---|---|
| 0 | Characters were produced |
| 1 | They could not be, which in practice means the rules data did not load |
| 2 | Usage error |

The choice of output mode changes neither the code nor the outcome. No code outside
`{0, 1, 2}` is used.

Usage errors, each naming the option or options at fault:

- `--count` below 1. A count of zero or a negative count is a usage error naming the
  option, rather than a successful run producing nothing.
- `--name` together with `--count` above 1. Naming both, because a name names one
  character and applying it to all of them or to the first alone would each silently
  discard part of what was asked for (FR-053a).
- The inherited `--rules-data` checks: an empty location, one that does not exist, one that
  is neither a file nor a directory.

`--full` together with `--json` is **not** an error. Machine-readable output carries every
field unconditionally (FR-050), so the fuller rendering has nothing to add; the flag is
accepted and changes nothing, and `--full`'s help string says so. Rejecting it was
considered: the combination asks for everything and gets everything, so there is no wrong
outcome to protect against, which is what separates it from `as_text(throw, full=True)`.

### Streams

This is the one place this feature's stream split differs from the rest of the tool, and
FR-051 is the reason.

**Text mode.** Standard output carries exactly the character sheets and nothing else. The
seed, the package version, and the provenance go to standard error. Redirecting the
command's output therefore produces a file that is a character sheet, while both the rule
that generators echo their seed and the rule that provenance always renders are satisfied.

**Machine-readable mode.** The document carries the seed, the version, and the provenance
in-document, and they are **not** additionally echoed to standard error. Standard error is
silent on a successful run, so the stream is not split and the document is self-contained
(spec Assumptions).

In both modes, a failure prints its reason to standard error and produces no output at all
on standard output. A run that cannot trust its rules data produces no character rather
than a character with a caveat.

## Text rendering: the Universal Character Format

The default. Three fixed lines and one conditional one, **tab separated**. The blocks below
show a real rendering; every separator written as a run of whitespace inside a line is a
single literal tab character, and the escaped form beneath each block is what the bytes
actually are.

```text
Lieutenant Amara Okonkwo	9A7B86	Age 34
Navy (4 terms)	Cr55,000
Comms-1, Gun Combat (Slug Rifle)-1, Leadership-0, Melee Combat-0, Navigation-2, Tactics-1, Vehicle-0, Zero-G-1
High Passage (x2), Weapon
```

```text
Lieutenant Amara Okonkwo\t9A7B86\tAge 34\n
Navy (4 terms)\tCr55,000\n
Comms-1, Gun Combat (Slug Rifle)-1, ...\n
High Passage (x2), Weapon\n
```

| Line | Content | Omitted when |
|---|---|---|
| 1 | The rank title, one space, the name; tab; the characteristic profile; tab; `Age ` and the age | never |
| 2 | The careers; tab; `Cr` and the funds | never |
| 3 | The skills | never |
| 4 | The benefit items | the character holds none |

The source material's format defines a fifth line for species traits. Every generated
character is human, so it is the line that is always inapplicable and it is never emitted
(FR-044). The benefit-items line is the one that varies, and SC-009 requires a committed
reference with it and one without.

### The parts

**The name.** The rank title, a single space, then the name. No title, no space: an
untitled character's line begins with the name. The title is the one from the most recently
served career in which the character holds a rank the ladder names a title for; a later
career that left them untitled does not erase an earlier career's title (FR-047c). Noble
titles are never rendered (FR-048).

**The profile.** One pseudo-hex symbol per characteristic, in the order the characteristics
registry declares them, with no separator. `9A7B86` is six characteristics at 9, 10, 7, 11,
8, 6. Which characteristics exist and what order they print in are both data (FR-002).

**The age.** The literal `Age`, one space, the integer.

**The careers.** `Name (N terms)`, comma separated, in the order entered (FR-046). Singular
`term` at one, plural above. A character who served Navy for four terms and then drifted
for one renders `Navy (4 terms), Drifter (1 term)`.

**The funds.** `Cr`, no space, the amount with thousands separators (FR-045). Debt is not
shown here; the format has nowhere to put it, which is why the fuller rendering exists.

**The skills.** `Name-Level`, hyphen, no spaces, joined by comma and a space. Level-zero
skills are shown (FR-045). A cascade specialization is written qualified by its parent so a
reader can find it in the registry: `Gun Combat (Slug Rifle)-1`, not `Slug Rifle-1`
(FR-046). Sorted by `(text.casefold(), text)` over the rendered name-and-specialty, which
is alphabetical as the format states and locale-independent as SC-012 requires.

**The benefit items.** Comma and a space separated, repeats collapsed to `Name (x2)`,
sorted by the same key. Omitted entirely when there are none.

### A batch

Consecutive sheets are separated by exactly one blank line and by nothing else. No index,
no count, no seed, no header may be written between or above sheets, because every byte on
standard output in text mode belongs to some sheet (FR-048a). A batch of one therefore
renders byte for byte as the single character of that seed and position renders.

### Standard error, both text renderings

```text
Seed:  14333185781139156525
Rules: packaged (cetools 2026.8.1)
```

Overridden, with a file ignored:

```text
Seed:  14333185781139156525
Rules: overridden (cetools 2026.8.1)
  navy.toml     replaced  sha256:3b1f...c0
  scouts.toml   added     sha256:9ad4...71
  notes.md      ignored
```

The same provenance block `check` and `validate` write, with the labels unindented because
there is no result heading above them. `render._provenance_lines` gains an `indent`
parameter for it rather than the form being duplicated, so the three surfaces cannot
disagree.

The seed reported is the **master** seed, which is what a referee quotes for a whole table.
Each character's own derived seed is in the machine-readable output (FR-050a); it is not
written to standard error, because a batch of twelve would put twelve lines there and the
one a referee wants is the one that reproduces the table.

## Text rendering: the fuller sheet

`--full`. The Universal Character Format, then a blank line, then what the format has
nowhere to put: the outstanding debt, the pension, and the generation history (FR-049).

```text
Lieutenant Amara Okonkwo	9A7B86	Age 34
Navy (4 terms)	Cr55,000
Comms-1, Gun Combat (Slug Rifle)-1, Leadership-0, ...
High Passage (x2), Weapon

  Debt:    Cr12,000
  Pension: none

  History:
    characteristics                       STR 9, DEX 10, END 7, INT 11, EDU 8, SOC 6
    background-skills                     3 skills: Zero-G 0, Computer 0, Admin 0
    career-selected                       Navy
    qualification        Navy       t1    2, 5 (sum 7) INT +1 = 8 vs 6  SUCCESS
    career-entered       Navy       t1    selected
    basic-training       Navy       t1    Comms 0, Engineering 0, Gun Combat 0, ...
    rank-bonus           Navy       t1    Zero-G 1
    survival             Navy       t1    4, 3 (sum 7) INT +1 = 8 vs 5  SUCCESS
    commission           Navy       t1    6, 4 (sum 10) SOC +0 = 10 vs 7  SUCCESS
    ...
```

The history is the point of this rendering. Each line is **composed from the step's named
parts**, never stored as prose (FR-030a): the kind, the career and term where they apply,
the throw with its faces and each modifier itemized, and the effects that followed. A
consumer who wants the parts reads the machine-readable output, which emits them; this line
is a rendering of the record and never the record itself.

Columns are padded to the longest value present, matching the padding rule the `Modifiers`
block already uses. `Debt:` reads `none` rather than `Cr0` when there is none, and
`Pension:` likewise, so a reader never has to tell a zero from an absence.

In a batch, the fuller sheets are separated by exactly one blank line, the same as the
default ones.

## Golden files

The npc golden files are compared as **bytes**, not as text, through a new
`read_golden_bytes` fixture (research R7). `read_text` opens in universal-newline mode and
would read a CRLF golden back as LF, and no existing golden holds a tab, so the current
comparison has never had to tell a tab from spaces. A format defined by tabs needs a
comparison that can.

`.gitattributes` marks `tests/golden/npc_*.txt` so nothing rewrites their line endings.

SC-009 requires committed references covering, between them: a character with the benefit
line and one without, a character holding a rank title and one holding none, a
multi-career character, a multi-career character titled by an earlier career and untitled
by a later one, and a character carrying a cascade specialization. SC-011 requires a
committed batch reference whose bytes are exactly its sheets with one blank line between
consecutive ones.

## Help text

`npc` and each of its options carry help strings. The licensing guard treats CLI help as a
claim surface, so no help string may name the trademark as something this tool works with.

`tests/integration/test_cli.py` asserts whole-set equality on the options a command's help
screen offers, so `npc` gets its own assertion:

```python
assert options_in_help(["npc"]) == {
    "--seed", "--count", "--name", "--rules-data", "--full", "--json", "--help"
}
```
