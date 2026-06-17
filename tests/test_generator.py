import time

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate_character
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


# --- Performance ---


def test_generation_completes_under_2_seconds() -> None:
    start = time.perf_counter()
    generate_character(NAVY_CAREER)  # uses default RandomDiceRoller
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"generate_character took {elapsed:.3f}s (> 2s)"


# --- Extensibility (US3 preview) ---


def test_generate_character_accepts_any_career_without_navy_hardcoding() -> None:
    import dataclasses

    stub_career = dataclasses.replace(NAVY_CAREER, name="Scout")
    result = generate_character(stub_career, roller=SmartRoller(10, 1))
    assert isinstance(result, (Character, GenerationFailure))
