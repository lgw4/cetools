# Changelog

All notable changes to cetools are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Versioning is CalVer in `YYYY.0M.INC1` form: `2026.08.1` is the first
release cut in August 2026, `2026.08.2` the second. Because CalVer says
nothing about compatibility, breaking changes get their own **Breaking
changes** heading in the entry that ships them.

PEP 440 normalizes the zero-padded month away, so the version installed
metadata reports — and therefore the version `cetools` prints in its
provenance block — drops it: `2026.08.1` here is `2026.8.1` there. The two
name the same release.

## 2026.08.1 (unreleased)

- **README installation points at the published artifact.** `uv add
  cetools` named a package index that has never carried this package. The
  primary instruction is now `uv tool install` against the released wheel's
  download URL, with an alternative that installs from the tagged source
  (`uv tool install git+...@v<version>`) and a third for a project that
  depends on `cetools` as a library rather than installing the command
  (`uv add <the same wheel URL>`). `CONTRIBUTING.md`'s remaining references
  to a PyPI description now name the public release page and the built
  package's description instead (FR-016 through FR-018, FR-024, FR-026).
### Fixed

- **The Universal Character Format's skills line sorted by the rendered
  `"Name-Level"` string instead of by the skill's name (and specialty)
  alone.** A skill whose label is a prefix of another's — `Gun Combat`
  against `Gun Combat (Slug Rifle)` — could render in the wrong order,
  because the space introducing the specialty sorts before the hyphen
  introducing the level. `as_text` now sorts skills by label first and
  appends the level afterward, matching `contracts/cli.md` and the order
  `as_dict`'s `skills` already agreed with (T154).
- **An empty or whitespace-only `--name` was refused only by the CLI.**
  `generate_character` and `generate_batch` now refuse it too, raising
  `CetoolsError`, so a library consumer bypassing the command line cannot
  produce a character whose `name` is `""` — which would render a title
  with a dangling separator and nothing after it (FR-047, FR-053c, SC-018,
  T148).
- **A mishap-ended term could forfeit its benefit roll twice.** One shipped
  mishap row ("Gravely injured and forced out of the service") carried its
  own `forfeit-term-benefit` effect on top of the forfeiture every
  mishap-ended term already incurs unconditionally (FR-020), so a character
  ending a service on that row lost two rolls instead of one. `mishaps.toml`
  no longer declares it, and `forfeit-term-benefit` is dropped from the
  mishap effect schema entirely — the unconditional per-term rule is the
  only place this ever belonged (T145).
- **A characteristic already at the floor could raise a fresh medical-crisis
  debt for a reduction that never happened.** The aging and mishap
  characteristic-class effects tested the characteristic's score *after*
  applying the delta, rather than whether the delta actually reduced
  anything, so a characteristic re-selected while already floored applied a
  delta of zero and still triggered another throw-times-multiplier debt.
  Both call sites now trigger only where the applied amount is itself
  negative (FR-021, T146).
- **The mustering-out cash-roll cap applied per career service rather than
  per character.** `cash_taken` was a local reset to zero on every
  `muster_out_service` call, so a multi-career character could take more
  rolls as cash than `mustering-out.maximum-cash-rolls` allows across their
  whole life. It is now `_Walk` state carried across every service the
  character musters out of (FR-016, T147).
- **A medical bill was one flat point per characteristic sitting at the
  floor, not the per-point cost times the points an injury actually
  reduced.** An injury that reduced a score without flooring it raised no
  bill at all, and a characteristic an aging crisis had already floored —
  the same injury never touched — was billed to the employer regardless.
  `_apply_class_effect` now reports the magnitude of each characteristic it
  actually reduces, and `_raise_medical_bill` bills for exactly those
  points (FR-025, T143).
- **The medical tier's rank modifier was declared in data and read by
  nothing.** `medical-tiers.toml`'s `rank-dm` was parsed but the character's
  rank was never carried into `_raise_medical_bill`, so it always read the
  tier's thresholds unmodified. The term loop's current rank is now passed
  through `_roll_injury` and added to the bill's throw wherever `rank-dm`
  is set (FR-025, T150).
