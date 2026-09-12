# Phase 0 research: Parse Context Carrier

Ten decisions. Each records what was chosen, why, and what was rejected. The
spec left no NEEDS CLARIFICATION; what needed settling was shape, not scope,
and the user input to `/speckit-plan` fixed most of it. The findings below that
were *not* given — R6, R7, R9 — came out of reading the sites.

## R1. One class in `schema.py`, methods rather than free functions

**Decision**: `ParseContext` lives in `src/cetools/schema.py`. The module keeps
its name. The eight checks are methods on the class; the seven existing free
functions survive only as the delegation bridge (R8) and are deleted by the
final commit.

**Rationale**: the module is already the one home for "a rule about what a data
file may contain", and its import position (`errors.py` + `tasks.py` →
`schema.py` → the five parsers) is the position the carrier needs, unchanged. A
new module would split the vocabulary from the thing that carries it for no
gain, and would need the same imports.

Methods rather than module functions taking a context first: a check's whole
job after this feature is *"ask the carrier"*, and `ctx.require_int(table,
"rank", minimum=0)` is that sentence. `require_int(ctx, table, "rank")` keeps
the caller supplying context — the habit FR-011 exists to end — with the
supplying merely made cheaper.

**Alternatives rejected**: a new `parse_context.py` (splits the vocabulary from
its carrier, and `schema.py` would import it or vice versa either way); a
`Protocol` so parsers could be handed a test double (nothing needs one — the
real carrier over a real list *is* the test double, and it is three fields).

## R2. Descent: `at(*parts)`, one method for keys and indices

**Decision**:

```python
def at(self, *parts: str | int) -> ParseContext
```

A `str` part appends `.key` (or the bare key when the location is empty); an
`int` part appends `[index]`. So `ctx.at("entries", index)` is the user's
spelling, `ctx.at("names")` a plain key, and `ctx.at(index)` an element of the
array the carrier already points at.

**Rationale**: all three shapes occur at real sites. A helper that receives a
carrier already pointing at an array (`_require_name_array`,
`_parse_row_array`, `_parse_rank_bonus_list`) needs the index-only form; a
caller that descends a whole level in one step (`_parse_surname_entry` at
`names[i]`, `_parse_mishap_effect` at `effects[j]`) needs the pair. Two
methods would have made `at(key, index)` a shorthand for `at(key).item(index)`
— two ways to write one thing. The variadic collapses them into one rule about
one method: *string is a key, integer is an index*.

FR-003's identity is then arithmetic rather than a promise:
`""` + `"task"` → `"task"`, `"task"` + `"roll"` → `"task.roll"`, `"names"` +
`0` → `"names[0]"`. The empty parent location is the reason the join is a
method and not an f-string at the call site: the top of a file is the one case
the f-string gets wrong, and it gets it wrong invisibly (`".task"`).

**Alternatives rejected**: `at(key)` plus `item(index)` (two primitives, but
the user's design named `at("entries", index)`, and the variadic satisfies both
readings); a `child(key=None, index=None)` keyword form (a call site would then
read `ctx.child(index=0)`, which is longer than what it replaces).

## R3. Reporting: `report(*, found, expected)`

**Decision**: `ctx.report(found=..., expected=...)`, keyword-only, appends one
`ValidationProblem(file=self.file, location=self.location, ...)`. A site that
reports one level down writes `ctx.at("kind").report(...)`.

**Rationale**: the roughly 102 bespoke sites all supply exactly `found` and
`expected` and today repeat `file=` and `location=` beside them. Keyword-only
because `found` and `expected` are two strings of the same type in a fixed
order, which is precisely the argument pair a positional call gets silently
backwards.

**Alternatives rejected**: a `problem()` name (the module already has
`ValidationProblem`; `report` says what the carrier does with it); accepting a
`location=` override (that is `at()`, and an override would give descent two
spellings).

## R4. Per-scope failure: the watermark is the carrier's own birth length

**Decision**: a carrier records the length of the shared list at the moment it
was constructed. `ctx.failed` is `len(problems) > watermark`. Nothing is
passed, held, or closed by the caller: **the child carrier is the scope.**

**Rationale**: FR-005 asks for per-scope failure, and the seventeen sites that
ask it are each already at the top of the thing they are asking about. The
fragment helpers (`_parse_mishap_effect`, `_parse_surname_entry`,
`_parse_bands`) receive a carrier derived immediately before they run, so
"anything recorded since I was derived" is exactly "anything this fragment
recorded". The file-level carrier is derived at the top of the file, so the
same expression answers the other fourteen.

Because the watermark is computed in `__init__` from the list handed in, a
carrier built over a list that already holds problems is correct by
construction — which is what the loader needs when it builds a carrier for a
cross-file rule that reports inside one file (R7).

**Alternatives rejected**: a caller-held token (`mark = ctx.mark()` … `if
ctx.failed_since(mark)`) — correct, but it hands the caller a second thing to
carry, which is the habit this feature removes; a separate list per fragment
(the spec forbids it: FR-004 wants one collection); a `with ctx.scope():`
context manager (a block form for a question asked once at the end of a
function, and `__exit__` has nothing to do).

## R5. One collection per file, not per run

**Decision**: the loader builds one root carrier per file, over a fresh list,
and extends its own run-wide list from `ctx.problems` after the parse returns.

**Rationale**: it is what happens today — every `parse_*` allocates its own
list — so the insertion-order question the spec's second edge case raises is
answered structurally rather than by trusting `problems.sort()`. The sort
still runs and is still load-bearing for order *within* a file (FR-015), but
the migration does not additionally depend on it to erase interleaving
*between* files, because there is none.

