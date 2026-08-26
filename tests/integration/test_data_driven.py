"""SC-011: a behavior change with no code edit, demonstrated for a career
throw, a skill table entry, a rank bonus, and a registry entry. The registry
case is the sharpest: removing a skill name from the registry must make
every career reference to it fail, which is what proves the registry is
what gives names meaning (FR-013).
"""

from pathlib import Path

import pytest

from cetools.dice import Roller, parse_notation
from cetools.errors import RulesDataError
from cetools.generator import _Walk, generate_character
from cetools.render import as_text
from cetools.rules import load_rules, validate_rules

_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"
NAVY = (_DATA / "careers" / "navy.toml").read_text(encoding="utf-8")
SKILLS = (_DATA / "registries" / "skills.toml").read_text(encoding="utf-8")
CHARACTERISTICS = (_DATA / "registries" / "characteristics.toml").read_text(encoding="utf-8")
DRAFT = (_DATA / "chargen" / "draft.toml").read_text(encoding="utf-8")
AGING = (_DATA / "chargen" / "aging.toml").read_text(encoding="utf-8")
MISHAPS = (_DATA / "chargen" / "mishaps.toml").read_text(encoding="utf-8")
CHARGEN_PARAMETERS = (_DATA / "chargen" / "chargen-parameters.toml").read_text(encoding="utf-8")


def _first_seed_matching(rules, predicate, limit=500):
    """The first seed under `limit` whose generated character satisfies
    `predicate`, so SC-013's demonstrations can force the walk down a
    specific path without hand-deriving a seed's draws.
    """
    for seed in range(limit):
        character = generate_character(Roller(seed), rules)
        if predicate(character):
            return seed, character
    raise AssertionError(f"no seed under {limit} satisfies the predicate")


_PROMOTION_BLOCK = '[throws.promotion]\ncharacteristic = "EDU"\ntarget = 6\n'
_TACTICS_ENTRY = '"Tactics" = []\n'


def test_a_career_throw_takes_effect_with_no_code_edit(tmp_path):
    assert _PROMOTION_BLOCK in NAVY
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace(_PROMOTION_BLOCK, _PROMOTION_BLOCK.replace("target = 6", "target = 11"), 1),
        encoding="utf-8",
    )
    rules = load_rules(override)
    assert rules.careers["navy"].throws["promotion"].target == 11


def test_a_skill_table_entry_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(NAVY.replace('"Comms"', '"Advocate"', 1), encoding="utf-8")
    rules = load_rules(override)
    entries = rules.careers["navy"].tables["service"].entries
    assert entries[0].name == "Advocate"


def test_a_rank_bonus_takes_effect_with_no_code_edit(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace('bonus = "Zero-G 1"', 'bonus = "Zero-G 3"', 1), encoding="utf-8"
    )
    rules = load_rules(override)
    (enlisted,) = (ladder for ladder in rules.careers["navy"].ladders if ladder.name == "enlisted")
    (starman,) = (rank for rank in enlisted.ranks if rank.title == "Starman")
    assert starman.bonus.level == 3


def test_removing_a_registry_entry_breaks_every_career_reference_to_it(tmp_path):
    assert _TACTICS_ENTRY in SKILLS
    override = tmp_path / "skills.toml"
    override.write_text(SKILLS.replace(_TACTICS_ENTRY, "", 1), encoding="utf-8")

    report = validate_rules(tmp_path)

    assert not report.valid
    # Scoped to navy.toml: the packaged set now ships seven other careers
    # (003-npc-generator), several of which also name Tactics, and this test
    # demonstrates the rule against the one reference career rather than
    # against the whole set.
    tactics_locations = {
        p.location for p in report.problems if p.file == "navy.toml" and "Tactics" in p.found
    }
    assert tactics_locations == {
        "tables.advanced-education.entries[5]",
        "ladders[1].ranks[2].bonus",
    }


