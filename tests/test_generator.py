import dataclasses

import pytest

from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scientist import SCIENTIST_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import (
    _HOMEWORLD_SKILLS,
    _apply_material_benefit,
    _apply_skill_entry,
    _apply_stat_boost,
    _check,
    _draw_distinct,
    _grant_background_skills,
    _muster_out,
    _roll_material_benefit,
    draft_character,
    generate_career_character,
    generate_character,
    roll_until_qualified,
)
from cetools.engine.models import STAT_NAMES, Character, GenerationFailure
from conftest import ConstantRoller, SequenceRoller, SmartRoller


class _MaxFaceRoller:
    """Always rolls the top face of whatever die it is asked for."""

    def roll(self, sides: int, count: int = 1) -> int:
        return sides


# --- Check helper ---


def test_check_succeeds_when_roll_plus_modifier_meets_target() -> None:
    # ConstantRoller(6): 2D6=6, Intelligence=8 → dm=0 → 6+0=6 >= target 6
    assert _check(ConstantRoller(6), {"Intelligence": 8}, "Intelligence", 6) is True


def test_check_fails_when_roll_plus_modifier_below_target() -> None:
    # ConstantRoller(5): 2D6=5, Intelligence=8 → dm=0 → 5+0=5 < target 6
    assert _check(ConstantRoller(5), {"Intelligence": 8}, "Intelligence", 6) is False


def test_check_applies_characteristic_modifier() -> None:
    # ConstantRoller(4): 2D6=4, Intelligence=12 → dm=+2 → 4+2=6 >= target 6
    # Without the modifier, 4 < 6 would fail.
    assert _check(ConstantRoller(4), {"Intelligence": 12}, "Intelligence", 6) is True


# --- Enlistment ---


def test_enlistment_failure_returns_generation_failure() -> None:
    # ConstantRoller(1): all characteristics = 1, Int modifier = -2,
    # qualification roll = 1 + (-2) = -1 < 6 → fail
    result = generate_character(NAVY_CAREER, roller=ConstantRoller(1))
    assert isinstance(result, GenerationFailure)
    assert result.exit_code == 1
    assert "enlist" in result.reason.lower() or "navy" in result.reason.lower()


def test_enlistment_pass_returns_character() -> None:
    # SmartRoller(10, 1): 2D6 = 10 (passes all checks), 1D6 = 1 (index 0 of tables)
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)


# --- UPP ---


def test_character_upp_is_six_pseudohex_chars() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert len(result.upp) == 6
    assert "I" not in result.upp
    assert "O" not in result.upp


# --- Name generation (US2) ---


def test_generated_character_has_non_empty_two_word_name() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.name
    assert len(result.name.split(" ")) >= 2


# --- Survival failure ---


def test_survival_fail_returns_character_with_mishap() -> None:
    # 6 characteristics (10 each) + 1 qualification (10) → pass enlistment
    # then survival roll = 1 → 1 + Int_dm(10) = 1 + 1 = 2 < 5 → mishap in term 1
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 1], default=1)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert result.terms[-1].survived is False


def test_mishap_ended_character_still_rolls_psionics() -> None:
    # Same term-1 mishap setup as test_survival_fail_returns_character_with_mishap.
    # The SequenceRoller is exhausted before the psi roll, so the Psi 2D6 draw
    # returns the default (1): psi_strength = max(0, 1 - terms_served). This
    # confirms a mishap-ended career still rolls Psi (design-spec testing case).
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 1], default=1)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert isinstance(result.talents, dict)
    assert result.psi_strength == max(0, 1 - result.terms_served)


# --- T010: one integration test per SURVIVAL_MISHAPS_TABLE roll ---


def test_mishap_roll_1_injury_no_discharge() -> None:
    # 7 passing values (6 characteristics + qualification, all 10) then a failing
    # survival roll (2), mishap-table roll (1), two injury rolls (6, 6 -> both land
    # on injury row 6, "no permanent effect", so no candidate/amount roll follows).
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 1, 6, 6], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap.roll == 1
    assert result.mishap.discharge_type == "none"
    assert result.mishap.imprisoned is False
    assert result.mishap.injury_reductions == {}
    assert result.mishap.injury_crisis is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_2_honorable_discharge() -> None:
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 2], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap.roll == 2
    assert result.mishap.discharge_type == "honorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_3_honorable_discharge_with_legal_debt() -> None:
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 3], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap.roll == 3
    assert result.mishap.discharge_type == "honorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 10_000
    assert result.age == 20


def test_mishap_roll_4_dishonorable_discharge_not_imprisoned() -> None:
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 4], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap.roll == 4
    assert result.mishap.discharge_type == "dishonorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_5_dishonorable_discharge_imprisoned() -> None:
    # Outcome 5 adds an extra 4 years for imprisonment on top of the mishap
    # term's usual +2 (research.md D9): age == 18 + 2 + 4 == 24.
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 5], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap.roll == 5
    assert result.mishap.discharge_type == "dishonorable"
    assert result.mishap.imprisoned is True
    assert result.debt == 0
    assert result.age == 24


def test_mishap_roll_6_medical_discharge_with_injury() -> None:
    # Mishap-table roll 6, single injury roll of 6 -> injury row 6, no effect.
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 6, 6], default=6)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.mishap.roll == 6
    assert result.mishap.discharge_type == "medical"
    assert result.mishap.imprisoned is False
    assert result.mishap.injury_reductions == {}
    assert result.mishap.injury_crisis is False
    assert result.debt == 0
    assert result.age == 20


