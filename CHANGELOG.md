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

First release: the dice and 2D6 task-check engine, as a library and a CLI.

### Breaking changes

- **`load_task_parameters` is removed.** Read `load_rules().task_parameters`
  instead. `check`'s `parameters=` keyword is removed too, replaced by
  `rules=`, which takes a `RulesData` rather than a bare `TaskParameters`.
  Package version `2026.08.1` is unreleased, so no published consumer is
  affected.
- **`TaskParameters` no longer carries `characteristic_bands` or
  `characteristic_dm()`.** Both moved to `CharacteristicRegistry`, fed by a
  new `[modifier-dms]` table in `characteristics.toml`; `check` now reads
  `rules.characteristics.characteristic_dm(...)`. `tasks.toml` drops
  `[characteristic-dms]`, and both files rise to `schema-version = 2`. No
  check result changes as a consequence — the committed
  `tests/golden/check_*.txt` files and the existing JSON fixtures are
  byte-identical before and after.
- **A seed's output is a promise only within one package version.** Every
  entry under this heading — including several below, in this and earlier
  releases — reorders, adds, or removes a draw, changes the emitted
  document's shape, or otherwise changes what a seed produces; that is what
  belongs under this heading rather than under Fixed or Added. The promise
  a referee quoting a seed gets is narrower than "nothing changes": it is
  that the same seed against the same package version always produces the
  same character, not that this or any future version reproduces what an
  earlier one did.
- **The career schema rises to `schema-version = 3`: every `throws.*` table
  now requires a `dice` field.** The walk's qualification, survival,
  commission, promotion, and re-enlistment throws used to roll a `2d6`
  constant the engine held; they now read their dice pool from the career
  file, closing the last rules constant Constitution V and FR-038 forbid in
  engine code. Every shipped career ships `dice = "2d6"` on every throw, so
  no shipped seed's output changes; a career override file written against
  schema v2 must add `dice` to each of its throws to keep validating.
- **`navy.toml`'s enlisted ladder gains a rank above zero.** Every shipped
  career's entry ladder previously declared a single rank 0, so an
  uncommissioned character's `ranks_above` was always empty and the
  promotion throw the term loop already attempts for the ladder a
  character is currently on was never actually rolled for entry-ladder
  service. Adding rank 5 ("Petty Officer") to Navy's `enlisted` ladder
  means that throw now fires for every uncommissioned Navy term, which
  reorders the draw sequence: every character a seed produces that serves
  in Navy without commissioning changes from this version forward
  (FR-033, FR-007b, FR-056b, T155).

  **Superseded, in this same unreleased entry**: 004-complete-srd-careers's
  convergence pass (T095) found the source prints no such rank — "Petty
  Officer" was invented to exercise this engine path, not transcribed. It
  is removed; see "Navy's rank ladders are corrected against the source"
  below. The path it was added to exercise now runs off a unit fixture
  instead of shipped data.
- **All eight name tables' entries are replaced.** Every `source` line
  named what kind of names a table held rather than a source a reviewer
  could find and check the terms of, which FR-043e requires. Each file's
  `source` now cites a real public-domain, government/census, or
  CC BY-SA-licensed source, and its `names` are drawn from that source
  rather than the prior unsourced entries; sizes changed too (given names
  66 → 185; surnames: Africa 45 → 52, Asia 45 → 52, Central America
  45 → 48, Europe 99 → 105, indigenous peoples 45 → 68, North America
  45 → 54, South America 44 → 80). A rolled index into a differently
  sized, differently ordered table names a different person, so every
  character a seed produces changes from this version forward (FR-043e,
  FR-056b, T149).
- **A medical crisis could arise from a mishap or an injury, not only from
  aging.** `_apply_class_effect` — the reduction machinery the term loop's
  direct mishap effects and `_roll_injury` both use — triggered a crisis
  debt whenever its reduction floored a characteristic, even though FR-021
  defines a crisis as arising from an *aging* effect specifically. A
  mishap or an injury that floors a characteristic no longer rolls for a
  crisis debt at all; `_apply_aging_if_due` is now the only place one is
  raised. Every character whose walk used to reach that branch draws fewer
  dice from that point forward and produces a different rest of their life
  (FR-021, FR-056b, T160).
- **Debt settlement restored nothing and left no trace.** Two problems in
  one: a medical bill's partial payment discarded whatever fraction fell
  short of a full point, so two payments that together covered one point
  restored none of it; and no step recorded a settlement at all — the
  `debt-settled` kind was misapplied to a crisis debt's *creation* instead.
  `_Debt` now carries a payment remainder and a restored-point count across
  settlements, and `settle_debts` records the amount paid and which
  characteristics were restored and by how much, per debt, per call; the
  crisis-creation step is renamed `medical-crisis` so `debt-settled` names
  only real settlement. `history` is a field of `Character`, so renaming a
  step's kind and restoring points that used to stay lost changes every
  character whose walk creates or settles a debt from this version forward
  (FR-025a, FR-030, FR-056b, T144, T157).
