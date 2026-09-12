# Inventory: wording inconsistencies and questionable gates (FR-021)

**Nothing in this document may be acted on in this feature.** It exists so that
the structural argument and the wording argument never share a review. Each
entry names a concrete site and states the question; none states an answer.

Seeded during planning from the sites already read. The migration extends it as
each parser is converted — an entry added is the correct response to noticing a
disagreement, and changing the words is not.

---

## I-1. An unrecognized key under `[pseudo-hex]` reports at the wrong location

**Site**: `src/cetools/registries.py:239`, in `_parse_pseudo_hex`.

The helper parses at location `pseudo-hex` but calls the unrecognized-key check
with no prefix, so a stray key reports at `"minimum-typo"` rather than
`"pseudo-hex.minimum-typo"`. Every other unrecognized-key call in the five
modules prefixes with its enclosing location.

**Question**: is the bare location intended? If not, the fix is deleting one
argument, and it changes one reported location.

**Preserved how**: the converted helper calls `unrecognized_keys` on the
file-level carrier rather than on its own, with a comment pointing here.

---

## I-2. "Missing" and "wrong type" state the same array rule in different words

**Sites**: the fifteen rows of [data-model.md](data-model.md)'s SC-005 table.

An absent array says `"a non-empty array"` at `chargen.py:63`,
`careers.py:337`, `careers.py:709`, and `careers.py:762`; `"an array"` at
`chargen.py:278`, `chargen.py:598`, `chargen.py:607`, `chargen.py:729`,
`chargen.py:830`, `chargen.py:893`, `chargen.py:1138`, `names.py:71`, and
`names.py:155`; and repeats the wrong-type wording at `careers.py:586` and
`careers.py:861`. A present-but-wrong array then says something else again.

**Question**: this is the same divergence 006 settled for `require_string`,
where the surviving wording was the one that described the rule rather than the
way it was broken. Should the array rule be settled the same way, and to which
words?

**Preserved how**: `require_list`'s `expected_missing`.

---

## I-3. The "at least one" noun varies by field with no rule behind it

**Sites**: `"at least one entry"` (nine sites), `"at least one row"` (two),
`"at least one rank"`, `"at least one ladder"`, `"at least one amount"`,
`"at least one benefit"`.

Some of these read better than the generic noun; some look like whichever word
was to hand. `registries.py:245` breaks the pattern entirely with one string,
`"a non-empty array of strings"`, covering all three ways the field can be
wrong.

**Question**: is the specific noun worth keeping where it is accurate, and
should the fields that have no specific noun be made to agree?

---

## I-4. Three arrays accept empty where their siblings reject it

**Sites**: `chargen.py:188` (`rows[i].effects`), `chargen.py:490`
(`<section>[i].effects`), `registries.py:429` (`skills.<name>`).

Each checks that the value is an array and stops there, so `effects = []`
validates clean. Every other array field in the schema requires at least one
element.

**Question**: is an aging or mishap row with no effects meaningful? A skill
with an empty specialty array is meaningful — it is a non-cascade skill — so
`registries.py:429` is probably right and the other two are probably
oversights, but "probably" is what this list is for.

**Preserved how**: `require_list`'s `allow_empty`.

---

## I-5. Two sibling rules split their wording where a third does not

**Sites**: `registries.py:474`/`485` (`benefits`), `registries.py:294`/`303`
(`characteristics`), against `rules.py:174` (`difficulty-dms`).

`benefits` says `"an array of strings with at least one entry"` when absent or
wrong-typed and `"at least one entry"` when empty. `characteristics` splits the
same way. `difficulty-dms` states one rule one way for all three cases.

**Question**: same question as I-2, one level up: does a rule get one wording or
one per way of breaking it? The three sites currently answer differently.

**Preserved how**: `require_list`'s `expected_empty`, and the hand-written
branches at `registries.py:294-311`, which are table checks and not touched by
`require_list` at all.

---

## I-6. The cross-reference gate skips on any unrelated problem

**Site**: `src/cetools/registries.py:463`, in `parse_skills`.

The cycle check runs only when the skills file has produced no problems at all,
so one misspelled key elsewhere in the file suppresses the report of a genuine
dependency cycle. The author fixes the key, reruns, and only then learns about
the cycle.

**Question**: this reads against the project's own "the number of runs needed
to find every problem in a file is always one" (006 SC-003), which is the rule
the comment at `registries.py:439-443` cites for looping rather than reporting
the first bad specialty. Is the gate protecting the cycle walk from malformed
input it cannot survive, or is it the older habit that rule was written to
replace? If the former, the gate could narrow to the problems that actually
threaten the walk.

FR-017 requires the gate to behave exactly as it does today through this
feature.

---

*Entries I-7 onward are added by the migration commits.*