def test_draft_character_survival_failure_returns_character_not_failure() -> None:
    # Proves FR-011: draft_character funnels through the same mishap-resolution
    # path as generate_character/generate_career_character, never GenerationFailure.
    # Draft roll 5 -> Scout; 6 characteristics of 10 qualify immediately
    # (Intelligence 10 >= 6); survival roll 2 -> 2 + End_dm(10)=1 = 3 < 7 -> fails;
    # mishap-table roll 2 -> honorable discharge, no injury.
    roller = SequenceRoller([5, 10, 10, 10, 10, 10, 10] + [6] * 4 + [2, 2], default=6)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.mishap is not None


# --- 7-term cap ---


def test_seven_term_cap_voluntary_musterout() -> None:
    # SmartRoller(10, 1): re-enlistment = 10 (passes 5+, not 12) → voluntary muster at term 7
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.terms_served == 7


# --- Natural 12 at term 7 forces term 8 ---


def test_natural_12_at_term_7_forces_term_8() -> None:
    # SmartRoller(12, 1): re-enlistment at term 7 = 12 → mandatory term 8,
    # then always muster out after term 8
    result = generate_character(NAVY_CAREER, roller=SmartRoller(12, 1))
    assert isinstance(result, Character)
    assert result.terms_served == 8


# --- Basic training ---


def test_first_term_basic_training_grants_all_six_service_skills() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    for skill_name in NAVY_CAREER.service_skills:
        assert (
            skill_name in result.skills
        ), f"Service skill {skill_name!r} missing from character after basic training"


# --- Skills non-empty ---


def test_character_has_non_empty_skills() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert len(result.skills) > 0


# --- Aging ---


def test_aging_check_triggers_at_term_4_or_later() -> None:
    # SmartRoller(10, 1) → 7 terms served, aging starts at term 4
    # With 2D6=10: aging roll = 10 - terms_served; at term 7 it's 10-7=3 ≥ 1, no reduction
    # but we confirm the character completes successfully (aging doesn't crash)
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.terms_served >= 4
    assert result.age >= 34


# --- Pension ---


def test_pension_present_at_5_or_more_terms() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.terms_served >= 5
    assert result.pension is not None
    assert result.pension > 0


def test_pension_amount_for_seven_terms() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.terms_served == 7
    assert result.pension == 14000


# --- Cash roll cap ---


def test_cash_roll_cap_at_3() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    cash_benefits = [b for b in result.benefits if b.kind == "cash"]
    assert len(cash_benefits) <= 3


# --- Rank bonuses on mustering out ---


def test_rank_bonus_muster_rolls_applied() -> None:
    # SmartRoller(10, 1): reaches rank 6 (Commodore) → +3 muster rolls
    # 7 terms + 3 rank bonus = 10 total benefit rolls
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.rank == 6
    expected_total = result.terms_served + 3  # O6 bonus = 3
    assert len(result.benefits) == expected_total


# --- Material benefit row 7 reachable via rank DM ---


def test_material_benefit_row_7_reachable_at_rank_5_plus() -> None:
    # Direct unit test of _muster_out (a full generate_character run with a
    # fixed-value roller would hang once reroll-on-repeat is wired in below, since
    # a fixed roller can never produce a "different" result). rank=5 -> material_dm=1,
    # so idx = clamp(roll + 1 - 1) = roll. terms_served=2 + rank-5 bonus_rolls (2) = 4
    # total rolls: 3 cash (cap) + 1 material. ConstantRoller(6): material die=6 ->
    # idx=6 -> material_benefits[6] = "Explorers' Society". Without the rank-5+ DM,
    # idx would clamp to 5 (High Passage), so this confirms row 7 is reachable.
    result = _muster_out(
        career=NAVY_CAREER,
        terms_served=2,
        rank=5,
        skills={},
        characteristics={},
        roller=ConstantRoller(6),
    )
    assert len(result) == 4
    material_benefits = [b for b in result if b.kind == "material"]
    assert any(
        b.material_name == "Explorers' Society" for b in material_benefits
    ), "rank 5+ DM should make material benefit row 7 (Explorers' Society) reachable"


def test_muster_out_grants_explorers_society_once_and_rerolls_repeat() -> None:
    # NAVY_CAREER.material_benefits[6] = "Explorers' Society". rank=5 -> material_dm=1,
    # so idx = clamp(roll + 1 - 1) = roll. terms_served=3 + rank-5 bonus_rolls (2) = 5
    # total rolls: 3 cash (any values) + 2 material.
    # Material roll 1: die=6 -> idx 6 -> "Explorers' Society" (granted).
    # Material roll 2: die=6 -> idx 6 -> "Explorers' Society" again, but it's already
    # granted, so it rerolls: die=2 -> idx 2 -> "Weapon" (accepted).
    roller = SequenceRoller([1, 1, 1, 6, 6, 2], default=6)
    result = _muster_out(
        career=NAVY_CAREER,
        terms_served=3,
        rank=5,
        skills={},
        characteristics={},
        roller=roller,
    )
    assert len(result) == 5  # reroll must not add an extra roll (FR-008)
    material = [b.material_name for b in result if b.kind == "material"]
    assert material == ["Explorers' Society", "Weapon"]