- **A settled medical bill restored nothing, or left the reduction
  permanent.** `_raise_medical_bill` charged the character its discounted
  share (`cost_per_point * points * share_owed`) but handed `_Debt` the
  full, undiscounted `medical.restore-cost-per-point` as its per-point
  price, so `settle_debts` priced restoration higher than what was
  actually paid — a partial-share bill paid in full restored zero of the
  points it billed for. Separately, an employer paying the bill in full
  (`owed <= 0`) returned before recording anything: the reduction stood
  permanently and the tier throw that had already happened went
  unrecorded. `_Debt` now carries its own per-point price
  (`owed // total_points`, not the flat rate), and a fully employer-paid
  bill restores its points immediately and records the throw. A
  characteristic restored earlier than before can change a later throw's
  characteristic DM and, with it, whether that throw succeeds — which
  branches the rest of the walk takes — so every character whose walk
  reaches this path changes from this version forward (FR-024, FR-025,
  FR-025a, FR-056b, T161).
- **A mishap's own characteristic reduction was never billed.** The term
  loop discarded the reduction map `_apply_class_effect` returns for a
  mishap row's own `characteristic-class` effect (e.g. mishaps.toml row 1,
  "Injured in action"), so the reduction persisted with no medical bill
  ever raised against it — unlike the structurally identical reduction
  `_roll_injury` produces, which already is billed. FR-024's reduction
  "MUST persist unless the character's medical bills are paid," which
  presupposes a bill exists to pay. The term loop now bills it exactly the
  way `_roll_injury` does: every character whose walk reaches this branch
  now draws the medical tier's `2d6` where it previously drew nothing, and
  any restoration that follows can change a later throw's characteristic
  DM and, with it, which branch the rest of the walk takes — every
  character whose walk reaches this path changes from this version forward
  (FR-024, FR-025, FR-056b, T162).
- **A crisis debt could precede the aging step that caused it in the
  history.** `_apply_aging_if_due` called `_trigger_medical_crisis` from
  inside its class-effects loop, before appending its own `aging` step, so
  `cetools npc --full` could print a `medical-crisis` line above the
  `aging` line that caused it — FR-030 requires the steps in the order the
  walk occurred, which is what makes a surprising sheet diagnosable (US2
  acceptance scenario 4). Every crisis a row's class effects raise is now
  deferred until after the `aging` step is appended, one trigger per class
  effect that reached the floor, same as before. An aging row naming both
  a physical and a mental class effect that each float a characteristic to
  the floor now draws the first effect's crisis dice after the second
  effect's characteristic selection instead of before it, changing every
  character whose walk reaches that branch from this version forward
  (FR-030, FR-056b, T163).
- **A debt's settlement could precede the step that created it.** `add_debt`
  settles immediately — it calls `settle_debts` synchronously, which
  appends its own `debt-settled` step(s) — but all three callers (the
  mishap `debt` effect, `_trigger_medical_crisis`, `_raise_medical_bill`)
  appended their own creation step only *after* calling it, so a
  `debt-settled` step could land in the history before the `mishap`,
  `medical-crisis`, or `medical-bills` step that created the debt it
  settled: `cetools npc --seed 51 --full` printed `debt-settled Cr20,000
  debt, END 1` above the `medical-crisis` that created it. All three call
  sites now record their creation step before calling `add_debt`. `history`
  is a field of `Character`, so reordering it changes what a seed produces
  even though the dice sequence itself is untouched — every character
  whose walk creates a debt changes from this version forward (FR-030,
  FR-056b, T164).
- **A floor clamp's called-for and applied effects were indistinguishable
  in the record.** `_apply_characteristic_delta` emitted both as
  `StepEffect(kind="characteristic", ...)`, so a floor clamp rendered
  `END -5, END -4` with nothing in the record saying which was which. The
  only disambiguating convention lived in a test helper, which treated any
  two adjacent same-subject `characteristic` effects as a clamp pair and
  could not tell one from two genuine independent reductions of the same
  characteristic — a real ambiguity under a career override, since nothing
  stops two of a table's class effects from choosing the same
  characteristic. FR-030a requires the parts be separately addressable and
  the check made from the record's own shape. The called-for half now
  carries its own kind, `characteristic-called-for`, added to `StepEffect`'s
  closed set. `history` is a field of `Character`, and a floor-clamped
  reduction's called-for effect now carries a different `kind` string than
  before, so every character whose walk reaches a floor clamp changes from
  this version forward (FR-030a, FR-056b, T165).
- **A mishap that forfeits a career's benefits still took its rank-derived
  bonus rolls.** `run_term_loop` already zeroed `benefit_rolls` for a
  mishap's `forfeit-career-benefits` effect (T145), but `muster_out_service`
  computed `rolls = benefit_rolls + rank_bonus` regardless, so a character
  dishonorably discharged or imprisoned at a high rank still took one to
  three mustering-out rolls from that service —
  `CareerService.benefit_rolls` recorded 0 while rolls were actually taken.
  `muster_out_service` now takes the forfeiture flag and skips every roll,
  rank-derived or not, when it is set. A forfeited service at a rank the
  mustering-out rank benefits cover now draws none of the dice it used to
  for its bonus rolls, changing every character whose walk reaches that
  branch from this version forward (FR-016, FR-019, FR-056b, T168).