- **Five `StepEffect` kinds — `age`, `rank`, `commission`, `career`,
  `benefit-roll-forfeit` — were declared and never produced.** `render.py`
  carried a rendering case for each, but the walk never constructed one, so
  the cases were dead code reachable only in principle. Dropped from the
  closed set: `career` is already traceable through `HistoryStep.career`
  and `.selected` without a duplicate effect, and none of the five appears
  in FR-030's enumerated list of what must trace to a step (T151).
- **A mustering-out material benefit that adjusts a characteristic was
  invisible to anything grouping the history by `characteristic` effects.**
  `muster_out_service` already ran the change through
  `_apply_characteristic_delta`, which returns correctly-kinded
  `characteristic` effects — including the called-for/applied pair a floor
  clamp produces — but then discarded them and rewrapped a bare scalar as a
  single `benefit`-kind effect instead. Found while strengthening SC-005's
  traceability check (T153) to replay characteristics from history and
  reconcile them against the sheet, which this defect made fail. Now uses
  `_apply_characteristic_delta`'s own effects directly.
- **A shipped name table's `source` named what the entries were rather
  than where they came from**, so no reviewer could check whether the
  entries were actually redistributable under this project's GPL-3.0
  designation, which FR-043e requires. All eight files now cite a real,
  checkable source — see the Breaking changes entry above for what
  changed as a result — and `test_name_tables.py` now asserts that every
  `source` names a checkable reference (contains a URL) rather than only
  that it is non-empty (FR-043e, T149).
- **A character generated under `--rules-data` rendered its pseudo-hex
  profile against the *packaged* symbol table, not the override's.**
  `_characteristic_profile` called `load_rules()` with no override to look
  its symbols up in, so an overridden `[pseudo-hex]` table changed nothing
  about what a character's sheet showed — swapping data did not change
  output, contradicting Constitution V. `Character` gains
  `characteristic_symbols`, one pseudo-hex symbol per `characteristics`
  entry computed at generation time from the rules that produced the
  character; the renderer reads it instead of reloading the packaged
  registry (Constitution V, FR-043, FR-058, T159).
- **Nothing validated that at least one career is `always-available` or
  `re-enterable`.** `generator.py`'s `enter_career` takes a bare
  `next(...)` over each — the qualification fallback (FR-006) and FR-015's
  re-entry exception — with no cross-file check behind either. An override
  clearing both flags on Drifter, the only shipped career declaring
  either, made `cetools validate` report the data set clean and exit 0,
  then made `cetools npc` fail mid-walk with an unhandled
  `StopIteration` instead of failing the load. `rules.py` now rejects a
  data set with neither, naming what is missing (FR-004, FR-006, T166).
- **A supplied name carrying a tab or a newline was accepted and rendered
  verbatim, breaking the sheet it landed on.** FR-047 requires a supplied
  name verbatim, but `--name $'Alex\tRivera'` put a third tab on a line
  FR-046 requires to hold exactly two, and `--name $'Alex\n\nRivera'`
  wrote a blank line inside a sheet — which FR-048a reserves as the
  separator between sheets in a batch. `generate_character`,
  `generate_batch`, and `cetools npc --name` now all refuse a name
  containing a tab or a newline, on the same terms T148's empty-name
  refusal already uses (FR-044, FR-046, FR-048a, FR-053c, T170).
- **An injury's characteristic reduction was recorded under the wrong step
  kind.** `_apply_class_effect` hard-coded `kind="mishap"` on the step it
  appends, and `_roll_injury` called it for the reduction an injury row
  produces, so that reduction was indistinguishable in the history from a
  mishap row's own direct reduction. FR-030a requires each step name which
  kind of step it was. `_apply_class_effect` now takes a `kind` parameter
  (`"mishap"` by default, `"injury"` from `_roll_injury`) (FR-030a, T174).