# --- Cash DM from Gambling skill ---


def test_gambling_skill_grants_cash_dm_on_muster_out() -> None:
    # Direct unit test of _muster_out with a controlled 1D6 roll of 5.
    # Without Gambling: idx = max(0, min(6, 5+0-1)) = 4 → cash_benefits[4] = 20,000
    # With Gambling:    idx = max(0, min(6, 5+1-1)) = 5 → cash_benefits[5] = 50,000
    common = dict(
        career=NAVY_CAREER,
        terms_served=1,
        rank=0,
        characteristics={},
        roller=ConstantRoller(5),
    )
    without_dm = _muster_out(**common, skills={})
    with_dm = _muster_out(**common, skills={"Gambling": 0})
    assert len(without_dm) == 1
    assert len(with_dm) == 1
    assert without_dm[0].cash_amount == 20000
    assert with_dm[0].cash_amount == 50000


# --- Explorers' Society: reroll on repeat ---


def test_roll_material_benefit_grants_explorers_society_when_not_yet_granted() -> None:
    # NAVY_CAREER.material_benefits[6] = "Explorers' Society". material_dm=1, so
    # idx = clamp(roll + 1 - 1) = roll; ConstantRoller(6) -> idx 6.
    name = _roll_material_benefit(NAVY_CAREER, 1, ConstantRoller(6), set())
    assert name == "Explorers' Society"


def test_roll_material_benefit_rerolls_once_when_already_granted() -> None:
    # First die = 6 -> "Explorers' Society", but it's already granted, so it
    # rerolls: second die = 3 -> idx 3 -> "Mid Passage".
    roller = SequenceRoller([6, 3], default=6)
    name = _roll_material_benefit(NAVY_CAREER, 1, roller, {"Explorers' Society"})
    assert name == "Mid Passage"


def test_roll_material_benefit_rerolls_repeatedly_until_non_duplicate() -> None:
    # Three more 6s in a row (each still "Explorers' Society", already granted)
    # before a 2 finally lands on idx 2 -> "Weapon".
    roller = SequenceRoller([6, 6, 6, 2], default=6)
    name = _roll_material_benefit(NAVY_CAREER, 1, roller, {"Explorers' Society"})
    assert name == "Weapon"


def test_roll_material_benefit_unaffected_for_career_without_explorers_society() -> None:
    # AEROSPACE_CAREER.material_benefits[6] = "+1 Soc" (no "Explorers' Society" entry
    # exists in this table at all), so the uniqueness check can never match —
    # behavior is identical to before this feature, even when `granted_names`
    # already contains that string. material_dm=1, so idx = clamp(6 + 1 - 1) = 6.
    name = _roll_material_benefit(AEROSPACE_CAREER, 1, ConstantRoller(6), {"Explorers' Society"})
    assert name == "+1 Soc"


# --- Research Vessel (Scientist) and Courier Vessel (Scout): once-only ---


def test_roll_material_benefit_grants_research_vessel_when_not_yet_granted() -> None:
    # SCIENTIST_CAREER.material_benefits[6] = "Research Vessel". material_dm=1, so
    # idx = clamp(6 + 1 - 1) = 6.
    name = _roll_material_benefit(SCIENTIST_CAREER, 1, ConstantRoller(6), set())
    assert name == "Research Vessel"


def test_roll_material_benefit_rerolls_research_vessel_when_already_granted() -> None:
    # First die = 6 -> "Research Vessel", already granted, so it rerolls:
    # second die = 4 -> idx 4 -> "+1 Soc".
    roller = SequenceRoller([6, 4], default=6)
    name = _roll_material_benefit(SCIENTIST_CAREER, 1, roller, {"Research Vessel"})
    assert name == "+1 Soc"


def test_roll_material_benefit_grants_courier_vessel_when_not_yet_granted() -> None:
    # SCOUT_CAREER.material_benefits has 6 entries; [5] = "Courier Vessel".
    # material_dm=1, roll 6 -> idx = clamp(6, 0, 5) = 5.
    name = _roll_material_benefit(SCOUT_CAREER, 1, ConstantRoller(6), set())
    assert name == "Courier Vessel"


def test_roll_material_benefit_rerolls_courier_vessel_when_already_granted() -> None:
    # First die = 6 -> idx 5 -> "Courier Vessel", already granted, so it rerolls:
    # second die = 3 -> idx 3 -> "Mid Passage".
    roller = SequenceRoller([6, 3], default=6)
    name = _roll_material_benefit(SCOUT_CAREER, 1, roller, {"Courier Vessel"})
    assert name == "Mid Passage"


def test_roll_material_benefit_terminates_with_fixed_roller_on_granted_unique() -> None:
    # ConstantRoller(6) always lands on SCOUT_CAREER.material_benefits[5]
    # ("Courier Vessel"). With it already granted, the reroll loop would spin
    # forever without a cap; the fallback must return a non-duplicate benefit.
    name = _roll_material_benefit(SCOUT_CAREER, 1, ConstantRoller(6), {"Courier Vessel"})
    assert name != "Courier Vessel"
    assert name in SCOUT_CAREER.material_benefits