def test_removing_a_characteristic_from_the_registry_breaks_every_career_reference_to_it(
    tmp_path,
):
    # The skills case above is SC-011's "sharpest" registry demonstration but
    # proves only the skills registry; a characteristic code hard-coded into
    # `CharacteristicRegistry.__contains__` as a fallback would pass every
    # other test in the suite while making this one requirement — that a
    # characteristic is known from data, not from the parsing code (FR-012,
    # Constitution V) — false. One problem per characteristic-bearing
    # position in the shipped career: a throw's characteristic, a skill
    # table's characteristic adjustment entry, a table's gate, and a
    # mustering-out benefit's characteristic adjustment.
    edu_block = '[characteristics.EDU]\nlabel = "Education"\nclass = "mental"\n\n'
    assert edu_block in CHARACTERISTICS
    override = tmp_path / "characteristics.toml"
    override.write_text(CHARACTERISTICS.replace(edu_block, "", 1), encoding="utf-8")

    report = validate_rules(tmp_path)

    assert not report.valid
    # Scoped to navy.toml for the same reason as the skills case above: the
    # packaged set now ships other careers that also reference EDU.
    edu_locations = {
        p.location for p in report.problems if p.file == "navy.toml" and p.found == "EDU"
    }
    assert edu_locations == {
        "throws.promotion.characteristic",
        "tables.personal.entries[4]",
        "tables.advanced-education.requires",
        "mustering-out.benefits[1]",
    }


# --- SC-013: a Draft table row, an aging table entry, a Survival Mishaps ---
# entry, a career's medical tier, and the term cap, each changed in an
# override with no code edit.


def test_a_draft_table_row_takes_effect_with_no_code_edit(tmp_path):
    packaged = load_rules()
    seed, baseline = _first_seed_matching(
        packaged, lambda c: any(step.kind == "draft" for step in c.history)
    )
    draft_step = next(step for step in baseline.history if step.kind == "draft")
    original_name = draft_step.selected
    replacement = next(name for name in packaged.draft.careers if name != original_name)

    override = tmp_path / "draft.toml"
    override.write_text(
        DRAFT.replace(f'"{original_name}"', f'"{replacement}"', 1), encoding="utf-8"
    )
    rules = load_rules(override)
    assert rules.draft.careers != packaged.draft.careers

    overridden = generate_character(Roller(seed), rules)
    new_draft_step = next(step for step in overridden.history if step.kind == "draft")
    assert new_draft_step.selected == replacement
    assert new_draft_step.selected != original_name


def test_an_aging_table_entry_takes_effect_with_no_code_edit(tmp_path):
    packaged = load_rules()
    seed, baseline = _first_seed_matching(
        packaged, lambda c: any(step.kind == "aging" and step.effects for step in c.history)
    )

    # Every amount in the table made drastically more severe, so whichever
    # row this seed's modified roll lands on, the row it reads has changed.
    overridden_text = AGING.replace("amount = -1", "amount = -10").replace(
        "amount = -2", "amount = -20"
    )
    override = tmp_path / "aging.toml"
    override.write_text(overridden_text, encoding="utf-8")
    rules = load_rules(override)

    overridden = generate_character(Roller(seed), rules)
    baseline_step = next(
        step for step in baseline.history if step.kind == "aging" and step.effects
    )
    overridden_step = next(
        step for step in overridden.history if step.kind == "aging" and step.effects
    )
    assert overridden_step.effects != baseline_step.effects


def test_a_survival_mishaps_entry_takes_effect_with_no_code_edit(tmp_path):
    packaged = load_rules()
    seed, baseline = _first_seed_matching(
        packaged,
        lambda c: any(step.kind == "mishap" and step.throw is not None for step in c.history),
    )
    mishap_step = next(
        step for step in baseline.history if step.kind == "mishap" and step.throw is not None
    )
    original_description = mishap_step.selected
    new_description = f"{original_description} (house rule)"

    override = tmp_path / "mishaps.toml"
    override.write_text(
        MISHAPS.replace(f'"{original_description}"', f'"{new_description}"', 1),
        encoding="utf-8",
    )
    rules = load_rules(override)

    overridden = generate_character(Roller(seed), rules)
    overridden_step = next(
        step for step in overridden.history if step.kind == "mishap" and step.throw is not None
    )
    assert overridden_step.selected == new_description
    assert overridden_step.selected != original_description


def test_a_careers_medical_tier_takes_effect_with_no_code_edit(tmp_path):
    assert 'medical-tier = "service"' in NAVY
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace('medical-tier = "service"', 'medical-tier = "professional"', 1),
        encoding="utf-8",
    )
    rules = load_rules(override)
    assert rules.careers["navy"].medical_tier == "professional"
    assert (
        rules.medical_tiers.tiers[rules.careers["navy"].medical_tier]
        != rules.medical_tiers.tiers["service"]
    )


