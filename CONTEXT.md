# CONTEXT.md

The domain language of cetools. Use these terms exactly — in code, in tests, in
commit messages, and in conversation. When a new concept earns a name, it gets
an entry here.

cetools generates characters for the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/).
Where cetools departs from the SRD, the entry says so.

## Domain

**Career** — one of the 24 services a character can enter (Navy, Scout, Rogue,
…). A career is pure data: the targets a character must roll against, its four
skill tables, its ranks, and its benefit tables. Careers never contain logic.

**Assignment** — how a character came to be in a career: chosen by name, taken
from the **draft table**, or drawn at random. The distinction is visible on the
finished character (`drafted`), and nowhere else.

**Draft table** — the six careers a drafted character can land in. It is also
the single source of truth for which careers are **military**; there is no
separate list.

**Term** — four years of service. A term is survived or not; it may bring a
**commission**, an **advancement**, skills, and ageing. A character serves up to
seven terms, and a natural 12 on re-enlistment can force one more.

**Check** — the engine's one universal rule: `2D6 + DM ≥ target`. Qualification,
survival, commission, advancement, the psionics gate and psionic training are
all checks. Nothing else in the rules has this shape, and everything with this
shape is a check.

**DM** — a dice modifier, usually derived from a characteristic via
`characteristic_modifier`. The caller computes its own DM; a **check** only
knows the number.

**Mishap** — what happens when a **term** is not survived: a discharge (honorable,
dishonorable, medical, or none), possibly imprisonment, possibly injury, possibly
debt. A mishap ends the career.

**Injury crisis** — an injury that would reduce a characteristic to zero. The
characteristic is restored to 1 and the character takes debt instead.

**Muster-out** — the benefits drawn on leaving a career: **cash benefits** (at
most three draws) and **material benefits**. A dishonorable discharge forfeits
both.

**Benefit** — one item drawn at muster-out. Cash, a stat boost, an item, or ship
shares. Some material benefits are **once-only** (Explorers' Society, Research
Vessel, Courier Vessel): a career can grant them at most once.

**UPP** — the six characteristics encoded in pseudo-hex. A psionic character's
Psi strength is appended after a hyphen.

## Architecture

The architecture vocabulary (module, interface, depth, seam, adapter, leverage,
locality) is defined by the `/codebase-design` skill and used as written there.

**Rolls** — the engine's single seam for chance. Everything the rules leave to
chance passes through it, and nothing else in the engine touches `random`.

Its interface is four verbs, because the rules only ever do four things:

| verb | meaning |
| --- | --- |
| `check(dm, target, name)` | the **check** rule: `2D6 + dm ≥ target` |
| `two_d6(name)` | a raw `2D6` value the rules do arithmetic on (characteristics, ageing, re-enlistment, Psi strength) |
| `d6(name)` | a `1D6` table index or quantity |
| `choose(items, name)` | a uniform pick from a list — not a die roll at all |

**Roll name** — every roll site is named with a `RollName`. The enum is the index
of every random decision the rules make: read it and you know what the engine
leaves to chance. Names exist so that tests can address a roll by intent
("survival fails in term 2") instead of by position in a die sequence.

Two adapters satisfy the seam: `RandomRolls` in production, `ScriptedRolls` in
tests. A test scripts rolls by name; anything it does not name takes a per-verb
default.