- **An uncommissioned character in a promotion-offering career never rolled
  the advancement throw at all.** `run_term_loop` gated the whole throw on
  `ranks_above`, a precondition no data declares — FR-008 conditions the
  step on the career offering the throw, not on a higher rank existing to
  move to. Every shipped entry ladder other than Navy's (T155) declares a
  single rank 0, so a character on one of them was denied both the throw
  and the skill roll FR-009 grants on a successful one. The throw is now
  attempted whenever `throws.promotion` is declared; only the rank move
  and its bonus stay conditioned on a higher rank existing. Every character
  in a promotion-offering career now draws the advancement dice at least
  once per uncommissioned term where it used to draw nothing, changing
  every character whose walk reaches that branch from this version forward
  (FR-008, FR-009, FR-056b, T169).
- **A dice notation's own flat modifier (`"2d6+1"`) is now honored, on every
  throw and table read the lifepath walk makes.** `_dice` used to unpack
  `parse_notation`'s `(count, sides, modifier)` and discard the modifier,
  so all sixteen call sites — the five career throws, the characteristics
  roll, the draft, mishaps, injuries, continuation, the medical crisis, the
  medical tiers, aging, and the three mustering-out reads — compared
  `sum(faces)` against a target or used it to index a table while ignoring
  what the file asked for; `task.roll`'s identical notation was already
  honored and itemized. No shipped file carries a modifier, so no packaged
  seed's output changes, but any override that sets one now takes effect,
  itemized in the recorded step's modifiers the way `task.roll`'s is
  (FR-056b, SC-013, T178).
- **The `characteristics`, `background-skills`, `skill-roll`, `benefit`,
  `basic-training`, and mishap/injury reduction steps now carry the throw
  that produced them.** All six kinds rolled dice and recorded
  `throw=None` regardless — 35 of a character's 54 draws went
  unrecorded. Each now carries a `StepThrow` (faces, target `0`, success
  `true`, per the table-reading-roll convention `data-model.md` already
  states) whenever it actually rolled; `basic-training` still records
  `throw=None` when a first career's whole service table is granted
  outright, since nothing was rolled for that. This changes the emitted
  `Character` and `--json` document — every one of these steps' `throw`
  field goes from `null` to populated — but not what a seed's
  characteristics, skills, funds, or anything else on the sheet come out
  to: the dice drawn and their order are unchanged, only whether the
  record keeps them (FR-030, FR-030a, `data-model.md:155`, T183).
- **`as_dict(Character)` (and therefore `--json`) dropped
  `characteristic_symbols`.** T159 added the field so a `--json` consumer
  reads the profile through the rules that generated the character rather
  than the packaged table, and `as_dict` was never updated to emit it —
  the only field-versus-emitted mismatch across all six produced types.
  It now appears right after `characteristics`. Every existing `--json`
  consumer parsing the document positionally rather than by key sees an
  extra field where it did not before (FR-050, FR-029, T159, T184).
- **`CareerService.benefit_rolls` understated the rolls a service actually
  took, by 1 to 3.** `run_term_loop` set the field from the term-derived
  count alone, while `muster_out_service` separately added the
  rank-derived bonus (`mustering-out.rank-benefits`) before rolling —
  T155's rank-5 enlisted ladder made this ordinary on Navy rather than
  confined to commissioned officers. `muster_out_service` now returns the
  count it actually rolled, and `run()` records that on the
  `CareerService` instead. A consumer reading `benefit_rolls` — the field
  `data-model.md` and `contracts/json-output.md` both publish — now sees
  the true count for every character generated from this version forward
  (FR-016, SC-004, `data-model.md:99`, T188).
- **A draft or fallback collision with an already-entered career was
  substituted silently, and then, once given a step of its own, that step
  named the wrong career.** When the Draft table or the always-available
  fallback names a career the character already entered and cannot
  re-enter, `enter_career` falls through to a re-enterable career instead
  — correct per FR-015, but the substitution left no trace: `entered_by`
  stayed `"drafted"`, and the `"draft"` step still named the career the
  walk never actually entered, with nothing between it and
  `"career-entered"` explaining the gap. A new requirement, FR-015a,
  states the rule explicitly, and the substitution now appends its own
  `"career-selected"` step between the `"draft"` step and the
  `"career-entered"` step it precedes — naming the *substitute* the walk
  actually entered, not the collided-with career the `"draft"` step
  already names, which a first attempt recorded instead and which only
  restated what came before it, leaving the substitute itself still
  unexplained (163 of 5,000 sampled characters). Reachable only when a
  character re-enters a career already served through the draft or the
  fallback route specifically, which every character's history from this
  version forward may now carry one more, correctly-named, step for
  (FR-015a, FR-030, FR-030a, T189, T201).
