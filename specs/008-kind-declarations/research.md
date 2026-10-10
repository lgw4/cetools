# Phase 0 research: Kind Declarations

Nine decisions. The spec left no NEEDS CLARIFICATION, and the user input to
`/speckit-plan` fixed the record's fields, its home, what it replaces, which
tests move, and the commit type. What needed settling was the shape of the
record, how the table is read so that a test can patch it, and the commit
sequence. Line numbers refer to `src/cetools/rules.py` and
`tests/unit/test_rules.py` at `0074436`.

## R1. The record: a frozen, slotted dataclass with positional fields

**Decision**:

```python
@dataclass(frozen=True, slots=True)
class _Kind:
    name: str
    version: int
    arity: Literal["one", "many"]
    canonical_file: str | None = None
    parser: Callable[[Mapping[str, object], ParseContext], object] | None = None
```

Declared positionally, one line per kind:
`_Kind("draft-table", 1, "one", "draft.toml", parse_draft_table)`.

**Rationale**: the record is a bundle of five typed fields with value
semantics, which is what `@dataclass(frozen=True, slots=True)` already means in
this module (`RulesData`, `ValidationReport`). Frozen matters: a declaration
that can be mutated in place is a second source of truth waiting to happen.
`dataclasses.replace` gives the version-bump tests (R6) a one-expression way to
build a bumped copy.

Arity is a two-value `Literal` rather than a `bool` because a bare `True` in a
positional record says nothing, and rather than an `Enum` because two strings
the invariant tests check (R7) are all the job needs. It stays a field even
though it is inferable from `canonical_file`: the user input asks for it, and
FR-015's "every one-file kind declares a canonical file and no many-file kind
does" is only a test if both facts are stated.

Positional, not keyword-only: thirteen keyword-heavy declarations wrap under
black's 99 columns to five or six lines each, and SC-004 requires the module to
end shorter. One line per kind is also the reading the feature exists to give.

No `RulesData` field name (user input): the constructor stays explicit
(FR-010), so a field-name attribute would be a sixth fact with no reader.

**Alternatives rejected**: `typing.NamedTuple` (iterable and indexable, which
invites positional unpacking of a record whose order is not meaningful);
keyword-only fields (R1 line-count argument); an `Enum` for arity (four lines
for two strings); a `field` attribute naming the `RulesData` field (no reader,
per FR-010 and the user input).

## R2. The table is a tuple, read at call time; nothing is derived at import

**Decision**: `_KINDS: tuple[_Kind, ...]`. `_SUPPORTED_VERSION`,
`_SINGLETON_KINDS`, `_CANONICAL_FILE`, and `_KIND_AT_CANONICAL_FILE` are
deleted, not kept as derived module constants. Every reader derives what it
needs from `_KINDS` when it runs:

| Reader | Reads |
|---|---|
| `_packaged_kind_map` | the set of names |
| `_singleton_slots` | names of one-file kinds; the kind whose `canonical_file` is `basename` |
| `_validate`, header checks | a `{name: _Kind}` lookup built once per call, for membership, `version`, and the sorted names in the unknown-kind problem |
| `_validate`, missing/duplicate check | one-file kinds and their `canonical_file` |
| `_validate`, parse loop | kinds with a `parser` |
| `_validate`, presence check | one-file kinds |

**Rationale**: two requirements force it.

- The version-bump tests (FR-012) patch the table. A constant derived from
  `_KINDS` at import would not see the patch, so the test would pass or fail
  for reasons unrelated to the claim it makes. Reading at call time means
  patching `_KINDS` is patching everything.
- FR-015 requires a test that every declared name is unique. A table that is a
  dict keyed by name silently keeps the last of two duplicate keys, so the test
  could not see the defect it exists to catch. A tuple keeps both.

Cost: rebuilding a thirteen-entry set or dict a few times per load. The loader
runs once per load (spec, Assumptions); no performance requirement exists.