def test_roll_material_benefit_raises_when_no_eligible_benefit_remains() -> None:
    import dataclasses

    import pytest

    # Degenerate career whose entire material table is once-only benefits that
    # are all already granted: the reroll loop exhausts and the fallback finds
    # nothing, so the guard raises a descriptive error instead of a bare
    # StopIteration. Not reachable with any real career table.
    degenerate = dataclasses.replace(
        SCOUT_CAREER,
        material_benefits=("Explorers' Society", "Research Vessel", "Courier Vessel"),
    )
    granted = {"Explorers' Society", "Research Vessel", "Courier Vessel"}
    with pytest.raises(RuntimeError, match="no material benefit outside"):
        _roll_material_benefit(degenerate, 0, ConstantRoller(1), granted)


# --- Benefits non-empty ---


def test_character_has_non_empty_benefits() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert len(result.benefits) > 0


# --- terms_served ≥ 1 ---


def test_successful_character_served_at_least_one_term() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.terms_served >= 1


# --- Skill rolls per term ---


def test_failed_commission_grants_two_skill_rolls() -> None:
    # Stats=8 (modifier 0); qualify 8≥6 ✓, survive 8≥5 ✓, commission 4+0=4<7 ✗.
    # Neither commission nor advancement was received, so 2 skill rolls must follow.
    # Each skill roll consumes 2 dice: table select then entry select.
    # Edu=8 → 4 tables; 1D6=2 → (2-1)%4=1 → service_skills; 1D6=1 → "Comms".
    # Comms is level 0 after basic training; two rolls push it to level 2.
    # With only 1 roll it would stay at 1.
    roller = SequenceRoller([8] * 6 + [6, 6, 6] + [8, 8, 4, 2, 1, 2], default=1)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.rank == 0
    assert result.skills.get("Comms") == 2, "failed commission should not reduce skill rolls to 1"


def test_per_term_skill_rolls_recorded_in_term_history() -> None:
    # Same roller: 2 skill rolls after failed commission, both land on "Comms".
    # Basic training records 6 service skills; each skill roll appends its entry.
    # Edu=8 → 4 tables; 1D6=2 → service_skills[0] = "Comms".
    roller = SequenceRoller([8] * 6 + [6, 6, 6] + [8, 8, 4, 2, 1, 2], default=1)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    term = result.terms[0]
    # 6 from basic training + 2 from skill rolls
    assert len(term.skills_gained) == 8
    # "Comms" appears once in basic training and twice from the two skill rolls
    assert term.skills_gained.count("Comms") == 3


# --- Rank bonus skill levels ---


def test_rank_bonus_skills_granted_at_level_1() -> None:
    # SmartRoller(10, 1): 1D6=1 → table index (1-1)%4=0 → personal_development[0]
    # = "+1 Str" for every skill roll, so Zero-G (rank 0) and Tactics (rank 3)
    # can only appear via rank bonuses and must start at level 1, not 0.
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.skills.get("Zero-G") == 1, "rank-0 bonus should grant Zero-G-1"
    assert result.skills.get("Tactics") == 1, "rank-3 bonus should grant Tactics-1"


# --- Extensibility (US3 preview) ---


def test_generate_character_accepts_any_career_without_navy_hardcoding() -> None:
    import dataclasses

    stub_career = dataclasses.replace(NAVY_CAREER, name="Scout")
    result = generate_character(stub_career, roller=SmartRoller(10, 1))
    assert isinstance(result, (Character, GenerationFailure))


# --- Stat boost helper ---


def test_apply_stat_boost_applies_boost_and_returns_true() -> None:
    characteristics = {"Strength": 7}
    assert _apply_stat_boost("+1 Str", characteristics) is True
    assert characteristics["Strength"] == 8


def test_apply_stat_boost_returns_false_for_plain_skill_name() -> None:
    characteristics = {"Strength": 7}
    assert _apply_stat_boost("Melee Combat", characteristics) is False
    assert characteristics["Strength"] == 7


def test_apply_stat_boost_returns_true_for_unknown_abbreviation_without_applying() -> None:
    characteristics = {"Strength": 7}
    assert _apply_stat_boost("+1 Xyz", characteristics) is True
    assert characteristics == {"Strength": 7}


# --- Characteristic cap at 33 ---


def test_apply_skill_entry_caps_stat_at_33() -> None:
    characteristics = {"Strength": 33}
    _apply_skill_entry("+1 Str", characteristics, {})
    assert characteristics["Strength"] == 33


def test_apply_material_benefit_caps_stat_at_33() -> None:
    characteristics = {"Strength": 33}
    _apply_material_benefit("+1 Str", characteristics, {})
    assert characteristics["Strength"] == 33


# --- T008: roll_until_qualified ---


def test_roll_until_qualified_returns_qualifying_characteristics() -> None:
    # First iteration: all stats=2, Intelligence=2 < 6 → fail
    # Second iteration: all stats=8, Intelligence=8 >= 6 → return
    roller = SequenceRoller([2] * 6 + [8] * 6, default=8)
    chars = roll_until_qualified(SCOUT_CAREER, roller)
    assert chars[SCOUT_CAREER.qualification_stat] >= SCOUT_CAREER.qualification_target


def test_roll_until_qualified_loops_until_qualified() -> None:
    # Three failing iterations (Int=3 < 6), then one passing (Int=8)
    roller = SequenceRoller([3] * 18 + [8] * 6, default=8)
    chars = roll_until_qualified(SCOUT_CAREER, roller)
    assert chars["Intelligence"] >= 6
    # Roller consumed more than 6 values → actually looped multiple times
    assert roller._pos > 6