- **The retired cash modifier applied by the current service's own terms,
  not by whether the character had ever qualified for a pension.** FR-017
  gives the modifier the same character-wide scope FR-016 already gives
  the cash-roll cap (T147): it applies once the character has qualified,
  in any single career, not only when the service currently mustering out
  does. A character who qualified in an earlier career and mustered out
  of a later, shorter one took an undiscounted cash roll — 90 of 20,000
  sampled characters. `_Walk` now remembers whether the character has
  ever qualified and reads that instead. A career service reached after
  an earlier pension-qualifying one now applies the modifier to its cash
  rolls where it previously did not, changing the funds (and, through
  `mustering-out.cash`'s row spacing, which item or amount) every such
  character's walk produces from this version forward (FR-017, FR-016,
  FR-056b, T202).
- **A later career's basic training discarded a drawn characteristic
  adjustment after rolling for it.** `basic_training`'s later-career
  branch filtered every drawn entry down to skill references, so a
  service-table entry like `"END +1"` was rolled, selected, and then
  applied nowhere — a die thrown, an entry chosen, and nothing granted,
  leaving a `basic-training` step that could not be replayed from its own
  record. The later-career draw now applies whatever it draws through the
  same `_apply_entry` `_roll_skills` already uses; the first-career branch,
  which grants every entry of the table regardless of what it drew, keeps
  its own filter. No shipped career's service table holds a non-skill
  entry, so no packaged seed's output changes; an override whose service
  table does now applies it, changing that career's basic-training step
  from this version forward (FR-007a, FR-030a, T200).
- **The characteristics roll — the sixteenth `_dice` call site T178 missed
  — applied its own dice-notation modifier to every rolled score but
  recorded none of it.** The `characteristics` step's single `StepThrow`
  (one throw across all six per-characteristic rolls) carried
  `modifiers=()` regardless, so `total` (`sum(faces)`) fell short of
  `contracts/data-files.md`'s own stated remedy for a modifier here: added
  to the total and itemized in the recorded step, the way every other
  dice-notation field's now is. No shipped file sets `[characteristics].roll`
  to anything but a bare `2d6`, so no packaged seed's output changes; an
  override that sets a modifier now sees it in the record it already saw
  applied to the sheet (FR-030a, FR-030, Constitution V, `contracts/data-files.md:251`, T198).
- **The aging total's `terms-served` subtraction and a medical bill's rank
  addition both changed `total` while recording no modifier for either.**
  `contracts/data-files.md` declares `modifier = "terms-served"` and
  `rank-dm` as modifiers of the total in exactly those words, and
  `contracts/json-output.md` states the invariant `total == sum(faces)`
  plus the modifier values as one a contract test asserts — but that test
  ran only against a hand-constructed fixture, never a generated
  character, so the gap was latent: 437 steps in 201 of 1,000 sampled
  characters violated it. Both are now itemized as `Modifier`s the same
  way every other throw's are — `"Terms served"` and `"Rank N"` — with no
  change to either `total`, since both already carried the correct
  numeric value; only `modifiers`, which was empty, now is not. `history`
  is a field of `Character`, so every character whose walk reaches aging
  past its first term, or a medical bill charged at a nonzero rank, now
  carries a different `aging` or `medical-bills` step from this version
  forward (FR-030a, FR-030, `contracts/json-output.md:187`, T196).
- **A mustering-out roll's cash-or-material decision was merged into the
  table throw's own record, and the row-choosing DM was applied with
  nothing itemized for it.** The FR-016 cash-choice die's face was
  concatenated onto the mustering-out table die's `faces`, describing one
  throw that was never actually made — `faces=(4, 6)` for what was really
  two separate throws — while `mustering-out.retired-cash-dm` and
  `.material-rank-dm` were folded into `total` with neither recorded in
  `modifiers`, so a consumer holding `faces`, `modifiers`, and `total`
  could not reach the amount the effect reports. The cash-choice decision
  is now its own `"cash-choice"` step (new in the closed step-kind set),
  `throw = None` when the character-wide cash-roll cap already forces
  material without a die; the DM that follows is itemized as `"Retired"`
  or `"Rank N"`. No dice are added, removed, or reordered — every draw a
  seed already made still happens in the same sequence — but `history` is
  a field of `Character`, and every mustering-out roll now produces a
  different, more granular set of steps than before, so every character
  whose walk takes at least one such roll changes from this version
  forward (FR-030a, FR-016, FR-017, `contracts/cli.md:196`, T197).
- **The die that chose a career recorded `throw = None`, indistinguishable
  from the throwless draft-collision substitution step beside it.**
  `_select_career` throws `self.roller.die(len(available))` for every
  career entry attempt, and the `"career-selected"` step naming its result
  carried no record of it — "why did this person end up a Drifter" was
  unanswerable from the record, and a consumer counting selection attempts
  could not tell an ordinary selection from a substitution by shape, only
  by adjacency to the preceding `"draft"` step, which FR-030a's "separately
  addressable parts" rules out. The step now carries the die as a
  table-reading throw; the substitution, chosen deterministically rather
  than drawn, still carries none. No dice are added, removed, or
  reordered, but `history` is a field of `Character`, and every
  `"career-selected"` step from an ordinary selection now carries a throw
  where it previously carried none (FR-030, FR-030a, FR-015a, T207).