def test_a_careers_medical_tier_changes_what_the_generator_actually_charges(tmp_path):
    # T173: the case above proves only that the *loader* reports the
    # override; a generator that ignored `career.medical_tier` and
    # hard-coded a tier would still pass it, and would still pass SC-008's
    # coverage check too, since that one reads the tier off the career
    # rather than off what was actually charged. This one generates a
    # character and compares the bill itself.
    #
    # A Navy medical bill throwing a total of 7 makes the two tiers bill
    # differently: the "service" tier pays 75% at that total (target 4),
    # the "fringe" tier pays 0% (target 8 is the first rung it clears).
    # The override only changes `medical-tier`, not any table or throw, so
    # it consumes the same dice as the packaged file and a seed found
    # under one reproduces the same throw under the other.
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace('medical-tier = "service"', 'medical-tier = "fringe"', 1),
        encoding="utf-8",
    )
    packaged = load_rules()
    overridden = load_rules(override)

    def _has_navy_medical_bill_of_seven(character):
        return any(
            s.kind == "medical-bills" and s.career == "Navy" and s.throw.total == 7
            for s in character.history
        )

    seed, baseline = _first_seed_matching(packaged, _has_navy_medical_bill_of_seven, limit=20000)
    changed = generate_character(Roller(seed), overridden)

    baseline_bill = next(s for s in baseline.history if s.kind == "medical-bills")
    changed_bill = next(s for s in changed.history if s.kind == "medical-bills")
    assert baseline_bill.throw.total == changed_bill.throw.total == 7

    baseline_owed = next(e.amount for e in baseline_bill.effects if e.kind == "debt")
    changed_owed = next(e.amount for e in changed_bill.effects if e.kind == "debt")
    assert baseline_owed != changed_owed


def test_the_term_cap_takes_effect_with_no_code_edit(tmp_path):
    assert "cap = 7" in CHARGEN_PARAMETERS
    packaged = load_rules()
    seed, baseline = _first_seed_matching(
        packaged, lambda c: sum(service.terms for service in c.careers) > 1
    )

    override = tmp_path / "chargen-parameters.toml"
    override.write_text(CHARGEN_PARAMETERS.replace("cap = 7", "cap = 1", 1), encoding="utf-8")
    rules = load_rules(override)
    assert rules.chargen.terms_cap == 1

    overridden = generate_character(Roller(seed), rules)
    assert sum(service.terms for service in overridden.careers) == 1
    assert sum(service.terms for service in overridden.careers) < sum(
        service.terms for service in baseline.careers
    )


def test_a_pseudo_hex_symbol_takes_effect_with_no_code_edit(tmp_path):
    # T159: the rendered profile must trace to the rules that generated the
    # character, not to whatever `--rules-data` happens to leave packaged —
    # Constitution V promises swapping data changes output.
    assert '"A", "B"' in CHARACTERISTICS
    override = tmp_path / "characteristics.toml"
    override.write_text(CHARACTERISTICS.replace('"A", "B"', '"B", "A"', 1), encoding="utf-8")
    overridden_rules = load_rules(override)
    packaged_rules = load_rules()

    seed, character = _first_seed_matching(
        overridden_rules, lambda c: any(v in (10, 11) for v in c.characteristics.values())
    )

    packaged_profile = "".join(
        packaged_rules.characteristics.symbol(v) for v in character.characteristics.values()
    )
    overridden_profile = "".join(
        overridden_rules.characteristics.symbol(v) for v in character.characteristics.values()
    )
    assert packaged_profile != overridden_profile
    rendered_profile = as_text(character).split("\n")[0].split("\t")[1]
    assert rendered_profile == overridden_profile


def test_a_throws_dice_modifier_is_honored_and_itemized(tmp_path):
    # T178: `_dice` used to discard `parse_notation`'s modifier entirely, so
    # a `dice = "2d6+N"` override validated clean and changed nothing.
    block = '[throws.re-enlistment]\ntarget = 5\ndice = "2d6"'
    assert block in NAVY
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.replace(block, '[throws.re-enlistment]\ntarget = 5\ndice = "2d6+6"', 1),
        encoding="utf-8",
    )
    rules = load_rules(override)
    found = False
    for seed in range(300):
        character = generate_character(Roller(seed), rules)
        for step in character.history:
            if step.kind != "re-enlistment" or step.career != "Navy":
                continue
            found = True
            assert step.throw.total == sum(step.throw.faces) + 6
            assert any(m.label == "Roll (2d6+6)" and m.value == 6 for m in step.throw.modifiers)
            assert step.throw.success == (step.throw.total >= step.throw.target)
    assert found


