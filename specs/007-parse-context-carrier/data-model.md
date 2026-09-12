# Data model and migration inventory: Parse Context Carrier

Two parts. The first is the one entity this feature adds. The second is the
site-by-site inventory the migration works from — the counts SC-002 through
SC-007 measure, resolved to file and line against the tree at
`5f0b11c`.

## Entities

### `ParseContext` (new)

`src/cetools/schema.py`. Full interface in
[`contracts/parse-context.md`](contracts/parse-context.md).

| Field | Type | Notes |
|---|---|---|
| `file` | `str` | the data file's basename; never a glob, never two names |
| `location` | `str` | dotted path, `""` at the top of a file |
| problem collection | `list[ValidationProblem]` | shared by reference with every derived carrier |
| watermark | `int` | the collection's length when this carrier was built; private |

No validation rules of its own and no state transitions: it is immutable in its
three fields, and the only thing that changes is the length of the list it
points at. Descent creates a new carrier rather than mutating one, which is why
a parent's `location` cannot be corrupted by a child.

### `ValidationProblem` (unchanged)

`src/cetools/errors.py`. Frozen, ordered by `(file, location, found,
expected)`. This feature adds no field and changes no value.

### Unchanged everywhere else

`RulesData`, `ValidationReport`, every parsed rules type. The carrier is a
parsing-time object; nothing it holds survives into a `RulesData`.

## The thirteen entry points

Each takes `(data, ctx)` after migration and returns the value or `None`
(research R6). "Called from" is `rules._validate`.

| Kind | Function | Module | Extra arguments |
|---|---|---|---|
| `task-parameters` | `parse_task_parameters` | `rules.py` | — |
| `characteristics` | `parse_characteristics` | `registries.py` | — |
| `skills` | `parse_skills` | `registries.py` | — |
| `benefits` | `parse_benefits` | `registries.py` | — |
| `given-names` | `parse_given_names` | `names.py` | — |
| *(per file)* | `parse_surnames` | `names.py` | — |
| `career` | `parse_career` | `careers.py` | three registries |
| `draft-table` | `parse_draft_table` | `chargen.py` | — |
| `aging-table` | `parse_aging_table` | `chargen.py` | — |
| `mishap-table` | `parse_mishap_table` | `chargen.py` | — |
| `background-skills` | `parse_background_skills` | `chargen.py` | skills registry |
| `medical-tiers` | `parse_medical_tiers` | `chargen.py` | — |
| `chargen-parameters` | `parse_chargen_parameters` | `chargen.py` | — |

Ten are dispatched through `rules._SINGLETON_PARSERS`, which requires one
uniform signature; `parse_career`, `parse_surnames`, and
`parse_background_skills` are called directly. The table cannot hold two
signatures at once, so each parser module's commit updates its own dispatch in
`_validate` (plan, *Approach*).

## SC-002: functions taking the file name (53 counted, 52 removed)

| Module | Count | Disposition |
|---|---|---|
| `chargen.py` | 20 | all take a carrier instead |
| `careers.py` | 12 | all take a carrier instead |
| `registries.py` | 7 | all take a carrier instead |
| `schema.py` | 7 | become methods; `file` comes from `self` |
| `names.py` | 4 | all take a carrier instead |
| `rules.py` | 3 | 2 take a carrier; `_unreadable` keeps its parameter |

`rules._unreadable(file, exc)` builds the problem for a file that could not be
opened, which FR-012 places outside the carrier — there is no carrier to report
through. It is the one exclusion, named in the guard with that reason, exactly
as SC-002 already excludes `generator._table_row`. So the honest count is 53 →
1, or 52 removed. Research R7 records the finding; the plan reports the
corrected number rather than 53 → 0.

`rules._class_effect_problems` does convert: it is a cross-file rule, but it
reports at `rows[i].effects[j].class` inside one named file, which is exactly
what a carrier describes. The loader builds a carrier for the aging file and
one for the mishap file.

## SC-003: `_HEADER_KEYS` (5 → 1)

`frozenset({"schema", "schema-version"})`, byte-identical in `careers.py:45`,
`chargen.py:28`, `names.py:15`, `registries.py:26`, `rules.py:63`. Replaced by
`schema.HEADER_KEYS`; each module drops its copy in its own commit.

## SC-004: problem-passing conventions (3 → 1)

| Convention | Example | Fate |
|---|---|---|
| a caller-owned list passed in and appended to | `careers._parse_ranks(..., problems)` | the shared collection |
| a list returned as the whole result | `registries._acyclic_problems`, `schema.unrecognized_key_problems` | the shared collection |
| a list returned beside the value in a pair | every `parse_*` entry point; `names._require_name_array` | the shared collection |