- **The dice that chose which characteristics an aging effect reduced went
  unrecorded.** `_apply_aging_if_due` draws a selection die per
  characteristic a row's class effect chooses, the same selection
  `_apply_class_effect` performs for mishaps and injuries — but that
  sibling site records its selection dice and this one did not, so the
  same recorded row-lookup throw could map to more than one outcome across
  a sampled population (the worst observed, eight). The row-lookup
  throw's own `total` is the modified value the row was read against, so
  the selection dice cannot simply be appended to its `faces` without
  breaking `total == sum(faces)` plus the modifiers; each class effect a
  row declares now gets its own `"aging"` step instead, immediately after
  the row-lookup step, carrying the selection dice as its own throw and
  the characteristic changes that effect produced. No dice are added,
  removed, or reordered, but `history` is a field of `Character`, and an
  `"aging"` step that reduces anything now produces a different, more
  granular set of steps than before, so every character whose walk
  reaches such a reduction changes from this version forward (FR-030,
  FR-030a, `contracts/json-output.md:187`, T208).
- **The package now ships all twenty-four SRD careers, not eight, and a seed
  from an earlier version is not reproducible against this one.** Three
  independent causes each reorder or resize the draws a walk makes, and all
  three land together: the career pool a random selection or a draft throw
  can land on grows from eight entries to twenty-four (FR-001, FR-026); the
  background-skills table's three lists are corrected to the source's actual
  rows, including repeats a uniform draw had flattened away (FR-014a); and a
  bare skill grant that resolves through more than one cascade level now
  costs one die per level instead of one die total (FR-012). No seed's
  output from a prior release is preserved — reproducing the previous
  eight-career pool requires shipping it explicitly as a `--rules-data`
  override, the same mechanism any other house rule uses.
- **The career schema rises to `schema-version = 4`, and the skills registry
  schema rises to `schema-version = 2`.** A career file declaring the old
  version is rejected on its header with no migration path: `ranks[].title`
  is now optional (a rank whose source row prints no title omits the key
  rather than inventing one, FR-007/FR-008); `mustering-out.benefits`
  entries admit a dice-quantity form (`"1d6 Ship Share"`, FR-011); and
  `throws.re-enlistment` no longer admits a `characteristic`, since no
  source career's re-enlistment throw ever used one. The skills registry
  admits a specialty that is itself a cascade with specialties of its own
  (`Vehicle` naming `Aircraft` and `Watercraft`, each resolving further,
  FR-012).
- **Three careers are renamed to their long source-published forms.** The
  working names `aerospace-defense`, `maritime-defense`, and
  `surface-defense` become `aerospace-system-defense`,
  `maritime-system-defense`, and `surface-system-defense` (composition keys
  and file basenames both), matching the source's own career-descriptions
  list rather than an abbreviated in-house label (FR-005). A house rule that
  overrides one of these three files by its old basename now composes as an
  addition, not a replacement, until it is renamed to match.
- **Scout's and Drifter's data is corrected against the source.** Scout's
  qualification and re-enlistment targets, its rank 0 title and grant, its
  cash table, and its service skills were wrong; Drifter's qualification
  target, its advanced-education gate, its cash table, its rank titles
  (the source prints none, on any rank), and several skill names were
  wrong. Both careers' mustering-out material tables drop a padded seventh
  row the source never prints, in favor of the coverage rule added
  alongside them (FR-020, FR-021) rather than a fixed seven-row table.

  **Not a bug, if you see it**: a sheet may now show a skill twice under
  different names — `Life Sciences-0` beside `Sciences (Life Sciences)-1`,
  for instance — because the source lists some names both as a bare skill
  and as a specialty of a cascade skill, and the two are recorded as
  distinct entries rather than merged (FR-016a). The background-skills
  table's education list is what makes this routine rather than rare.
- **Navy's rank ladders are corrected against the source; Hunter's
  advanced-education row 5 is corrected too.** The convergence pass behind
  `verification/navy.md` and `verification/hunter.md` (T095, T096) read the
  source's raw HTML directly rather than through a summarizing fetch tool,
  which resolved two prior open questions. Navy: the source prints one rank
  column, 0-6, not the two overlapping columns `navy.toml` (002's reference
  career) had carried since an earlier feature (T155) added them to
  exercise engine paths — an invented rank 5, "Petty Officer", on the entry
  ladder, and a specified specialty, "Melee Combat (Slashing Weapons)", on
  the officer ladder's Midshipman grant. Both are removed; the officer
  ladder now reproduces the source's single column at ranks 1-6 exactly,
  the same entry-rank-0-only split every other two-ladder career in the
  package uses. As a result, no shipped career's uncommissioned rank now
  exceeds 0 and no shipped rank bonus specifies a specialty — both engine
  paths move from shipped-data coverage to unit fixtures
  (`test_generator.py::TestPromotionOffTheEntryLadder`,
  `test_reference_career.py::test_no_shipped_career_specifies_a_specialty_on_a_rank_bonus`).
  Hunter: advanced-education row 5 is `Tactics`, not `Animals` as committed
  (`hunter.toml` had `Animals` at both rows 5 and 6); row 6 is confirmed
  `Animals`, settling a previously-unresolved ambiguity without changing it.
  Any character a seed produces that serves as an uncommissioned Navy
  rating, is promoted into Navy's officer ladder, or draws Hunter's sixth
  advanced-education row changes from this version forward (FR-024,
  FR-056b).
