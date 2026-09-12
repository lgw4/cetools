# Contract: the parse context carrier

**Module**: `src/cetools/schema.py`

**Audience**: the five modules that parse rules data files — `rules.py`,
`careers.py`, `registries.py`, `names.py`, `chargen.py` — and the loader in
`rules.py` that constructs one carrier per file.

**Status**: package-internal. Nothing here appears in `cetools/__init__.py`'s
`__all__`, and nothing outside the package is expected to import it.

**Relationship to
[`006-validation-vocabulary/contracts/schema-vocabulary.md`](../../006-validation-vocabulary/contracts/schema-vocabulary.md)**:
that contract keeps authority over the *wording* of the original seven checks —
every `found` and `expected` string, row by row — because that wording is
exactly what this feature promises not to change (FR-025). Its **signatures**
are superseded by this document, and it receives one added line saying so and
no other edit. Where the two disagree about a string, it wins; where they
disagree about a call shape, this one does.

## What the carrier is

One object holding the three things the parsers carry by hand today:

| Field | Meaning |
|---|---|
| `file` | the data file's basename, as it appears in a `ValidationProblem` |
| `location` | the dotted path of the point currently being read; `""` at the top of a file |
| the problem collection | a `list[ValidationProblem]`, shared with every carrier derived from this one |

Plus one derived value that is not a field the caller sets: the **watermark**,
the length of the collection at the moment this carrier was constructed. It is
what `failed` measures against.

Its meaning is **a point inside one named file** (FR-013). It cannot describe a
glob, a pair of files, or a file that could not be opened; see *What the
carrier does not describe*.

## Construction and descent

```python
class ParseContext:
    def __init__(
        self,
        file: str,
        location: str = "",
        problems: list[ValidationProblem] | None = None,
    ) -> None: ...

    def at(self, *parts: str | int) -> "ParseContext": ...
```

`problems` defaults to a new empty list. Passing one adopts it **by
reference**, which is how a child shares its parent's collection and how the
loader can build a carrier over a list it already holds.

`at` returns a new carrier with the same `file` and the same collection object,
and a location extended one part at a time:

| Part | Location before | Location after |
|---|---|---|
| `"task"` | `""` | `"task"` |
| `"roll"` | `"task"` | `"task.roll"` |
| `0` | `"names"` | `"names[0]"` |
| `"entries", 3` | `"tables.service"` | `"tables.service.entries[3]"` |
| `"class"` | `"rows[2].effects[0]"` | `"rows[2].effects[0].class"` |

A `str` part is a key and joins with a dot, except against an empty location,
where it joins with nothing — that empty case is FR-003 and is the one an
f-string at the call site gets wrong (`".task"`). An `int` part is an array
index and joins as `[n]`. `at()` with no parts returns an equivalent carrier
with a fresh watermark, which is the scope-only descent; no site needs it
today and it is not part of the interface's promise.

The new carrier's watermark is the collection's current length, so a child
carrier is also a scope (below).

## Reporting

```python
    def report(self, *, found: str, expected: str) -> None: ...
```

Appends `ValidationProblem(file=self.file, location=self.location,
found=found, expected=expected)` to the shared collection. Keyword-only: two
strings of the same type in a fixed order are the argument pair a positional
call gets silently backwards.

To report one level down without descending, chain:
`ctx.at("kind").report(found=..., expected=...)`.

This is how all ~102 bespoke problems inside the per-file parsers are recorded
(FR-009). A bespoke site supplies only `found` and `expected`.

## Reading the collection

```python
    @property
    def problems(self) -> tuple[ValidationProblem, ...]: ...

    @property
    def failed(self) -> bool: ...
```

`problems` is the whole shared collection as a tuple, in insertion order — the
loader reads it after a parse returns and extends its own run-wide list, which
it then sorts exactly where it sorts today (FR-015).

`failed` is `True` when anything has been recorded **since this carrier was
constructed**. A carrier is therefore its own scope:

- the carrier the loader builds for a file answers *"did anything in this file
  fail"* — the fourteen file-scope questions, including the skills parser's
  cross-reference gate, which must keep asking about the whole file (FR-017);
- a carrier derived immediately before a fragment is parsed answers *"did
  anything in this fragment fail"* — the three fragment scopes
  (`_parse_mishap_effect`, `_parse_surname_entry`, `_parse_bands`).

`failed` never sees a sibling's problems, because a sibling's problems were
recorded after this carrier's watermark only if they were recorded *inside*
this scope. It does see problems recorded by descendants, which is the point.

## The eight checks

Each is a method. The carrier supplies `file`; the location is the carrier's
own, extended by the key where the check takes one. Every check appends to the
shared collection and never raises. Return value is the accepted value or
`None`, with the two exceptions noted.

```python
    def require_int(
        self, container: Mapping[str, object], key: str, *, minimum: int | None = None
    ) -> int | None: ...

    def require_string(self, container: Mapping[str, object], key: str) -> str | None: ...

    def require_bool(self, container: Mapping[str, object], key: str) -> bool | None: ...

    def require_roll(self, container: Mapping[str, object], key: str) -> str | None: ...

    def require_dict(self, value: object, *, expected: str) -> dict | None: ...

    def optional_bool(
        self, container: Mapping[str, object], key: str, *, default: bool = False
    ) -> bool: ...

    def unrecognized_keys(
        self, data: Mapping[str, object], allowed: frozenset[str] | set[str]
    ) -> None: ...

    def require_list(
        self,
        container: Mapping[str, object],
        key: str,
        *,
        expected: str,
        expected_missing: str | None = None,
        expected_empty: str | None = None,
    ) -> list | None: ...
```

### Where each check reports

