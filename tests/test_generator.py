import pytest

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import (
    _apply_material_benefit,
    _apply_skill_entry,
    draft_character,
    generate_career_character,
    generate_character,
    roll_until_qualified,
)
from cetools.engine.models import Character, GenerationFailure


class ConstantRoller:
    """Returns the same value for all dice rolls."""

    def __init__(self, value: int):
        self._value = value

    def roll(self, sides: int, count: int = 1) -> int:
        return self._value


class SmartRoller:
    """Returns one value for 2-dice rolls (checks) and another for 1-die rolls (tables)."""

    def __init__(self, two_dice_value: int, one_die_value: int):
        self._two = two_dice_value
        self._one = one_die_value

    def roll(self, sides: int, count: int = 1) -> int:
        return self._two if count >= 2 else self._one


class SequenceRoller:
    """Returns values from a sequence, then falls back to a default."""

    def __init__(self, values: list[int], default: int = 6):
        self._values = list(values)
        self._pos = 0
        self._default = default

    def roll(self, sides: int, count: int = 1) -> int:
        if self._pos < len(self._values):
            val = self._values[self._pos]
            self._pos += 1
            return val
        return self._default


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


# --- Survival failure ---


def test_survival_fail_returns_generation_failure() -> None:
    # 6 characteristics (10 each) + 1 qualification (10) → pass enlistment
    # then survival roll = 1 → 1 + Int_dm(10) = 1 + 1 = 2 < 5 → die in term 1
    roller = SequenceRoller([10] * 7 + [1], default=1)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, GenerationFailure)
    assert result.exit_code == 1
    assert (
        "term" in result.reason.lower()
        or "killed" in result.reason.lower()
        or "died" in result.reason.lower()
    )


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
    # SmartRoller(10, 6): all 2D6 checks pass → rank 6 (Commodore), 7 terms served;
    # material_dm = 1 (rank >= 5). Each material benefit roll: 6 + 1 - 1 = 6 → index 6
    # → material_benefits[6] = "Explorer's Society". Without the DM it would be index 5
    # (High Passage), so this confirms row 7 is reachable.
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 6))
    assert isinstance(result, Character)
    assert result.rank >= 5
    material_benefits = [b for b in result.benefits if b.kind == "material"]
    assert any(
        b.material_name == "Explorer's Society" for b in material_benefits
    ), "rank 5+ DM should make material benefit row 7 (Explorer's Society) reachable"


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
    roller = SequenceRoller([8, 8, 8, 8, 8, 8, 8, 8, 4, 2, 1, 2], default=1)
    result = generate_character(NAVY_CAREER, roller=roller)
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.rank == 0
    assert result.skills.get("Comms") == 2, "failed commission should not reduce skill rolls to 1"


def test_per_term_skill_rolls_recorded_in_term_history() -> None:
    # Same roller: 2 skill rolls after failed commission, both land on "Comms".
    # Basic training records 6 service skills; each skill roll appends its entry.
    # Edu=8 → 4 tables; 1D6=2 → service_skills[0] = "Comms".
    roller = SequenceRoller([8, 8, 8, 8, 8, 8, 8, 8, 4, 2, 1, 2], default=1)
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
    # bypass_qualification=True must skip the enlistment check entirely
    result = generate_character(NAVY_CAREER, roller=ConstantRoller(1), bypass_qualification=True)
    # Result may be a survival failure but NOT an enlistment failure
    if isinstance(result, GenerationFailure):
        assert "enlist" not in result.reason.lower()


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
    # SmartRoller(10, 5): 2D6=10 passes all checks; 1D6=5 → material idx=4 → "Explorer's Society"
    # 7 terms, rank=0, material_dm=0 → 3 cash rolls then material rolls with roll=5
    result = generate_career_character(SCOUT_CAREER, roller=SmartRoller(10, 5))
    assert isinstance(result, Character)
    material_benefits = [b for b in result.benefits if b.kind == "material"]
    assert any(b.material_name == "Explorer's Society" for b in material_benefits)


# --- T010a: Education < 8 restricts Scout skill rolls to 3 tables ---


def test_education_below_8_excludes_advanced_education_skills() -> None:
    # ConstantRoller(7): all stats=7, Education=7 < 8 → only 3 skill tables (no advanced education)
    # Skill rolls hit personal_development[0] = "+1 Str" (stat boost, no skill entry added)
    # "Advocate" is excluded: it also appears in background skills (always granted)
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
    roller = SequenceRoller([8, 8, 8, 8, 8, 8, 8, 1, 1, 1, 1, 4, 1], default=1)
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


def test_draft_character_roll_1_gives_navy() -> None:
    # DRAFT_TABLE[0] = "navy"; 1D6 roll=1 → index 0 → Navy career
    roller = SequenceRoller([1], default=10)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Navy"


def test_draft_character_sets_drafted_true() -> None:
    roller = SequenceRoller([3], default=10)
    result = draft_character(roller=roller)
    assert isinstance(result, Character)
    assert result.drafted is True


# --- T016: draft_character with unimplemented career ---


def test_draft_character_unimplemented_career_returns_failure() -> None:
    from unittest.mock import patch

    # Patch DRAFT_TABLE in generator so index 0 is "marine" (not in CAREER_REGISTRY)
    with patch("cetools.engine.generator.DRAFT_TABLE", ("marine",) + ("navy",) * 5):
        roller = SequenceRoller([1], default=10)
        result = draft_character(roller=roller)
    assert isinstance(result, GenerationFailure)
    assert "marine" in result.reason


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