`chargen.parse_mishap_table` uses two of the three four lines apart
(`chargen.py:601` returns a pair, `chargen.py:602` extends a caller-owned
list).

What survives: a function returns its parsed value or `None`, and `None`
remains the caller's failure signal. What goes away is the problem list
travelling separately.

## SC-005: the non-empty-array idiom (15 → 0), plus four bare guards

The idiom is `found = type_name(raw) if not isinstance(raw, list) else "an
empty array"` guarded by `if not isinstance(raw, list) or not raw`. Every row
becomes one `require_list` call.

| # | Site | Location reported | `expected` | `expected_missing` | `expected_empty` |
|---|---|---|---|---|---|
| 1 | `chargen.py:68` | `careers` | at least one entry | a non-empty array | — |
| 2 | `chargen.py:282` | `rows` | at least one row | an array | — |
| 3 | `chargen.py:559` | `mishaps` / `injuries` | at least one row | an array | — |
| 4 | `chargen.py:692` | `law-level` / `trade-code` / `education` | at least one entry | an array | — |
| 5 | `chargen.py:835` | `tiers[i].thresholds` | at least one entry | an array | — |
| 6 | `chargen.py:897` | `tiers` | at least one entry | an array | — |
| 7 | `chargen.py:1079` | `mustering-out.rank-benefits` / `.material-rank-dm` | at least one entry | an array | — |
| 8 | `careers.py:342` | `tables.<t>.entries` | at least one entry | a non-empty array | — |
| 9 | `careers.py:483` | `ladders[i].ranks` | at least one rank | at least one rank | — |
| 10 | `careers.py:607` | `ladders` | at least one ladder | at least one ladder | — |
| 11 | `careers.py:714` | `mustering-out.cash` | at least one amount | a non-empty array | — |
| 12 | `careers.py:767` | `mustering-out.benefits` | at least one benefit | a non-empty array | — |
| 13 | `names.py:21` | `names` (given) | at least one entry | an array | — |
| 14 | `names.py:159` | `names` (surnames) | at least one entry | an array | — |
| 15 | `registries.py:245` | `pseudo-hex.symbols` | a non-empty array of strings | *(same)* | *(same)* |

Rows 3, 4, 7, 9, and 10 are helpers that receive the raw value while their
caller reports the absent case separately; after conversion the caller passes
the container and the key and the single call covers both rows.

The four further bare "must be an array" guards, which today accept an empty
array and must continue to:

| Site | Reports at | `expected` | Note |
|---|---|---|---|
| `chargen.py:188` | `rows[i].effects` | an array | `allow_empty=True` |
| `chargen.py:490` | `<section>[i].effects` | an array | `allow_empty=True` |
| `registries.py:429` | `skills.<name>` | an array of strings | `allow_empty=True` |
| `registries.py:474` | `benefits` | an array of strings with at least one entry | `expected_empty="at least one entry"` |

`allow_empty` is not a convenience: converting those three without it would
start reporting an empty array that validates clean today, which FR-014
forbids. `registries.py:474` is the mirror case — it *does* reject an empty
array, in different words from the wrong-type row, which is what
`expected_empty` preserves.

Three of `require_list`'s four keyword arguments exist only because the
converted sites disagree about wording. Each disagreement is
[inventory.md](inventory.md) entry I-2 through I-5; if those are ever settled,
the knobs collapse with them.

## SC-006: bespoke problems recorded through the carrier (102), and the 29 that are not

| Module | `ValidationProblem(` constructions | Through the carrier |
|---|---|---|
| `chargen.py` | 40 | 40 |
| `careers.py` | 37 | 37 |
| `registries.py` | 16 | 16 |
| `names.py` | 7 | 7 |
| `rules.py` | 31 | 2 in `parse_task_parameters`, plus `_class_effect_problems` |
| **inside one file** | **102** | **102** |
| **loader / cross-file** | **29** | **0** |

The 29 keep building their problems exactly as they do today: the three that
name a glob, the two that name a pair of files, the unreadable/unlistable/
not-a-regular-file trio, the schema-version and declared-kind rules, the
duplicate-basename and duplicate-career-name rules, and the rest.

## SC-007: the seventeen local emptiness questions (16 functions)

Each becomes `ctx.failed` on the carrier whose scope preserves its current
meaning.