- The six container-and-key checks report at `self.at(key)`. This is not a
  choice: an AST scan of all 73 named call sites confirms every one of them
  passes a location equal to the enclosing location joined with the key, so
  deriving it is byte-identical at every site.
- `require_dict` reports at `self.location`, because it takes a value rather
  than a container and a key — the asymmetry the 006 contract already explains
  and keeps. The caller descends first:
  `ctx.at("task").require_dict(data.get("task"), expected="a [task] table")`.
- `unrecognized_keys` reports each extra key at `self.at(key)`, which
  reproduces today's `prefix` argument (`""` at a file's top level,
  `f"{location}."` below it) at every site but one — see *The pseudo-hex
  exception*.

### `require_dict`, `optional_bool` and the five type checks

Behavior — every `found` and `expected` string, and every returned value — is
unchanged from the tables in the 006 contract, which remains authoritative.
`optional_bool` remains the one check that always yields a `bool`.
`unrecognized_keys` is the one behavioral difference in the seven: it appends
instead of returning a list, because a check that returns problems is one of
the three problem-passing conventions SC-004 removes. Its sort by key name is
unchanged, and is what keeps a report of the same file reading the same way on
every run.

### `require_list` (FR-008, new)

The eighth check, replacing fifteen hand-written copies of the same idiom and
absorbing four further bare "must be an array" guards.

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| key absent | `"missing"` | `expected_missing`, defaulting to `expected` | `None` |
| value not a `list` | `type_name(value)` | `expected` | `None` |
| value is `[]` | `"an empty array"` | `expected_empty`, defaulting to `expected` | `None` |
| value is a non-empty `list` | — | — | the list |

Three `expected` strings rather than one, because the converted sites really do
say three different things and FR-008 requires each to keep its words. Most
sites need one or two:

| Site | `expected` | `expected_missing` | `expected_empty` |
|---|---|---|---|
| `chargen` `careers` | `"at least one entry"` | `"a non-empty array"` | — |
| `chargen` `rows` | `"at least one row"` | `"an array"` | — |
| `careers` `ranks` | `"at least one rank"` | — | — |
| `registries` `pseudo-hex.symbols` | `"a non-empty array of strings"` | — | — |
| `registries` `benefits` | `"an array of strings with at least one entry"` | — | `"at least one entry"` |

The full nineteen-row table is in [data-model.md](../data-model.md). The
divergences the table exposes are recorded in
[inventory.md](../inventory.md) and are **not** reconciled here: a feature that
promises nothing it reports changes cannot also quietly improve a message.

An absent key is detected by membership (`key not in container`), not by a
`None` value, matching what the converted sites do. `require_dict`'s
value-taking form keeps reading `None` as missing, for the reason 006's
research R3 gives.

## The pseudo-hex exception

`registries._parse_pseudo_hex` parses at location `pseudo-hex` but calls the
unrecognized-key check with **no prefix**, so an unrecognized key under
`[pseudo-hex]` is reported at location `"minimum-typo"` rather than
`"pseudo-hex.minimum-typo"`. Every other site in the five modules prefixes.

Converting that call on the fragment's carrier would change the report, which
FR-014 forbids. So the helper takes the *file-level* carrier and derives
`ctx.at("pseudo-hex")` internally for its field checks, calling
`ctx.unrecognized_keys(...)` on the file-level one, with a comment saying why.
The question of whether the location is right is
[inventory.md](../inventory.md) entry I-1.

## What the carrier does not describe

Recorded so the boundary is explicit, and because FR-012 and FR-013 forbid
reaching for any of it:

- **A glob.** Three problems name `careers/*.toml` or `names/surnames-*.toml`
  rather than a real file.
- **A pair of files.** Two problems name one file in `file` and both in
  `found`. The loader carries a written explanation of why folding two names
  into one `file` field was rejected; that explanation stands.
- **A file that could not be opened.** Unreadable files, unlistable
  directories, and paths that are not regular files are reported before any
  parse begins. `rules._unreadable` therefore keeps its own file-name
  parameter, the single exclusion from FR-011 (research R7).
- **Any other cross-file rule.** The twenty-nine problems the loader and its
  file-reading helpers build stay as they are — with one exception:
  `_class_effect_problems`, which is a cross-file rule that reports at a
  location inside one named file, and so is given a carrier.

## Import position

```text
errors.py  ──┐
             ├──> schema.py ──> rules.py, careers.py, registries.py,
tasks.py   ──┘                  names.py, chargen.py
```

Unchanged from 006. `schema.py` cannot fold into `errors.py`: `require_roll`
needs `tasks._check_dice`, and `tasks.py` already imports from `errors.py`.

`HEADER_KEYS` — `frozenset({"schema", "schema-version"})` — is a module-level
constant here, the one definition replacing five (FR-010). It is a constant
rather than a class attribute because it is an argument callers pass to
`unrecognized_keys`, not something the carrier knows.

## Worked example

`rules.parse_task_parameters`, before and after:

```python
# before
problems.extend(unrecognized_key_problems(data, _HEADER_KEYS | {"task", "difficulty-dms"}, file))
task = require_dict(data.get("task"), file, "task", "a [task] table", problems) or {}
problems.extend(unrecognized_key_problems(task, {"roll", "target", "unskilled-dm"}, file, "task."))
roll = require_roll(task, "roll", file, "task.roll", problems)

# after
ctx.unrecognized_keys(data, HEADER_KEYS | {"task", "difficulty-dms"})
task_ctx = ctx.at("task")
task = task_ctx.require_dict(data.get("task"), expected="a [task] table") or {}
task_ctx.unrecognized_keys(task, {"roll", "target", "unskilled-dm"})
roll = task_ctx.require_roll(task, "roll")
```

No file name, no location string, no choice of how the problems travel
(SC-008).