**Alternatives rejected**: one carrier over the loader's list for the whole
run. It would work — the watermark makes per-file scoping still correct — but
it puts the feature's central claim on a sort that would then be doing more
work than it does today, for no benefit.

## R6. The entry points take a carrier and return only the value

**Decision**: after migration, the thirteen entry points are
`parse_x(data: Mapping[str, object], ctx: ParseContext) -> Value | None`. The
loader constructs the carrier, calls, then extends from `ctx.problems`.

**Rationale**: FR-011 forbids the file name as a parameter, and the entry
points are where it enters. SC-004 counts the returned `(value, problems)` pair
as one of the three conventions to be removed, and the spec's own assumption
says a function may still return the value or `None` while "the problem list
travelling separately" goes away. Both are satisfied only by this shape.

`value is None` remains the caller's failure signal, and stays exactly as
informative as today: every entry point currently returns `(None, problems)`
whenever `problems` is non-empty, so "returned `None`" and "the carrier failed"
already agree.

**Consequence to plan for**: `rules._validate` calls each entry point, and
`_SINGLETON_PARSERS` maps ten of them by kind through a table that requires one
uniform signature. Mixed signatures cannot coexist in that table, so each
parser's commit updates its own dispatch. Two of the thirteen
(`parse_background_skills`, `parse_career`) are called directly and take extra
registry arguments; they change in the same commit as their module.

## R7. `rules._unreadable` keeps its file name, and SC-002's arithmetic moves by one

**Finding**: SC-002 counts 53 functions taking the file name, of which "3 in
the rules module". Those three are `parse_task_parameters` (rules.py:148),
`_unreadable` (rules.py:248), and `_class_effect_problems` (rules.py:1019).
`_unreadable` builds the problem for a file that could not be opened at all —
which FR-012 and the spec's fourth edge case explicitly place *outside* the
carrier, on the grounds that there is no carrier to report through.

**Decision**: the parsing layer is the thirteen entry points and everything
beneath them. `_unreadable` is a loader helper and keeps its parameter, named
in the guard as the one exclusion with FR-012 as the reason, exactly as SC-002
already excludes `generator._table_row`. The migration therefore removes 52 of
the 53, and the plan states the corrected count rather than quietly reporting
53 → 0.

`_class_effect_problems` does convert: it is a cross-file *rule* but it reports
at a location inside one named file (`rows[i].effects[j].class`), which is
precisely what the carrier describes. The loader builds a carrier for the aging
file and one for the mishap file and passes them in.

This follows the precedent the spec sets for itself over SC-007: a count found
wrong while reading the code is corrected in the commit that finds it, not
worked around.

## R8. Staging: a delegation bridge, one parser per commit

**Decision**: the first commit adds `ParseContext` whose seven inherited checks
call the seven existing free functions. Then one parser per commit, smallest
first: `names.py` (4 functions), `rules.py` (2), `registries.py` (7),
`careers.py` (12), `chargen.py` (20). Then a final commit that moves the seven
bodies into the class, deletes the free functions, and tightens both guards.

**Rationale**: the delegating commit cannot change a message, because it adds
code nothing calls yet and the code it does add is a forwarding call. That is
what makes User Story 3's first acceptance scenario checkable rather than
merely asserted. Smallest-module-first is 006's order and for 006's reason: the
pattern is established four times before it reaches the module holding a third
of the sites.

`require_list` is the exception — it is new, so it has no free function to
delegate to and is written directly in the class in the first commit, with its
own tests, before any of its nineteen sites are converted.

**Alternatives rejected**: converting all five parsers in one commit (the spec
forbids it, and a hundred-site diff is not reviewable); keeping the free
functions permanently as thin wrappers (leaves the old habit reading as normal,
which User Story 2 says is the failure mode).

## R9. `HEADER_KEYS` goes in `schema.py`, bare-named

**Decision**: `HEADER_KEYS = frozenset({"schema", "schema-version"})` at
module level in `schema.py`. Each parser drops its private copy in its own
commit and imports this one.

**Rationale**: five byte-identical copies of a rule about what a data file may
contain, in a feature whose whole subject is such rules having one home. Bare
rather than `_HEADER_KEYS` for the reason the 006 contract gives for the check
names themselves: the leading underscore in this package is reserved for the
two symbols `contracts/library-api.md` makes a stronger promise about, and
`schema.py`'s members are bare.

It is a module-level constant, not a class attribute: it is an argument callers
pass *to* `unrecognized_keys`, not something the carrier knows.

## R10. Verification: an out-of-tree mutation harness, not a new committed corpus

**Decision**: each migration commit is checked by running a mutation harness
before and after and diffing its output; the diff must be empty. The harness
walks every shipped `.toml`, applies a fixed catalog of mutations (delete each
key; retype each key; empty each array and table), validates each mutant, and
writes every problem as one sorted line. Its recipe is in
[quickstart.md](quickstart.md); it is not committed.

**Rationale**: the suite alone is not proof, and 006 learned this the
expensive way — it names a fraction of the distinct `expected` phrasings the
source emits, and the phrasings it never names are concentrated in exactly the
conversions this feature makes riskiest. The harness reaches every one of them
because it derives its inputs from the data files rather than from what someone
thought to test.

**Alternatives rejected**: committing the harness output as a snapshot corpus.
It would be reviewable, but it is thousands of lines of generated text that
every future data-file edit would churn, and FR-016's instinct — that a corpus
adjusted to accommodate a change stops being evidence — applies to a new corpus
as much as to the old ones. Keeping it out of the tree keeps it a check rather
than a thing to maintain.