| Site | Function | Scope after | Why |
|---|---|---|---|
| `rules.py:206` | `parse_task_parameters` | file | the list is the file's |
| `registries.py:201` | `_parse_bands` | **fragment** — the band list | the list holds only this band list's problems |
| `registries.py:328` | `parse_characteristics` | file | |
| `registries.py:459` | `parse_skills` | file | |
| `registries.py:463` | `parse_skills` | file | **the cross-reference gate** (FR-017) |
| `registries.py:510` | `parse_benefits` | file | |
| `names.py:77` | `parse_given_names` | file | |
| `names.py:124` | `_parse_surname_entry` | **fragment** — one surname entry | |
| `names.py:179` | `parse_surnames` | file | |
| `careers.py:885` | `parse_career` | file | |
| `chargen.py:95` | `parse_draft_table` | file | |
| `chargen.py:315` | `parse_aging_table` | file | |
| `chargen.py:474` | `_parse_mishap_effect` | **fragment** — one mishap effect | |
| `chargen.py:619` | `parse_mishap_table` | file | |
| `chargen.py:737` | `parse_background_skills` | file | |
| `chargen.py:929` | `parse_medical_tiers` | file | |
| `chargen.py:1162` | `parse_chargen_parameters` | file | |

Seventeen sites, sixteen functions: `parse_skills` asks twice.

One near-miss, named so the conversion does not trip over it: `registries.py:454`
(`if bad:`) also tests a list of problems for emptiness, but `bad` is a
comprehension-local list of specialty problems inspected immediately and
reported in one go, not the function's accumulator. Under SC-007's definition it
is not one of the seventeen and does not become a scope; it keeps reaching the
accumulator by the path it uses today. Counting it would make the number
eighteen, which is the looser reading SC-007 explicitly declines.

Two more shapes that a grep will mis-handle: `names.py:124` is written
`if name is None or problems:`, with the emptiness test second, so a search for
`if problems` misses it; and `registries.py:245`, row 15 above, inlines a
three-way conditional rather than the two-line twin, so it is the one row of the
fifteen that a mechanical rewrite will not match.

The three fragment scopes are the ones the spec's first edge case flags as
likeliest to be missed, and they are the reason `failed` measures against the
carrier's own watermark rather than against the list being empty. Each of the
three is reached through a carrier derived immediately before the fragment is
parsed, so "since I was derived" and "inside this fragment" are the same set.

`registries.py:463` is the gate that must keep asking about the **whole file**:
one bad field anywhere in the skills file still skips the cycle check. It sits
on the file-level carrier, unchanged in meaning. Whether it *should* is
[inventory.md](inventory.md) entry I-6.

If a fourth deeper-than-file scope turns up during conversion, it is converted
the same way and this table and SC-007's count are corrected in the same
commit, per the spec's own assumption.

## Where the location comes from, verified

An AST scan of all 73 named check call sites across the five modules confirms
that every one passes a `location` equal to its enclosing location joined with
the key it checks — including `chargen._parse_chargen_group`, whose
`field_location` variable is `f"{location}.{key}"`. So `self.at(key)` inside
each check reproduces every site byte for byte, and the same holds for the
`prefix` argument of the unrecognized-key check at every site but one.

The exception is `registries.py:239`: `_parse_pseudo_hex` parses at location
`pseudo-hex` but passes no prefix, so an unrecognized key under `[pseudo-hex]`
reports at `"typo"` rather than `"pseudo-hex.typo"`. Preserved by calling
`unrecognized_keys` on the file-level carrier there, with a comment; recorded
as [inventory.md](inventory.md) entry I-1.

## Guards after the migration

Two modules under `tests/guards/`.

**`test_no_duplicate_checks.py`** (rewritten). Walks `ast.ClassDef` for
`ParseContext` in `src/cetools/schema.py` and every module top level under
`src/`, and requires each of the eight check names to be defined exactly once,
as a method of that class. Its "the guard can fail" meta-test and its
underscore-prefixed-copy test carry over, retargeted at a planted class body.
During the migration it tolerates exactly one extra definition per name — the
free function it delegates to — and only in `schema.py`, with the tolerance
stating in the guard itself that it is temporary and that the final commit
closes it (FR-020).

**`test_parsing_layer_shape.py`** (new, final commit). Four facts:

| Fact | How it is checked |
|---|---|
| SC-002 | no function in `careers.py`, `chargen.py`, `names.py`, `registries.py`, or `schema.py` has a parameter named `file`; in `rules.py`, only `_unreadable` may, and the guard names it with FR-012 as the reason |
| SC-003 | the name `HEADER_KEYS` (or `_HEADER_KEYS`) is assigned at module level exactly once under `src/`, in `schema.py` |
| SC-004 | in the five modules, no function annotates a parameter as `list[ValidationProblem]`, and no return annotation contains `list[ValidationProblem]`; the loader's bare `-> ValidationProblem` helpers are unaffected |
| SC-005 | the string literal `"an empty array"` appears in exactly one module under `src/`, `schema.py` |

Each fact gets a planted-violation self-test, per FR-023 and the obligation
every existing guard in this project carries.
