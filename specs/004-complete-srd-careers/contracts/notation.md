# Notation: the 004 delta

A delta on [002-rules-data-loading/contracts/notation.md](../../002-rules-data-loading/contracts/notation.md).
The four existing forms, the admissibility table, the malformed-entry reporting, and the
specialty grammar are unchanged. One form is added.

## The grammar, with the addition

```text
entry       := quantified | check | adjustment | grant | bare
quantified  := dice WS name                          # NEW
check       := name WS integer "+"
adjustment  := name WS ("+" | "-") integer
grant       := name WS integer
bare        := name
name        := text [ WS "(" text ")" ]
dice        := <the same notation every dice field takes, d66 excluded>
WS          := one or more spaces
```

## Which forms each context admits

| Context | Admits | Registry a name is checked against |
|---|---|---|
| `SKILL_TABLE` | adjustment, grant, bare | characteristics, skills |
| `BENEFIT_TABLE` | adjustment, bare, **quantified** | characteristics, benefits |
| `GATE` | check | characteristics |

`quantified` is admissible in `BENEFIT_TABLE` and nowhere else. In `SKILL_TABLE` and `GATE` it
is reported the way any inadmissible form is, with the entry as written and the forms the
position accepts.

## The quantified form

```toml
benefits = ["Low Passage", "+1 Int", "Weapon", "Mid Passage", "1d6 Ship Share", "High Passage"]
```

`"1d6 Ship Share"` parses to `QuantifiedBenefit(dice="1d6", name="Ship Share")`: a material
benefit awarding a rolled number of one item.

### Why it anchors on the leading token

`parse_entry` decides which form an entry is by looking at its trailing whitespace-delimited
token, in the fixed order check, adjustment, grant, bare. All three suffixed forms are already
spoken for there, so a trailing count (`"Ship Share 1d6"`) could not be told from a grant
without special-casing the registry the name resolves in, which is exactly the lookup this
module does not do. The source prints the quantity in front, so a leading anchor is both
unambiguous and faithful to what is being transcribed.

Recognition therefore runs before the trailing-token match: if the entry's *first*
whitespace-delimited token is valid dice notation and the context is `BENEFIT_TABLE`, the entry
is quantified and the rest of the text is its name. Otherwise the existing trailing-token
matching runs unchanged, so no entry that parsed before parses differently now.

### Rules

- `dice` is checked by the same `_check_dice` every other dice field uses. `d66` is rejected
  there for the reason it is rejected everywhere: a two-digit table value is not a count.
- `dice` must have a **minimum total of at least one** (FR-011), so that an award always awards
  something. `"0d6 Ship Share"` and `"1d6-6 Ship Share"` are rejected naming the entry, the
  minimum total the notation yields, and that a quantity must be able to award at least one item.
  This is a rule about the *quantity*, not about dice generally: `_check_dice` alone does not
  supply it, because a minimum of zero is legitimate for a modifier elsewhere.
- `name` is taken from the text after the dice token and its whitespace, and is carried as
  written, exactly as a bare `BenefitItem`'s name is. It is matched against the benefits
  registry exactly, with no folding of case or whitespace.
- A name carrying a specialty group is rejected the way a bare benefit item's is; no benefit
  item in the source takes one.
- An entry whose leading token is dice notation and which has no text after it (`"1d6"`) is
  malformed, reported as needing a name after the quantity.

### What the walk does with it

The walk rolls `dice` from the seeded `Roller` and appends the item name that many times to the
character's benefits (FR-011, and the spec's clarification). The consequences are deliberately
confined to the roll:

- The human-readable sheet's existing repeat collapsing prints `Ship Share (x3)`.
- The machine-readable `benefits` array holds three identical plain strings. No quantity field
  enters the JSON contract, which is therefore unchanged.
- A roll of *n* is one draw, so the quantity is determined by the seed.

`QuantifiedBenefit` is not admissible in a skill table, so nothing else in the walk needs to
know about it.