def test_a_chargen_tables_roll_modifier_is_honored(tmp_path):
    # T178/T198: the modifier changes every rolled score correctly, but the
    # "characteristics" step's single `StepThrow` — covering all six
    # per-characteristic rolls — recorded none of their six modifiers, so
    # `total` (`sum(faces)`) fell short of the record's own promise that
    # `total == sum(faces) + the modifier values`
    # (contracts/json-output.md): the `+6` the file asked for reached the
    # sheet and not the record of how it got there.
    block = '[characteristics]\nroll = "2d6"'
    assert block in CHARGEN_PARAMETERS
    override = tmp_path / "chargen-parameters.toml"
    override.write_text(
        CHARGEN_PARAMETERS.replace(block, '[characteristics]\nroll = "2d6+1"', 1),
        encoding="utf-8",
    )
    rules = load_rules(override)
    packaged = load_rules()
    for seed in range(20):
        baseline = generate_character(Roller(seed), packaged)
        modified = generate_character(Roller(seed), rules)
        baseline_step = next(s for s in baseline.history if s.kind == "characteristics")
        modified_step = next(s for s in modified.history if s.kind == "characteristics")
        # Compare the "characteristics" step's own recorded effects, not the
        # final `characteristics` dict: everything after that first step —
        # DM-gated branching, benefits, aging — depends on the boosted
        # scores and legitimately diverges from the baseline walk from
        # there on.
        baseline_effects = {e.subject: e.amount for e in baseline_step.effects}
        modified_effects = {e.subject: e.amount for e in modified_step.effects}
        for code in packaged.characteristics.names:
            assert modified_effects[code] == baseline_effects[code] + 1
        assert modified_step.throw.total == sum(modified_step.throw.faces) + sum(
            m.value for m in modified_step.throw.modifiers
        )
        assert sum(m.value for m in modified_step.throw.modifiers) == len(
            packaged.characteristics.names
        )


def test_a_gap_in_the_aging_table_is_reported_not_silently_misassigned(tmp_path):
    # T186: `_apply_aging_if_due` (generator.py) matches a modified aging
    # total against `AgingRow.minimum` alone, discarding `maximum` — a
    # row's declared upper bound is parsed, validated, and unit-tested but
    # never honored when the table is actually read, so a gapped override
    # (which `contracts/data-files.md`'s own worked example already is)
    # silently sends a total in the gap to whichever row sorts highest
    # below it, rather than failing loudly.
    block = (
        '[[rows]]\nrange = "-3"\neffects = [{ class = "physical", count = 1, amount = -2 }]\n\n'
    )
    assert block in AGING
    override = tmp_path / "aging.toml"
    override.write_text(AGING.replace(block, "", 1), encoding="utf-8")
    rules = load_rules(override)

    found = False
    for seed in range(200):
        walk = _Walk(Roller(seed), rules)
        walk.characteristics = {code: 8 for code in rules.characteristics.names}
        walk.age = 40
        walk.total_terms_served = 7
        try:
            walk._apply_aging_if_due("Navy", 1)
        except RulesDataError:
            found = True
            break
    assert found


def _highest_matching_rank_row(rows, rank):
    best_rank = -1
    amount = 0
    for row in rows:
        if row.rank <= rank and row.rank > best_rank:
            best_rank = row.rank
            amount = row.amount
    return amount


def test_every_in_force_careers_mustering_out_tables_cover_the_full_dm_range():
    # T187 (originally): an engine-held clamp silently absorbed a roll that
    # overflowed a padded six-row table. FR-020/FR-021/D7 turned "every
    # table covers the full roll plus the maximum declared modifier" from a
    # fixed `== 7` pinned against the shipped eight into the computed bound
    # `cetools validate` itself now enforces over whatever careers are in
    # force — a bound that a career whose ladders stop at rank 0 satisfies
    # with fewer rows than one that reaches the rank-conditioned modifier
    # (data-model.md's mustering-out coverage rule).
    rules = load_rules()
    params = rules.chargen
    roll_count, roll_sides, roll_modifier = parse_notation(params.mustering_out_roll)
    max_total = roll_count * roll_sides + roll_modifier
    for stem, career in rules.careers.items():
        highest_rank = max(
            (rank_row.rank for ladder in career.ladders for rank_row in ladder.ranks), default=0
        )
        cash_required = max_total + params.mustering_out_retired_cash_dm
        material_required = max_total + _highest_matching_rank_row(
            params.mustering_out_material_rank_dm, highest_rank
        )
        assert len(career.mustering_out.cash) >= cash_required, stem
        assert len(career.mustering_out.benefits) >= material_required, stem