# --- T009: generate_character new params ---


def test_preset_characteristics_missing_stat_raises() -> None:
    incomplete = {
        "Strength": 9,
        "Dexterity": 9,
        "Endurance": 9,
        "Intelligence": 9,
        # Education and Social Standing intentionally omitted
    }
    with pytest.raises(ValueError, match="missing required stats"):
        generate_character(NAVY_CAREER, preset_characteristics=incomplete)


def test_preset_characteristics_are_used_not_rolled() -> None:
    # SmartRoller(10, 1) would roll Intelligence=10; preset gives Intelligence=9
    preset = {
        "Strength": 9,
        "Dexterity": 9,
        "Endurance": 9,
        "Intelligence": 9,
        "Education": 9,
        "Social Standing": 9,
    }
    result = generate_character(
        NAVY_CAREER,
        roller=SmartRoller(10, 1),
        preset_characteristics=preset,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    # Intelligence=9 comes from preset, not 10 from SmartRoller
    # SmartRoller(10, 1) → aging roll 10-terms ≥ 1 always → no stat reduction
    assert result.characteristics["Intelligence"] == 9


def test_bypass_qualification_skips_enlistment() -> None:
    # ConstantRoller(1): qual_dm=-2, roll=1 → -1 < 6 → normally fails enlistment
    # bypass_qualification=True must skip the enlistment check entirely; the
    # survival check then also fails (1 + -2 < 5), which now resolves via the
    # mishap table instead of GenerationFailure.
    result = generate_character(NAVY_CAREER, roller=ConstantRoller(1), bypass_qualification=True)
    assert isinstance(result, Character)


def test_hard_max_terms_prevents_forced_8th_term() -> None:
    # SmartRoller(12, 1): re-enlistment at term 7 = 12 → normally forces term 8
    # hard_max_terms=True must prevent the extra term
    result = generate_character(
        NAVY_CAREER,
        roller=SmartRoller(12, 1),
        bypass_qualification=True,
        hard_max_terms=True,
    )
    assert isinstance(result, Character)
    assert result.terms_served == 7


def test_drafted_param_sets_character_drafted_true() -> None:
    result = generate_character(
        NAVY_CAREER,
        roller=SmartRoller(10, 1),
        bypass_qualification=True,
        drafted=True,
    )
    assert isinstance(result, Character)
    assert result.drafted is True


def test_drafted_defaults_to_false_in_generate_character() -> None:
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.drafted is False


# --- T010: generate_career_character with Scout ---


def test_generate_career_character_returns_character() -> None:
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)


def test_generate_career_character_intelligence_at_least_6() -> None:
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.characteristics["Intelligence"] >= 6


def test_generate_career_character_piloting_at_level_1() -> None:
    # rank-0 bonus grants Piloting+1 before basic training; basic training skips setting it to 0
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.skills.get("Piloting", 0) >= 1


def test_generate_career_character_two_skill_rolls_per_term() -> None:
    # Scout has no commission/advancement → always 2 skill rolls per term
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    for i, term in enumerate(result.terms):
        non_bt = term.skills_gained if i > 0 else term.skills_gained[6:]
        assert len(non_bt) == 2, f"Term {i + 1} expected 2 skill rolls, got {len(non_bt)}"


def test_generate_career_character_material_roll_5_gives_explorers_society() -> None:
    # Direct unit test of _muster_out (a full generate_career_character run with a
    # fixed-value roller would hang once reroll-on-repeat is wired in, since a fixed
    # roller can never produce a "different" result). rank=0 -> material_dm=0, so
    # idx = clamp(roll + 0 - 1) = roll - 1. terms_served=4 + rank-0 bonus_rolls (0) = 4
    # total rolls: 3 cash (cap) + 1 material. ConstantRoller(5): material die=5 -> idx=4 ->
    # SCOUT_CAREER.material_benefits[4] = "Explorers' Society". This confirms row 5
    # (idx 4) is reachable with a roll of 5 and no rank DM.
    result = _muster_out(
        career=SCOUT_CAREER,
        terms_served=4,
        rank=0,
        skills={},
        characteristics={},
        roller=ConstantRoller(5),
    )
    assert len(result) == 4
    material_benefits = [b for b in result if b.kind == "material"]
    assert any(b.material_name == "Explorers' Society" for b in material_benefits)


# --- T010a: Education < 8 restricts Scout skill rolls to 3 tables ---


def test_education_below_8_excludes_advanced_education_skills() -> None:
    # ConstantRoller(7): all stats=7, Education=7 < 8 → only 3 skill tables (no advanced education)
    # Skill rolls hit personal_development[0] = "+1 Str" (stat boost, no skill entry added)
    # Background skills are random now; probe only advanced-education-exclusive skills.
    # Check skills that come ONLY from advanced_education and not from other sources
    result = generate_career_character(SCOUT_CAREER, roller=ConstantRoller(7))
    assert isinstance(result, Character)
    # Navigation and Tactics are in advanced_education only (not in service/background skills)
    exclusively_advanced = {"Navigation", "Tactics"}
    for skill in exclusively_advanced:
        assert (
            skill not in result.skills
        ), f"{skill!r} must not appear when Edu<8 (advanced education excluded)"