- **A render-time failure in `cetools npc` wrote an unhandled traceback
  instead of a clean reason.** `as_text`/`as_json` were called outside
  the command's `try/except CetoolsError`, so a failure while rendering —
  `CharacteristicRegistry.symbol` raises `RulesDataError` for a score
  outside the declared pseudo-hex range — propagated uncaught rather than
  the "reason on standard error, nothing on standard output" FR-054
  requires. Rendering is now inside its own `try/except`, using the same
  error-reporting path (`_report_cetools_error`) the generation step
  already uses (FR-054, T175).
- **Nothing validated that the characteristic modifier bands in force
  cover every score `characteristic_dm` can be asked for.** A gap made an
  ordinary walk raise `RulesDataError` mid-generation on a data set
  `cetools validate` had already called valid; an overlap left one band's
  claim on a score silently unreachable, resolved only by which band
  sorts first by `minimum`. A new cross-file rule now requires the bands
  to cover every integer from the pseudo-hex minimum up to the unbounded
  band with no gap and no overlap. The shipped bands already satisfy it,
  so no packaged seed's output changes (FR-039, Constitution V, T180).
- **A die able to produce a total outside a chargen table's row count
  raised a bare `IndexError` instead of a reported failure.** The draft
  table, the mishap table, and the injury table are all read positionally
  off a throw's total, and `contracts/data-files.md` already states that
  a mismatch between the die and the row count is "a data problem
  reported when it is read, not at load" — the same treatment
  `CharacteristicRegistry.symbol` gives a characteristic score outside
  the declared pseudo-hex range. All three reads now raise
  `RulesDataError` naming the file, the throw's total, and the table's
  row count, so `cetools npc` reports the reason on standard error
  instead of an unhandled traceback (FR-054, FR-005,
  `contracts/data-files.md:291`, T181).
- **Nothing validated that a career's entry ladder declares rank 0.**
  `run()` grants the entry ladder's rank-zero bonus with a bare
  `next(r for r in ladder.ranks if r.rank == 0)` on every career entry
  (FR-007), so an entry ladder starting above rank 0 validated clean and
  then raised `StopIteration` mid-walk — the same shape T166 was raised
  CRITICAL for. Every ladder declaring `role = "entry"` must now declare
  rank 0. Every shipped career already does, so no packaged seed's output
  changes (FR-007, FR-007b, T182).
- **An injury row admitted the same five effect kinds a mishap row does,
  though `_roll_injury` performs only `characteristic-class`.** A
  correctly spelled `debt`, `years`, `forfeit-career-benefits`, or
  `roll-injury` effect on an injury row validated clean and then changed
  nothing when the row was read — the closed kind set's own stated
  purpose, "a misspelling is caught rather than becoming a new effect
  nothing performs," defeated by an effect that performs nothing despite
  being spelled correctly. An injury row's `effects` array now admits
  `characteristic-class` only. No shipped injury row uses any of the
  other four, so no packaged seed's output changes (FR-019, FR-024,
  SC-013, T185).
- **A modified aging total was matched against `AgingRow.minimum` alone,
  discarding the declared `maximum`.** `contracts/data-files.md` permits
  gaps between aging rows and its own worked example is a gapped table,
  so a total falling in one was silently read off whichever row sorted
  highest below it rather than failing. The lookup now honors both ends
  of a bounded row's range, keeping the documented floor rule for a
  result below the lowest row, and raises `RulesDataError` for a result
  an override's gap leaves uncovered. The shipped table has no gaps, so
  no packaged seed's output changes (FR-013, FR-037, SC-013, T186).