def test_an_excessive_mustering_out_modifier_is_reported_not_silently_clamped():
    # T187: `index = max(0, min(len(...) - 1, sum(faces) + dm - 1))` was an
    # engine-invented clamp stated in no requirement, contract, or data
    # file — the opposite of the treatment `contracts/data-files.md`
    # already gives every other positional table read (T181). The read is
    # `_table_row`'s, which reports an overflow rather than silently
    # absorbing it into the table's last row.
    #
    # The mustering-out coverage rule (FR-020, FR-021, D7) now catches an
    # excessive `retired-cash-dm` at validation, before an override built
    # this way could ever reach the walk — that is the point of the rule.
    # Demonstrated here directly against a `ChargenParameters` no loader
    # would hand back, to pin that `_table_row`'s own runtime guard still
    # stands as defense in depth underneath the validation rule.
    import dataclasses

    rules = load_rules()
    excessive_chargen = dataclasses.replace(
        rules.chargen, mustering_out_cash_choice_target=1, mustering_out_retired_cash_dm=100
    )
    rules = dataclasses.replace(rules, chargen=excessive_chargen)

    career = rules.careers["navy"]
    walk = _Walk(Roller("t187"), rules)
    with pytest.raises(RulesDataError):
        walk.muster_out_service(career, terms=6, ladder="enlisted", rank=0, benefit_rolls=1)


def test_the_mustering_out_per_term_rate_takes_effect_with_no_code_edit(tmp_path):
    # T179: the benefit-roll-per-term rate used to be an implicit `1` held
    # in engine code (`generator.py`'s `benefit_rolls = ... terms -
    # forfeited_terms`) rather than data, unlike the rank thresholds it is
    # paired with in `mustering-out.rank-benefits`.
    anchor = "retired-cash-dm = 1\nper-term = 1"
    assert anchor in CHARGEN_PARAMETERS
    override = tmp_path / "chargen-parameters.toml"
    override.write_text(
        CHARGEN_PARAMETERS.replace(anchor, "retired-cash-dm = 1\nper-term = 2", 1),
        encoding="utf-8",
    )
    packaged = load_rules()
    rules = load_rules(override)
    assert rules.chargen.mustering_out_per_term == 2

    seed, baseline = _first_seed_matching(
        packaged,
        # `benefit_rolls` is `terms * per-term` (which doubles) *plus* a
        # rank-derived bonus (which does not) — restricting to rank 0
        # everywhere keeps that bonus at zero, so a clean doubling is what
        # this scenario is actually demonstrating. A single career service
        # keeps the extra rolls the doubled rate consumes from shifting any
        # later career's own draws out from under it.
        lambda c: len(c.careers) == 1
        and any(service.benefit_rolls > 0 for service in c.careers)
        and all(service.rank == 0 for service in c.careers),
    )
    overridden = generate_character(Roller(seed), rules)
    assert len(overridden.careers) == len(baseline.careers)
    doubled_any = False
    for base_service, over_service in zip(baseline.careers, overridden.careers):
        assert base_service.career == over_service.career
        assert base_service.terms == over_service.terms
        assert over_service.benefit_rolls == base_service.benefit_rolls * 2
        if base_service.benefit_rolls:
            doubled_any = True
    assert doubled_any


def _first_seed_reaching(rules, limit):
    """The first seed under `limit` whose walk reaches the out-of-range
    positional read (T181): a die able to produce a total outside the
    array, which `contracts/data-files.md:291` calls "a data problem
    reported when it is read, not at load" rather than an `IndexError`
    escaping the walk uncaught.
    """
    for seed in range(limit):
        try:
            generate_character(Roller(seed), rules)
        except RulesDataError:
            return seed
        except IndexError:
            pytest.fail(f"seed {seed} raised IndexError instead of RulesDataError")
    pytest.fail(f"no seed under {limit} reached the out-of-range read")