def test_education_8_or_above_can_access_advanced_education() -> None:
    # SmartRoller(10, 4): all stats=10, Education=10 >= 8 → 4 tables available
    # Skill table: (4-1)%4=3 → advanced_education; entry: (4-1)%6=3 → "Medicine"
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 4))
    assert isinstance(result, Character)
    assert "Medicine" in result.skills


# --- T010b: single-term Scout muster out ---


def test_single_term_scout_muster_out() -> None:
    # Qualification: 6 rolls of 8 (Intelligence=8 >= 6 → passes first try)
    # Survival (2D6=8 >= 7 ✓); 2 skill rolls (1D6=1,1 each); re-enlistment (2D6=4 < 6 → fail)
    roller = SequenceRoller([8] * 6 + [6, 6, 6] + [8, 1, 1, 1, 1, 4, 1], default=1)
    result = generate_career_character(SCOUT_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.skills.get("Piloting", 0) >= 1
    term = result.terms[0]
    assert len(term.skills_gained) == 8  # 6 basic training + 2 skill rolls
    assert len(term.skills_gained[6:]) == 2
    assert len(result.benefits) == 1


# --- T015: draft_character ---


def test_draft_character_roll_5_gives_scout() -> None:
    # DRAFT_TABLE[4] = "scout"; 1D6 roll=5 → index 4 → Scout career
    roller = SequenceRoller([5], default=10)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Scout"


def test_draft_character_roll_1_gives_aerospace() -> None:
    # DRAFT_TABLE[0] = "aerospace system defense"; 1D6 roll=1 → index 0
    roller = SequenceRoller([1], default=10)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Aerospace System Defense"


def test_draft_character_sets_drafted_true() -> None:
    # default=6 (not a larger value like 10): a fixed high-value roller would let
    # rank climb until material_dm=1, at which point every material-benefit roll
    # resolves to index 6 ("Explorers' Society"). Once granted once, the
    # reroll-on-repeat helper would call roller.roll(6) again forever, since a
    # fixed roller can never return a different value — an infinite loop.
    # default=6 keeps commission from ever succeeding (Navy needs Social
    # Standing >= 7; a fixed characteristic of 6 with a +0 DM never reaches it),
    # so rank stays 0, material_dm stays 0, and every material roll resolves to
    # index 5 ("High Passage") instead — no reroll is ever triggered.
    roller = SequenceRoller([3], default=6)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.drafted is True


def test_draft_character_roll_2_gives_marine() -> None:
    # DRAFT_TABLE[1] = "marine"; 1D6 roll=2 → index 1 → Marine career
    # default=6 for the same reason as test_draft_character_sets_drafted_true
    # above. Marine's commission succeeds once at this default (Education
    # target is exactly 6), reaching rank 1, but advancement then never
    # succeeds (Social Standing target 7, unmet), so rank stays at 1 and
    # material_dm stays 0 — every material roll resolves to index 5 ("High
    # Passage"), never index 6 ("Explorers' Society"), so no reroll is ever
    # triggered.
    roller = SequenceRoller([2], default=6)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Marine"


# --- T016: draft_character with unimplemented career ---


def test_draft_character_unimplemented_career_returns_failure() -> None:
    from unittest.mock import patch

    # Patch DRAFT_TABLE in generator so index 0 is "smuggler" (not in CAREER_REGISTRY)
    with patch("cetools.engine.generator.DRAFT_TABLE", ("smuggler",) + ("navy",) * 5):
        roller = SequenceRoller([1], default=10)
        result = draft_character(roller=roller)
    assert isinstance(result, GenerationFailure)
    assert "smuggler" in result.reason


# --- T017: benefits/pension/debt matrix after 5+ completed terms (US3) ---

_SCOUT_PRESET = {
    "Strength": 10,
    "Dexterity": 10,
    "Endurance": 10,
    "Intelligence": 10,
    "Education": 10,
    "Social Standing": 10,
}


def _five_completed_scout_terms() -> list[int]:
    # Scout has no commission/advancement, so each term is: survival(2D6),
    # 2 skill rolls (table+entry each), [aging(2D6) once age>=34], reenlist(2D6).
    # Preset stats of 10 give Endurance dm +1 (survival target 7, reenlistment
    # target 6) so a roll of 10 passes every check; 1D6=1 keeps skill rolls
    # deterministic (harmless "+1 Str" stat boosts, not asserted on here).
    no_aging_term = [10, 1, 1, 1, 1, 10]
    aging_term = [10, 1, 1, 1, 1, 10, 10]  # terms 4-5: age reaches 34+
    return no_aging_term * 3 + aging_term * 2


def _generate_scout_mishap_after_five_terms(mishap_extra: list[int]) -> Character:
    # Term 6's survival roll (value 1) fails: 1 + End_dm(10)=1 = 2 < target 7.
    values = [6] * 4 + _five_completed_scout_terms() + [1] + mishap_extra
    roller = SequenceRoller(values, default=6)
    result = generate_character(
        SCOUT_CAREER,
        roller=roller,
        preset_characteristics=_SCOUT_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    return result


def test_mishap_outcome_1_preserves_benefits_and_pension_after_five_terms() -> None:
    # Mishap-table roll 1, injury rolls (6, 6) -> injury row 6, no effect.
    result = _generate_scout_mishap_after_five_terms([1, 6, 6])
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


def test_mishap_outcome_2_preserves_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms([2])
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


def test_mishap_outcome_3_preserves_benefits_and_pension_with_legal_debt() -> None:
    result = _generate_scout_mishap_after_five_terms([3])
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 10_000


def test_mishap_outcome_4_forfeits_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms([4])
    assert result.terms_served == 5
    assert result.benefits == []
    assert result.pension is None


def test_mishap_outcome_5_forfeits_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms([5])
    assert result.terms_served == 5
    assert result.benefits == []
    assert result.pension is None


def test_mishap_outcome_6_preserves_benefits_and_pension_after_five_terms() -> None:
    # Mishap-table roll 6, single injury roll 6 -> injury row 6, no effect.
    result = _generate_scout_mishap_after_five_terms([6, 6])
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


# --- T019: mishap during a character's very first term (edge case) ---


def _generate_scout_first_term_mishap(mishap_extra: list[int]) -> Character:
    # Term 1's survival roll (value 1) fails immediately: no prior terms.
    values = [6] * 4 + [1] + mishap_extra
    roller = SequenceRoller(values, default=6)
    result = generate_character(
        SCOUT_CAREER,
        roller=roller,
        preset_characteristics=_SCOUT_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    return result


@pytest.mark.parametrize(
    "mishap_extra",
    [[1, 6, 6], [2], [3], [4], [5], [6, 6]],
    ids=["outcome1", "outcome2", "outcome3", "outcome4", "outcome5", "outcome6"],
)
def test_first_term_mishap_yields_no_benefits_or_pension(mishap_extra: list[int]) -> None:
    result = _generate_scout_first_term_mishap(mishap_extra)
    assert result.terms_served == 0
    assert result.benefits == []
    assert result.pension is None


# --- T011: two skill rolls per term recorded in term history ---


def test_two_skill_rolls_per_term_in_term_history() -> None:
    # SmartRoller(10, 1): all terms complete; basic training only in term 1
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.terms_served >= 2
    # Term 1: 6 basic training entries + 2 skill roll entries
    assert len(result.terms[0].skills_gained) == 8
    # All subsequent terms: exactly 2 skill roll entries each
    for term in result.terms[1:]:
        assert len(term.skills_gained) == 2


# --- Background skills: _draw_distinct ---


def test_draw_distinct_returns_requested_count_of_distinct_items() -> None:
    # ConstantRoller(1): idx = (1-1) % len = 0 every time → pops the head repeatedly.
    result = _draw_distinct(("A", "B", "C", "D"), 3, ConstantRoller(1))
    assert result == ["A", "B", "C"]
    assert len(set(result)) == 3


def test_draw_distinct_respects_exclude() -> None:
    result = _draw_distinct(("A", "B", "C"), 2, ConstantRoller(1), exclude=("A",))
    assert result == ["B", "C"]
    assert "A" not in result


def test_draw_distinct_truncates_when_over_requested() -> None:
    # Only 2 items available but 5 requested → returns just the 2.
    result = _draw_distinct(("A", "B"), 5, ConstantRoller(1))
    assert result == ["A", "B"]


def test_draw_distinct_uses_roller_to_index() -> None:
    # ConstantRoller(3): idx = (3-1) % len = 2 % len.
    # remaining=[A,B,C,D] → idx 2 → C; remaining=[A,B,D] → idx 2 → D.
    result = _draw_distinct(("A", "B", "C", "D"), 2, ConstantRoller(3))
    assert result == ["C", "D"]


def test_draw_distinct_can_reach_pool_tail() -> None:
    # Regression: indexing a pool larger than 6 with a fixed d6 left the tail
    # unreachable (Zero-G at index 9 could never be drawn). Sizing the die to the
    # remaining pool makes the last element reachable.
    result = _draw_distinct(_HOMEWORLD_SKILLS, 1, _MaxFaceRoller())
    assert result == ["Zero-G"]


# --- Background skills: _grant_background_skills ---


def test_background_skill_count_matches_three_plus_education_dm() -> None:
    # count = 3 + characteristic_modifier(Education).
    cases = {2: 1, 4: 2, 7: 3, 10: 4, 12: 5, 15: 6}
    for education, expected in cases.items():
        skills: dict[str, int] = {}
        _grant_background_skills({"Education": education}, skills, ConstantRoller(1))
        assert len(skills) == expected, f"Education {education} should grant {expected} skills"


def test_background_skills_are_all_level_zero() -> None:
    skills: dict[str, int] = {}
    _grant_background_skills({"Education": 12}, skills, ConstantRoller(1))
    assert all(level == 0 for level in skills.values())


def test_background_low_education_draws_only_homeworld_skills() -> None:
    # count 1 (Edu 2) and count 2 (Edu 4) → every skill comes from the homeworld pool.
    for education in (2, 4):
        skills: dict[str, int] = {}
        _grant_background_skills({"Education": education}, skills, ConstantRoller(1))
        assert set(skills) <= set(_HOMEWORLD_SKILLS)


def test_background_full_draw_is_deterministic_and_distinct() -> None:
    # Edu 12 → count 5. ConstantRoller(1) always pops index 0.
    # Homeworld: Animals, Broker. Education (excluding those): Admin, Advocate, Carousing.
    skills: dict[str, int] = {}
    _grant_background_skills({"Education": 12}, skills, ConstantRoller(1))
    assert set(skills) == {"Animals", "Broker", "Admin", "Advocate", "Carousing"}


def test_background_skills_reproducible_across_identical_rollers() -> None:
    first: dict[str, int] = {}
    second: dict[str, int] = {}
    _grant_background_skills({"Education": 10}, first, SequenceRoller([2, 4, 1, 3]))
    _grant_background_skills({"Education": 10}, second, SequenceRoller([2, 4, 1, 3]))
    assert first == second


def test_generate_character_grants_background_skills() -> None:
    # Preset Education 10 → 4 background skills. SmartRoller single-die value 1 →
    # idx 0 every draw → homeworld Animals, Broker; education Admin, Advocate.
    # Broker/Admin/Advocate are not Scout service, rank, or skill-roll outputs
    # under this roller, so they can only come from background granting.
    preset = {
        "Strength": 10,
        "Dexterity": 10,
        "Endurance": 10,
        "Intelligence": 10,
        "Education": 10,
        "Social Standing": 10,
    }
    result = generate_character(
        SCOUT_CAREER,
        roller=SmartRoller(10, 1),
        preset_characteristics=preset,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    for skill in ("Animals", "Broker", "Admin", "Advocate"):
        assert skill in result.skills
    assert result.skills["Broker"] == 0


def test_generate_character_none_qualification_skips_enlistment_failure() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # ConstantRoller(1) would fail Navy's Int 6+ qualification; with no
    # qualification the career must not return an enlistment failure.
    result = generate_character(no_qual, roller=ConstantRoller(1))
    assert isinstance(result, Character)


def test_generate_character_concrete_qualification_still_gates() -> None:
    result = generate_character(NAVY_CAREER, roller=ConstantRoller(1))
    assert isinstance(result, GenerationFailure)
    assert "enlistment failed" in result.reason


def test_roll_until_qualified_none_qualification_returns_immediately() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # All stats roll to 1 — Navy would loop forever; no-qual returns at once.
    result = roll_until_qualified(no_qual, roller=ConstantRoller(1))
    assert set(result.keys()) == set(STAT_NAMES)


def test_muster_out_ship_shares_rolls_quantity() -> None:
    import dataclasses

    from cetools.engine.models import STAT_NAMES

    ship_career = dataclasses.replace(
        NAVY_CAREER,
        material_benefits=(
            "Low Passage",
            "+1 Int",
            "Weapon",
            "Mid Passage",
            "+1 Soc",
            "High Passage",
            "1D6 Ship Shares",
        ),
    )
    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 5 -> material_dm=1 and +2 bonus muster rolls; terms=2 -> 4 total rolls
    # (3 cash cap, then 1 material). Cash rolls 1,1,1; material-select roll 6 ->
    # idx 6 -> "1D6 Ship Shares"; quantity roll 3.
    roller = SequenceRoller([1, 1, 1, 6, 3])
    benefits = _muster_out(ship_career, 2, 5, {}, characteristics, roller)
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3
    # ship shares do not touch characteristics
    assert all(value == 7 for value in characteristics.values())


def test_muster_out_zero_cash_benefit() -> None:
    from cetools.engine.careers.barbarian import BARBARIAN_CAREER
    from cetools.engine.models import STAT_NAMES

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0, terms=1 -> 1 total roll (cash). ConstantRoller(1) with no Gambling
    # -> cash_dm=0 -> idx 0 -> cash_benefits[0] == 0.
    benefits = _muster_out(BARBARIAN_CAREER, 1, 0, {}, characteristics, ConstantRoller(1))
    cash = [b for b in benefits if b.kind == "cash"]
    assert len(cash) == 1
    assert cash[0].cash_amount == 0


def test_muster_out_hunter_ship_shares() -> None:
    from cetools.engine.careers.hunter import HUNTER_CAREER
    from cetools.engine.models import STAT_NAMES

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0 -> material_dm=0; terms=4 -> 4 total rolls (3 cash cap, 1 material).
    # Cash rolls 1,1,1; material-select roll 5 -> idx 4 -> "1D6 Ship Shares";
    # quantity roll 3.
    roller = SequenceRoller([1, 1, 1, 5, 3])
    benefits = _muster_out(HUNTER_CAREER, 4, 0, {}, characteristics, roller)
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3


def test_generate_career_character_drifter_no_qualification() -> None:
    from cetools.engine.careers.drifter import DRIFTER_CAREER

    result = generate_career_character(DRIFTER_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.career == "Drifter"


def test_muster_out_belter_ship_shares() -> None:
    from cetools.engine.careers.belter import BELTER_CAREER
    from cetools.engine.models import STAT_NAMES

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0 -> material_dm=0; terms=4 -> 4 total rolls (3 cash cap, 1 material).
    # Cash rolls 1,1,1; material-select roll 5 -> idx 4 -> "1D6 Ship Shares";
    # quantity roll 3.
    roller = SequenceRoller([1, 1, 1, 5, 3])
    benefits = _muster_out(BELTER_CAREER, 4, 0, {}, characteristics, roller)
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3


# --- Psionics ---


def test_generated_character_has_psionics() -> None:
    # ConstantRoller returns 9 for every roll, including the Psi 2D6 roll, so
    # Psi = max(0, 9 - terms_served). terms_served is on the result, so the
    # relationship holds without predicting the full generation.
    result = generate_career_character(NAVY_CAREER, ConstantRoller(9))
    assert isinstance(result, Character)
    assert isinstance(result.talents, dict)
    assert result.psi_strength == max(0, 9 - result.terms_served)