- **A mustering-out cash or benefit roll silently clamped to the table's
  last row instead of failing on an out-of-range total.** Seven of the
  eight careers shipped six-entry `cash` and `benefits` tables while
  `navy.toml` alone shipped seven, so `mustering-out.retired-cash-dm` or
  `.material-rank-dm` (both at most `1`) pushed a natural 6 onto the same
  row a natural 5 already read — an engine-held clamp
  (`max(0, min(len - 1, total - 1))`) stated in no requirement, contract,
  or data file, the opposite of the treatment every other positional
  table read in this feature gets (T181). Every career's `cash` and
  `benefits` tables now carry a seventh row, repeating the sixth — the
  same shape `navy.toml`'s own cash table already has — and the read now
  goes through `_table_row`, which raises `RulesDataError` for a total no
  row covers rather than absorbing it. The repeated seventh row draws the
  same amount or item the clamp already produced for that collision, so
  no packaged seed's output changes; an override whose modifier pushes a
  total past even the seventh row now fails cleanly instead of silently
  misreading (FR-016, FR-017, T181, T187).

  **Superseded, in this same unreleased entry**: 004-complete-srd-careers
  replaces the padded-seventh-row rule with a computed coverage bound
  (FR-020, FR-021) once transcribing the source literally meant some
  material tables really do stop at six rows. Seven shipped careers
  (`athlete`, `barbarian`, `belter`, `drifter`, `entertainer`, `hunter`,
  `scout`) now carry a six-row `benefits` table rather than a padded
  seventh; `cash` stays seven rows everywhere, and the out-of-range check
  still runs, now against the computed bound instead of a fixed length.
- **The licensing documents a redistributor reads first named every name
  table "this project's own content."** Most of them draw part of their
  entries from CC BY-SA 4.0 Wikipedia or Wiktionary material, or from
  public-domain government census and civil-registry data — each file's own
  `source` field already said so, but neither `README.md` nor
  `CONTRIBUTING.md` mentioned it anywhere. Both now record the source kinds
  and the position taken: CC BY-SA 4.0 is one-way compatible with GPLv3, and
  a bare list of names may not be copyrightable at all, but this project
  credits the source either way. No file's GPL-3.0-only designation changes
  (FR-042, FR-043e, T191).
- **The aging-table contract claimed its own worked example has no gap
  between rows, when it does.** `contracts/data-files.md` states "the
  worked example above has none" immediately below an example whose rows
  jump from `-6` to `0`, a five-value gap from `-5` to `-1` —
  `CHANGELOG.md` already described this correctly elsewhere. T186's code
  fix (reporting a gap rather than silently misreading it) was and stays
  correct; the sentence now says the example is not itself runnable as an
  override rather than claiming a gap it has does not exist (FR-013,
  FR-037, T205).
- **`chargen-parameters.toml`'s `background-skills.characteristic` was
  parsed as a string and checked against nothing.** A referee writing the
  characteristics registry's label (`"Intellect"`) rather than its code
  (`"INT"`) validated clean and then crashed every walk with an uncaught
  `KeyError`, on the second step of every character. Loading now rejects a
  code the characteristics registry does not declare, the same way an
  unresolvable medical tier already is. The packaged file already names a
  code, so no packaged seed's output changes (FR-003, FR-054, T194).
- **`throws.re-enlistment.characteristic` was parsed, registry-validated,
  and never read.** The other four career throws (qualification, survival,
  commission, promotion) all apply the declared characteristic's modifier;
  re-enlistment silently dropped it, so an override declaring one changed
  nothing. The walk now itemizes it the same way the other four do. No
  shipped career declares a re-enlistment characteristic, so no packaged
  seed's output changes (Constitution V, FR-038, FR-014, T195).
- **A characteristic modifier band declared above the unbounded band was
  silently unreachable.** T180's gap-and-overlap cross-file check stopped
  the moment it reached the unbounded band, so a band sorted after it
  (a higher `minimum`) was never checked, and `characteristic_dm` — which
  returns the *first* matching band — always matched the unbounded band
  first, making the higher band dead data with no error raised anywhere.
  The check now requires the unbounded band to hold the highest `minimum`
  of any band. The packaged table's unbounded band already is the
  highest, so no packaged seed's output changes (US4 acceptance scenario
  4, FR-039, Constitution V, T199).
- **Gating every one of a career's skill tables raised a bare `DiceError`
  naming neither the career nor the gate that excluded them.** One gated
  table correctly excludes rather than fails; nothing covered every table
  being gated at once, which reached `roller.die(0)` directly. The walk
  now raises `RulesDataError` naming the career and every table's gate
  when none is eligible. `validate` still passes such an override, since
  which characteristics a generated character carries is a runtime fact
  the loader cannot see; the failure is now nameable rather than opaque
  (US4 acceptance scenario 4, FR-010, FR-054, T203).