- **Belter's material row 3 is corrected against the source.** A second
  convergence pass (T098) found `belter.toml` carried a repeated `INT +1`
  at material row 3 where `verification/belter.md` itself already recorded
  the source's printed value, `Weapon` — the artifact's "committed file"
  column had drifted from the file it was meant to describe. Read from the
  source's raw HTML directly, the same treatment T095/T096 used. Any
  character a seed produces that draws Belter's third material-benefit row
  changes from this version forward (FR-002, FR-024, FR-056b). The same
  pass (T099) found a Pirate artifact discrepancy in the other direction —
  `verification/pirate.md` had recorded rank 0's title as unprinted when
  the source prints "Crewman" and `pirate.toml` already carried it; only
  the artifact was corrected, so no Pirate seed's output changes.

### Added

- **Validated rules data loading.** `load_rules` and `validate_rules`
  discover every `.toml` file under `cetools/data/`, compose it with an
  optional override, and validate the whole set on every load: a data set
  loads only when all of it is well-formed, or refuses, naming every problem
  it finds in one run rather than the first. A file that is present but
  cannot be read is reported like any other problem, naming the file, and the
  remaining files are still checked rather than masked by it. A file rejected
  on its header — an unsupported `schema-version`, an unrecognized kind — is
  reported once and its contents left uninterpreted, and it is never then also
  reported absent, because it is sitting in the data set. A `schema-version`
  is typed before it is compared, so `true` and `1.0` are refused as the
  wrong type rather than passing the gate on Python's `True == 1`. A problem
  about a value's type names both types the way the data files spell them —
  `found a string; expected an integer` — and a problem concerning two files
  names both in what it found while keeping its file key singular, so
  grepping the report by filename finds every problem about that file.
  `RulesData` carries the loaded set; `ValidationReport` carries a report of
  what is wrong, if anything, and the two agree on every input.
- **The compact table notation.** `parse_entry` reads a career table cell in
  any of its four forms — a characteristic check, a characteristic
  adjustment, a skill grant, or a bare name — governed by the `EntryContext`
  the field it came from admits. It returns a `NotationProblem` rather than
  raising for a malformed entry or a form its context does not admit, so a
  caller can collect every problem in one pass, and that problem reports the
  entry exactly as written along with the forms admissible in the position it
  sits in, which is one form for a table's gate and two for a mustering-out
  benefits entry. A parenthesized specialty belongs to a skill or a benefit
  item, so one written on a characteristic — `INT (Foo) 4+` — is reported
  rather than quietly discarded; a specialty may end in a digit, so
  `Blade (Mark 2)` reads as the same skill and specialty its grant form
  `Blade (Mark 2) 1` does. The space before a specialty group is part of the
  grammar rather than decoration, so `Blade(Cutlass)` is reported as
  malformed rather than read as `Blade (Cutlass)`, and a benefit item
  resolves under the name as written, so `Weapon  (Blade)` is not silently
  collapsed into the registry's `Weapon (Blade)`.
- **The reference career, and the registries that give it meaning.** Three
  shipped registries (`CharacteristicRegistry`, `SkillRegistry`,
  `BenefitRegistry`) resolve the names a career file's entries use, the skill
  registry reporting which of the four `SkillResolution` outcomes a reference
  produces. A name no registry contains is reported with the registry it was
  checked against, so an author knows which file to correct, and a skill
  registry entry that spells a specialty into its own name — `"Gun Combat
  (Slug Rifle)"` — is refused rather than admitted as an entry no career
  could ever reference.
  `CareerDefinition` and its parts (`Throw`, `SkillTable`,
  `RankLadder`, `Rank`, `MusteringOut`) are the schema a career file
  validates against.
  The Navy ships as the reference career, exercising every element of that
  schema.