def test_a_draft_roll_outside_the_table_is_reported_not_an_indexerror(tmp_path):
    text = DRAFT.replace('roll = "1d6"', 'roll = "2d6"', 1)
    assert text != DRAFT
    override = tmp_path / "draft.toml"
    override.write_text(text, encoding="utf-8")
    rules = load_rules(override)
    _first_seed_reaching(rules, limit=500)


def test_a_mishap_roll_outside_the_table_is_reported_not_an_indexerror(tmp_path):
    mishaps_text = MISHAPS.replace('roll = "1d6"', 'roll = "2d6"', 1)
    assert mishaps_text != MISHAPS
    params_text = CHARGEN_PARAMETERS.replace("natural-failure = 2", "natural-failure = 12", 1)
    assert params_text != CHARGEN_PARAMETERS
    # Forcing every survival throw to fail naturally reaches the mishap
    # row read on the very first term of every character, rather than
    # searching a large sample for one that happens to fail on its own.
    (tmp_path / "mishaps.toml").write_text(mishaps_text, encoding="utf-8")
    (tmp_path / "chargen-parameters.toml").write_text(params_text, encoding="utf-8")
    rules = load_rules(tmp_path)
    _first_seed_reaching(rules, limit=50)


def test_an_injury_roll_outside_the_table_is_reported_not_an_indexerror(tmp_path):
    mishaps_text = MISHAPS.replace('injury-roll = "1d6"', 'injury-roll = "2d6"', 1)
    assert mishaps_text != MISHAPS
    params_text = CHARGEN_PARAMETERS.replace("natural-failure = 2", "natural-failure = 12", 1)
    assert params_text != CHARGEN_PARAMETERS
    (tmp_path / "mishaps.toml").write_text(mishaps_text, encoding="utf-8")
    (tmp_path / "chargen-parameters.toml").write_text(params_text, encoding="utf-8")
    rules = load_rules(tmp_path)
    _first_seed_reaching(rules, limit=200)


# --- Phase 6d: the complete twenty-four-career roster (FR-026, FR-027, ---
# FR-028).

_TWENTY_FOUR_NAMES = {
    "Aerospace System Defense",
    "Agent",
    "Athlete",
    "Barbarian",
    "Belter",
    "Bureaucrat",
    "Colonist",
    "Diplomat",
    "Drifter",
    "Entertainer",
    "Hunter",
    "Marine",
    "Maritime System Defense",
    "Mercenary",
    "Merchant",
    "Navy",
    "Noble",
    "Physician",
    "Pirate",
    "Rogue",
    "Scientist",
    "Scout",
    "Surface System Defense",
    "Technician",
}

# research.md R1: the seven careers offering no commission, whose material
# table runs six rows (a dash where the source prints nothing for row 7) and
# whose one ladder carries an untitled rank.
_SIX_ROW_CAREERS = {
    "Athlete",
    "Barbarian",
    "Belter",
    "Drifter",
    "Entertainer",
    "Hunter",
    "Scout",
}


def test_the_packaged_set_holds_exactly_the_twenty_four_srd_careers():
    rules = load_rules()
    names = {career.name for career in rules.careers.values()}
    assert names == _TWENTY_FOUR_NAMES
    assert len(rules.careers) == 24


def test_every_cash_table_has_seven_rows_and_only_the_seven_have_six_material_rows():
    # FR-008's "no titles at all" is whole-ladder: Navy's enlisted ladder
    # carries four untitled *interior* rows (T047's contiguity gap-fill,
    # D2/FR-007) alongside titled ones, which is not the shape this checks.
    # A career only belongs to `_SIX_ROW_CAREERS` if every rank it has is
    # untitled, which is true of the seven commissionless careers' single
    # rank 0 and false of Navy's mixed ladder.
    rules = load_rules()
    for career in rules.careers.values():
        assert len(career.mustering_out.cash) == 7, career.name
        material_rows = len(career.mustering_out.benefits)
        ranks = [rank_row for ladder in career.ladders for rank_row in ladder.ranks]
        all_untitled = bool(ranks) and all(not rank_row.title for rank_row in ranks)
        if career.name in _SIX_ROW_CAREERS:
            assert material_rows == 6, career.name
            assert all_untitled, career.name
        else:
            assert material_rows == 7, career.name
            assert not all_untitled, career.name