- **A mishap or injury `amount` written as `d66`, `0d6`, or `1d0` validated
  clean and then crashed the walk uncaught.** `_valid_amount_text` checked
  the field against its own regex rather than through the same
  `_check_dice` guard every other dice-notation field in the package uses,
  so a two-digit table die (which `parse_notation` answers with `None`,
  raising an uncaught `TypeError` when the walk unpacks it) or a count or
  side count below 1 (an undiagnosed `DiceError`) both passed load. The
  field now routes through `_check_dice`, rejecting the same notation
  `task.roll` and every other `roll` field already reject. No shipped
  mishap or injury row's `amount` is any of these, so no packaged seed's
  output changes (FR-054, US4 acceptance scenario 4, FR-019, T204).
- **Nothing validated that `[characteristics] roll` cannot produce a score
  the characteristics registry has no symbol for.** Both ends are
  statically decidable — `parse_notation` gives the roll's possible span,
  and the registry declares its own pseudo-hex range — but nothing related
  them, so an override narrowing either one made `cetools validate` report
  the data set clean and then failed some seeds mid-walk while others
  succeeded, rather than failing the whole run before any character is
  produced. A new cross-file rule rejects a roll whose possible span
  reaches outside the declared range. The packaged roll (`2d6`) falls well
  within the packaged range, so no packaged seed's output changes (US4
  acceptance scenario 4, FR-039, FR-054, T209).
- **Nothing validated that the aging table's rows are free of overlap or
  that its unbounded row sorts highest.** The aging lookup takes the first
  row whose range covers a modified total, and the parser only counts
  unbounded rows before sorting the rest by `minimum` — the same shape
  T180 and T199 fixed for the characteristic modifier bands, left for the
  one other positional range table in the package. An override changing
  the shipped unbounded row from `"1+"` to `"-1+"`, one character away
  from the natural way to say "aging stops hurting at -1", validated
  clean and then read a row silently shadowed by TOML file order rather
  than the row its author wrote. A new cross-file rule rejects an
  overlapping row and a row sorted above the unbounded one; a gap remains
  permitted, since the lowest row is already a floor. The shipped
  `aging.toml` already satisfies both rules, so no packaged seed's output
  changes (FR-013, FR-037, US4 acceptance scenario 4, Constitution V,
  T210).
- **A skill grant written with an explicit but non-terminal specialty
  resolved to a name no rule gives a level to.** `Vehicle (Aircraft)` is
  syntactically valid — `Aircraft` is one of `Vehicle`'s declared
  specialties — but `Aircraft` is itself a cascade with specialties of its
  own, so the sheet recorded a compound FR-012 exists to prevent. Resolving
  a written specialty now continues drawing through it the same way a bare
  grant already does, landing on the innermost cascade paired with a
  terminal specialty (e.g. `Aircraft (Winged Aircraft)`) instead of
  stopping one level early. No shipped career writes an explicit
  non-terminal specialty, so no packaged seed's output changes; an override
  that does now draws one more time than it used to (FR-012, T100).
- **`MusteringOut.benefits`'s declared type omitted `QuantifiedBenefit`,**
  which `_parse_mustering_out` has placed there and `muster_out_service`
  has handled since FR-011 landed. No behavior changes; the annotation now
  matches what the field actually holds (T106).
- **The mustering-out coverage rule (FR-020, FR-021, D7) checked only the
  `dm` at a career's highest rank, and never bounded the low end.** Neither
  `material-rank-dm` nor `retired-cash-dm` is required to be monotonic, so
  a career whose highest rank's row carries a smaller `dm` than a row at a
  lower, still-reachable rank validated clean and then overflowed a table
  mid-batch; a negative `retired-cash-dm` (`retired-cash-dm` has no
  declared minimum) could likewise drive a throw below row 1 without
  either table being short enough to catch it. The rule now covers every
  rank a career's ladders can reach, bounds each table's ceiling by the
  DM's maximum clamped to zero, and adds a floor check for the DM's
  minimum. The packaged `chargen-parameters.toml` already satisfies both,
  so no packaged seed's output changes.