- **House rules without forking code.** `load_rules(override)` and
  `validate_rules(override)` accept a directory or a single file, composed
  over the packaged data set by basename: a file that matches a packaged
  name replaces it, one that does not is an addition, and everything the
  override does not touch still comes from the packaged data. A location that
  does not exist, or that is neither a file nor a directory, is refused as a
  usage error naming it, never quietly composed as the packaged set, and a
  directory within it that cannot be listed is reported the way an unreadable
  file is rather than passed over. Symlinked directories are followed, so a
  rule set assembled out of links composes. Files and directories whose names
  begin with a dot are passed over entirely when they are *found* under an
  override location, so pointing the tool at a git checkout reports nothing
  from `.git/` — and a `.toml` beneath such a directory does not quietly take
  effect either. A dot-prefixed path named on the command line is not passed
  over, because the author wrote it: `cetools validate ./.navy.toml` composes
  that file, rather than reporting success having done nothing. A file with
  the wrong extension is reported as ignored under its path within the
  override, so two files sharing a basename are both named. A FIFO or a
  symlink to a device node found within an override is reported rather than
  read, since either would otherwise hang the run forever with no output and
  no exit status. An empty override location is refused as a usage error too,
  rather than silently composing the current working directory, which is
  what the empty string names as a path.
- **Provenance.** Every `CheckResult` and `ValidationReport` carries a
  `Provenance`: the installed package version, and, for an overridden load,
  each file's disposition and a reproducible SHA-256 fingerprint over its
  raw bytes.
- **`cetools validate`.** Reports every problem in the packaged data set, or
  an override composed over it, with exit codes 0 (valid), 1 (invalid), and
  2 (usage error), in both text and `--json` output.
- **`--rules-data PATH` on `cetools check`.** Composes an override location
  over the packaged data set exactly as a library load does; the rendered
  and JSON output both gain a `Rules:` / `provenance` block reporting what
  produced the result.
- **Seeded dice rolling.** `Roller` wraps a seeded generator; `throw`,
  `throw_dice`, and `parse_notation` handle `NdN`, `NdN+M`, and `NdN-M`
  notation, returning a frozen `ThrowResult` carrying the individual dice,
  the modifier, the total, and the seed.
- **`d66`.** The two-digit table die, read as tens and units rather than
  summed, for the SRD's 36-entry tables.
- **2D6 task resolution.** `check` resolves a task against a target number,
  applying difficulty, characteristic, and skill modifiers plus any number
  of ad-hoc situational DMs, and returns a `CheckResult` with every modifier
  itemized and named. An omitted characteristic contributes no modifier
  rather than a silent zero; skill level 0 means trained-but-unpracticed and
  is distinct from no training at all, which takes the unskilled DM.
- **SRD parameters as data.** Target number, difficulty DMs, characteristic
  DM bands, and the unskilled DM live in `src/cetools/data/tasks.toml` and
  are read at runtime through `load_rules().task_parameters`. The engine
  hard-codes no table content, so house rules are a data edit.
- **`cetools roll` and `cetools check`.** Both accept `--seed`, print the
  seed they used (freshly generated if none was given), and accept `--json`
  for machine-readable output. `cetools --version` reports the version.
- **Rendering.** `as_text`, `as_dict`, and `as_json` render any result type
  for display or for machines, and are available to library consumers, not
  just the CLI.
- **Error hierarchy.** `CetoolsError` with `DiceError`, `RulesDataError`,
  and `TaskError` beneath it. The library raises; it never prints and never
  exits. The CLI is what turns an error into a stderr message and a non-zero
  exit code.
- **Reproducibility guarantee.** The same seed and the same package version
  produce the same result, verified by a dedicated guard suite alongside
  unit, integration, contract, property, and golden-output tests.
- **Dual licensing.** `LICENSE` (GPL-3.0) covers the code, declared in the
  package metadata as the SPDX expression `GPL-3.0-only` so installers and
  indexes can read it; `LICENSE-OGL.txt` (OGL 1.0a, with the SRD's Section 15
  chain verbatim) covers every `.toml` file under `src/cetools/data/` — which
  ships as `cetools/data/` in an installed package, and the notice names both
  paths — as Open Game Content. Both ship in every sdist and wheel, and the
  guard that checks the notice's coverage derives what must be covered from
  the files a distribution actually carries, keyed on the designation rather
  than on a directory prefix and an extension. The sdist's `include` patterns
  for `README.md` and `CHANGELOG.md` are anchored to the repository root:
  unanchored, they matched at any depth and picked up a vendored Spec Kit
  file the sdist was never meant to ship.
- **Project documentation.** `README.md` with installation and worked
  examples, and `CONTRIBUTING.md` covering the constitution, the spec-driven
  workflow, and the licensing rules.