**Alternatives rejected**: `dict[str, _Kind]` literal (R2 second bullet;
duplicate keys vanish); keeping the four names as derived constants (R2 first
bullet); a `functools.cache`d lookup helper (a cache is state a patched table
would bypass, the same problem).

## R3. Where the table sits in the module

**Decision**: a new `# --- kind declarations ---` section immediately after
`parse_task_parameters` (after line 191), holding `_Kind` and `_KINDS`.

**Rationale**: `_KINDS` references `parse_task_parameters`, which is defined in
this module. Placed where the four tables are today (lines 58-99), the module
raises `NameError` on import. Putting the section after the one local parser
is a smaller change than moving the parser above `RulesData`, and it leaves the
module's reading order (public types, then the one local schema, then how kinds
are declared, then discovery) intact.

**Alternatives rejected**: moving `parse_task_parameters` to the top (a second
structural move for no reader's benefit); a lambda or string indirection for
the parser (a declaration that does not name its parser is not the one place a
reader looks).

## R4. Declaration order

**Decision**: grouped by the module owning each kind's parser, in the order
the imports appear (FR-003): `rules` (task-parameters), `registries`
(characteristics, skills, benefits), `careers` (career), `chargen` (draft,
aging, mishap, background skills, medical tiers, chargen parameters), `names`
(given names, surnames).

**Rationale**: FR-003 asks for reader order that carries no behavior. The
one-file parse therefore changes from today's hand order (given-names first) to
declaration order (task-parameters first). This is safe for the reason the spec
gives: each file's problems are collected by its own `ParseContext` and folded
in whole, and `problems.sort()` (line 1029) runs once over the lot, so no
report can move (FR-013). The quickstart harness is the check.

## R5. The one-file parse: one loop, one results dict, the helper kept

**Decision**:

- `parse_singleton` stays, as the single place that turns a resolved kind into
  a carrier, a parser call, and folded problems. Its docstring loses the claim
  that call order is load-bearing (FR-011) and keeps the pointer to the single
  sort.
- A `values: dict[str, Any]` keyed by kind name collects every one-file result.
- One loop over `_KINDS` calls `parse_singleton` for each declaration with a
  `parser`. It names no kind (FR-007).
- The background-skills step stays explicit, after the substitutes, and stores
  into `values["background-skills"]`, calling `parse_background_skills`
  directly (FR-001, FR-007).
- The cross-file rules read the kinds they are about into locals once, after
  the loop: `characteristics`, `skills`, `benefits`, `draft`, `aging`,
  `mishaps`, `medical_tiers`, `chargen`. These are kind-specific code, which
  User Story 2 permits.

**Rationale**: keeping the helper means the background-skills step and the
loop share one body rather than two copies of the four-line
carrier-parse-fold sequence. `Any` is the honest type of a dict whose values
are ten unrelated types; `mypy` is optional in this project (pyproject), and
the typed boundary that matters, `RulesData`, is unchanged.

**Alternatives rejected**: inlining the helper into the loop and duplicating it
for background skills (two copies of one sequence); a declared dependency
mechanism for background skills (the spec forbids it); `dict[str, object]`
(every local read would need a `cast`, eight casts to say what `Any` says).

## R6. The two version-bump tests and the literal-version test

**Decision**: the monkeypatches at `test_rules.py:324` and `:342` become

```python
monkeypatch.setattr(rules_module, "_KINDS", tuple(
    replace(k, version=2) if k.name == "benefits" else k for k in rules_module._KINDS
))
```

factored into a small test-module helper, since both tests need it. The loop at
`:824` iterates `k.version for k in rules_module._KINDS`.

**Rationale**: `setattr` on the module attribute is the patch that R2 makes
effective; `replace` keeps every other field of the benefits declaration as
declared. Nothing else in either test changes, which is what FR-012 permits.

## R7. The tests FR-015 adds, and the rewritten pinning test

**Decision**: in `tests/unit/test_rules.py`, beside the pinning test:

1. **Names are unique**: `len({k.name for k in _KINDS}) == len(_KINDS)`.
2. **Arity and canonical file agree**: every declaration's `arity` is `"one"`
   or `"many"`; every `"one"` has a `canonical_file`; no `"many"` has one.
3. **Every one-file kind is parsed exactly once**: the one-file declarations
   without a parser are exactly `["background-skills"]`, and no many-file
   declaration states a parser. Together with FR-001's rule that the explicit
   steps call their parsers directly, this is "parsed by the general loop or
   by the background-skills step, not both, not neither".

The pinning test at `:605-623` is rewritten as
`test_each_declared_canonical_file_is_the_packaged_declarer_of_its_kind`: for
every one-file declaration, `_packaged_kind_map` maps its `canonical_file` to
its `name`. The `sorted(...) == sorted(...)` line goes (there is no second list
to agree with) and so does the `== 11` count (FR-012, SC-005).

No test asserts a count of kinds (SC-005). Test 3 compares a list of names, not
a length.

**Rationale**: these are the three mistakes a declaration can make that the
behavior suite cannot see directly. A duplicate name is the dict-collapse
defect of R2. An arity/canonical mismatch would make `_singleton_slots` or the
missing-kind problem read `None`. A background-skills declaration that also
named a parser would parse the file twice and fold its problems twice, which
the sort would not hide.

**Why the tests fail first**: `_KINDS` does not exist, so all four fail on
`AttributeError`. That is commit 1's red step (Constitution III).

## R8. Three commits, all `refactor(rules):`

**Decision**:

1. **`refactor(rules): declare each rules-data kind once`.** Red: the three
   FR-015 tests and the rewritten pinning test, reading `_KINDS`. Green: add
   `_Kind` and `_KINDS`, and redefine the four old names as expressions over
   `_KINDS`. Readers' code is untouched; `_singleton_slots`'s docstring is
   pointed at the renamed pinning test. After this commit the table is the
   single source, and the old names are views of it.
2. **`refactor(rules): read kind facts from the declarations`.** Red: point the
   two monkeypatches and the `:824` loop at `_KINDS`. The bump tests now fail,
   because the readers still read the derived `_SUPPORTED_VERSION`, computed
   before the patch. Green: `_packaged_kind_map`, `_singleton_slots`, the
   header checks, and the missing/duplicate check read `_KINDS`; delete the
   four derived names; update the part of `_singleton_slots`'s docstring
   that names `_CANONICAL_FILE`.
3. **`refactor(rules): parse one-file kinds in one loop`.** The loop, `values`,
   the explicit background-skills step, the cross-file locals, the presence
   check over one-file declarations, and the constructor reading `values`.
   Remove the load-bearing-order comment. This is Red-Green-Refactor's refactor
   step: no test is added because no behavior is, and the suite plus the
   harness is the check.

No commit has a `CHANGELOG.md` entry (FR-014, user input). Each is green under
the full suite before it lands.

**Rationale**: commit 1 removes drift in one step while touching no reader, so
a report *cannot* have moved. Commit 2 gets a genuine red from the tests FR-012
changes, rather than a manufactured one. Commit 3 is the largest edit and the
only one that changes parse order, so it is isolated where the harness diff
answers for it alone.

**Alternatives rejected**: one commit (mixes the first red with the parse-order
change, so a harness diff could not be attributed); adding the table beside the
old tables in commit 1 without deriving them (two sources for a commit's
lifetime, the defect this feature removes).

## R9. Proving no report moved

**Decision**: the suite, the unedited corpora, the line count, and a header
harness run in the scratchpad (never committed) that mutates each packaged
file's header every way the kind and version checks can see, plus one
duplicate-declarer and one removal per one-file kind. See
[quickstart.md](quickstart.md). An empty diff against the pre-feature output is
the pass condition for each of the three commits.

**Rationale**: the corpora pin the valid set. The kind machinery's reports are
the unknown-kind, version, missing-kind, duplicate-kind, and slot-occupied
paths, and the suite names only some combinations of those. A harness driven by
the packaged files, not by what anyone thought to test, covers the rest, which
is 007's R10 argument applied to the header rather than the body.