- **`cetools npc`.** Generates a complete NPC from a seed by walking the
  source material's lifepath end to end: characteristics, background
  skills, career selection with qualification, the draft, and the
  always-available fallback, basic training, a term loop of survival,
  commission, advancement, skill acquisition (including the cascade rule
  for specialties), and aging, then mustering out with cash-or-material
  benefit rolls, a pension, and ordered debt settlement. The character is
  always alive, always named, and always internally consistent — there is
  no death path and nothing is discarded and re-rolled. `--seed` and
  `--name` behave as everywhere else in the tool; `--rules-data` composes
  an override exactly as `check` and `validate` do. The rolled name comes
  from a seed stream derived from the walk's own seed, which the walk's
  roller never touches, so supplying `--name` changes nothing else about
  the character a seed produces. `generate_character` and `generate_batch`
  (with `character_seed` for a batch position's seed) are reachable from the
  library without the command line; a batch's position 0 is the master seed
  itself, so `--seed X` and a batch of one from that seed are the same
  person. Prints the Universal Character Format — the source material's own
  sheet, tab separated, four lines with the benefit-items line omitted when
  the character holds none — to standard output, and the seed, version, and
  provenance to standard error, so a redirected sheet is exactly a sheet.
- **`cetools npc --full` and `--json`.** `--full` adds the outstanding debt,
  the pension, and the generation history to the sheet: one line per step,
  composed from the step's own kind, career, term, throw, and effects —
  never from a stored line of prose — so a surprising character is
  diagnosed from output rather than a debugger. `--json` emits the same
  information as a machine-readable document instead: the master seed, the
  provenance, and one entry per character, with every field present
  unconditionally and both the master and each character's own derived seed
  as strings. The two options combine without conflict; `--json` already
  carries everything, so `--full` changes nothing under it. `as_text`
  gained a keyword-only `full` flag, rejected by every registration that
  has no fuller form; `as_dict` and `as_json` now render `Character` and
  `CharacterBatch` as well.
- **`cetools npc --count`.** Generates several characters from one master
  seed: `--count N` produces `N` sheets from the same `--seed`, one blank
  line between consecutive ones and nothing else, so a batch of one is
  byte-identical to the single character of that seed and quoting the
  master seed back reproduces the whole table. `--count` below 1 is a
  usage error naming `--count`; `--name` together with `--count` above 1
  is a usage error naming both, since a personal name names one character
  and applying it to the rest, or discarding it, would each silently drop
  part of what was asked for. `generate_batch` and `character_seed` were
  already reachable from the library; this wires the option through to
  them.
- **`chargen-parameters.toml` gains `mustering-out.per-term`, rising to
  `schema-version = 2`.** How many benefit rolls each net term served
  earns was an implicit `1` held in `generator.py`, unlike the rank
  thresholds it is paired with in `mustering-out.rank-benefits`, which
  already read from data. Shipped at `1`, matching the prior behavior, so
  no packaged seed's output changes; an override written against
  `schema-version = 1` must add the key to keep validating (FR-038, T179).
- **Tag-triggered release publishing.** Pushing `v<declared version>`
  publishes a release on the project's public source repository: a
  preflight (`scripts/release-preflight.sh`) refuses a tag that disagrees
  with `project.version`, a changelog section that is missing, marked
  `(unreleased)`, or empty, and a version that is already published (failing
  closed if the answer cannot be determined); only then does the full test
  suite run at the tagged commit, both distribution formats build, a
  combined `SHA256SUMS.txt` and a signed provenance attestation are produced
  for each artifact, and the release is published with the changelog
  section verbatim followed by a fixed attribution footer
  (`.github/release-footer.md`) as its notes. Nothing is published unless
  every check and the full suite pass. `scripts/changelog-section.sh`
  extracts a version's changelog body for reuse by both the preflight and
  the workflow. Neither script ships; `scripts/` is release tooling, not
  part of a distribution (FR-001 through FR-010, FR-021, FR-025).
- **README installation points at the published artifact.** `uv add
  cetools` named a package index that has never carried this package. The
  primary instruction is now `uv tool install` against the released wheel's
  download URL, with an alternative that installs from the tagged source
  (`uv tool install git+...@v<version>`) and a third for a project that
  depends on `cetools` as a library rather than installing the command
  (`uv add <the same wheel URL>`). `CONTRIBUTING.md`'s remaining references
  to a PyPI description now name the public release page and the built
  package's description instead (FR-016 through FR-018, FR-024, FR-026).
- **Package metadata a published artifact is expected to carry.** Both
  distributions now declare `keywords`, `classifiers` (including
  `Typing :: Typed`, with no redundant `License ::` classifier), `authors`
  (name only), and a `[project.urls]` table naming the repository, the
  changelog, and the issue tracker. An empty `src/cetools/py.typed` ships in
  both formats as the PEP 561 marker. A packaging guard verifies the marker
  and the descriptive fields in the built wheel's `METADATA` and the
  sdist's `PKG-INFO`, and the Python trove classifiers are held in step
  with `requires-python` and `ci.yaml`'s matrix by the guard that already
  exists for that drift (FR-019, FR-020).
- **The documented-version drift guard now covers the install command, in
  both of the version's spellings.** The guard's single pattern group split
  into a reported (normalized) group and a declared (padded) group compared
  against different expected values: the wheel filename in the install
  command joins the reported group, and the `releases/download/v.../` tag
  segment and the `@v...` source-install ref join a new declared group
  compared against `project.version`. A stale value fails naming the file
  and the value, and a value normalized before comparing — the padded form
  in the filename position or the unpadded form in the tag position — fails
  too, rather than passing on a coincidental match (FR-011, FR-012).

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
