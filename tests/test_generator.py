import dataclasses

import pytest

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import DRAFT, RANDOM, generate
from cetools.engine.models import STAT_NAMES, Cash, Character, GenerationFailure
from cetools.engine.rolls import RollName, ScriptedRolls
from cetools.engine.rules import SRD
from conftest import scripted

_rolls = scripted  # every check passes; see tests/conftest.py


# --- Check helper ---
# The 2D6 + DM >= target rule now lives on the Rolls seam; its tests are in
# tests/test_rolls.py. What remains here is the generator's own DM lookup, which
# is exercised end-to-end by the qualification and survival tests below.


# --- Enlistment ---


def test_enlistment_failure_returns_generation_failure() -> None:
    # Only SRD rules roll for enlistment at all, so only they can fail it.
    result = generate(NAVY_CAREER, _rolls(checks={RollName.QUALIFICATION: False}), rules=SRD)
    assert isinstance(result, GenerationFailure)
    assert result.exit_code == 1
    assert "enlist" in result.reason.lower() or "navy" in result.reason.lower()


def test_enlistment_pass_returns_character() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)


# --- UPP ---


def test_character_upp_is_six_pseudohex_chars() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert len(result.upp) == 6
    assert "I" not in result.upp
    assert "O" not in result.upp


# --- Name generation (US2) ---


def test_generated_character_has_non_empty_two_word_name() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.name
    assert len(result.name.split(" ")) >= 2


# --- Survival failure ---


def test_survival_fail_returns_character_with_mishap() -> None:
    result = generate(NAVY_CAREER, _rolls(checks={RollName.SURVIVAL: False}))
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert result.terms[-1].survived is False


def test_mishap_ended_character_still_rolls_psionics() -> None:
    # A dishonorable discharge (mishap 4) strips benefits, yet psionics is still
    # rolled on the sole return path. Psi 9 gives PsiDM +1, and the talent checks
    # are scripted highest-DM-first: Telepathy and Clairvoyance land, the rest do
    # not. A skipped psionics step would leave psi_strength 0 and fail this test.
    result = generate(
        NAVY_CAREER,
        rolls=_rolls(
            checks={
                RollName.SURVIVAL: False,
                RollName.PSI_GATE: True,
                RollName.PSI_TALENT: [True, True, False, False, False],
            },
            two_d6={RollName.PSI_STRENGTH: 9},
            d6={RollName.MISHAP: 4},
        ),
    )
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert result.mishap.discharge_type == "dishonorable"
    assert result.benefits == []
    assert result.psi_strength == 9
    assert result.talents == {"Telepathy": 0, "Clairvoyance": 0}


def test_gate_failure_yields_non_psionic_character() -> None:
    # Minimal pair with the test above: same dishonorable mishap, but the
    # eligibility gate fails, so the character is non-psionic even though
    # generation ran through the psionics step.
    result = generate(
        NAVY_CAREER,
        rolls=_rolls(
            checks={RollName.SURVIVAL: False, RollName.PSI_GATE: False},
            two_d6={RollName.PSI_STRENGTH: 9},
            d6={RollName.MISHAP: 4},
        ),
    )
    assert isinstance(result, Character)
    assert result.psi_strength == 0
    assert result.talents == {}


# --- T010: one integration test per SURVIVAL_MISHAPS_TABLE roll ---


def _mishap_character(mishap: int, injury: int | None = None) -> Character:
    """A Navy character whose first term ends in the given mishap-table roll."""
    d6 = {RollName.MISHAP: mishap}
    if injury is not None:
        d6[RollName.INJURY] = injury
    result = generate(NAVY_CAREER, rolls=_rolls(checks={RollName.SURVIVAL: False}, d6=d6))
    assert isinstance(result, Character)
    return result


def test_mishap_roll_1_injury_no_discharge() -> None:
    # Mishap 1 takes two injury rolls and uses the lower; both land on injury row
    # 6, "no permanent effect".
    result = _mishap_character(mishap=1, injury=6)
    assert result.mishap.roll == 1
    assert result.mishap.discharge_type == "none"
    assert result.mishap.imprisoned is False
    assert result.mishap.injury_reductions == {}
    assert result.mishap.injury_crisis is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_2_honorable_discharge() -> None:
    result = _mishap_character(mishap=2)
    assert result.mishap.roll == 2
    assert result.mishap.discharge_type == "honorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_3_honorable_discharge_with_legal_debt() -> None:
    result = _mishap_character(mishap=3)
    assert result.mishap.roll == 3
    assert result.mishap.discharge_type == "honorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 10_000
    assert result.age == 20


def test_mishap_roll_4_dishonorable_discharge_not_imprisoned() -> None:
    result = _mishap_character(mishap=4)
    assert result.mishap.roll == 4
    assert result.mishap.discharge_type == "dishonorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_5_dishonorable_discharge_imprisoned() -> None:
    # Outcome 5 adds an extra 4 years for imprisonment on top of the mishap
    # term's usual +2 (research.md D9): age == 18 + 2 + 4 == 24.
    result = _mishap_character(mishap=5)
    assert result.mishap.roll == 5
    assert result.mishap.discharge_type == "dishonorable"
    assert result.mishap.imprisoned is True
    assert result.debt == 0
    assert result.age == 24


def test_mishap_roll_6_medical_discharge_with_injury() -> None:
    # Mishap 6 takes a single injury roll; row 6 is "no permanent effect".
    result = _mishap_character(mishap=6, injury=6)
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
    result = generate(
        DRAFT,
        rolls=_rolls(
            checks={RollName.SURVIVAL: False},
            d6={RollName.DRAFT: 5, RollName.MISHAP: 2},
        ),
    )
    assert isinstance(result, Character)
    assert result.mishap is not None


# --- 7-term cap ---


def test_seven_term_cap_voluntary_musterout() -> None:
    # Re-enlistment of 10 passes Navy's target of 5 every term but is never a
    # natural 12, so the career ends by voluntary muster-out at the 7-term cap.
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.terms_served == 7


# --- Natural 12 at term 7 forces term 8 ---


def test_natural_12_at_term_7_forces_term_8() -> None:
    # SRD rules honour the natural 12; HOUSE rules hold the cap (tested above).
    result = generate(NAVY_CAREER, _rolls(two_d6={RollName.REENLISTMENT: 12}), rules=SRD)
    assert isinstance(result, Character)
    assert result.terms_served == 8


# --- Basic training ---


def test_first_term_basic_training_grants_all_six_service_skills() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    for skill_name in NAVY_CAREER.service_skills:
        assert (
            skill_name in result.skills
        ), f"Service skill {skill_name!r} missing from character after basic training"


# --- Skills non-empty ---


def test_character_has_non_empty_skills() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert len(result.skills) > 0


# --- Aging ---


@pytest.mark.parametrize(
    ("aging", "reenlistment", "dexterity", "endurance", "intelligence"),
    [
        ([4], 10, 12, 12, 12),  # term 4: 4-4 = 0   -> Str-1
        ([3], 10, 11, 12, 12),  # term 4: 3-4 = -1  -> Str-1, Dex-1
        ([2], 10, 11, 11, 12),  # term 4: 2-4 = -2  -> Str/Dex/End -1
        ([12, 2], 10, 11, 11, 12),  # term 5: 2-5 = -3  -> Str-2, Dex-1, End-1
        ([12, 12, 2], 10, 10, 11, 12),  # term 6: 2-6 = -4  -> Str-2, Dex-2, End-1
        ([12, 12, 12, 2], 10, 10, 10, 12),  # term 7: 2-7 = -5  -> Str/Dex/End -2
        ([12, 12, 12, 12, 2], 12, 10, 10, 11),  # term 8: 2-8 = -6  -> and Int-1
    ],
    ids=["0", "-1", "-2", "-3", "-4", "-5", "-6"],
)
def test_aging_ladder_reduces_characteristics(
    aging: list[int],
    reenlistment: int,
    dexterity: int,
    endurance: int,
    intelligence: int,
) -> None:
    # Ageing starts once age reaches 34, i.e. at the end of term 4, and the rung
    # of the ladder is (2D6 - terms_served). Every characteristic starts at 12;
    # ageing is the only thing that touches Dexterity, Endurance and Intelligence
    # under this script (skill rolls only ever grant "+1 Str", so Strength is not
    # asserted on here). A 2D6 of 12 in the earlier terms reduces nothing.
    #
    # The last rung is only reachable in a 8th term: 2D6 bottoms out at 2, and
    # 2 - 7 is only -5. A natural 12 on re-enlistment forces that extra term.
    result = generate(
        NAVY_CAREER,
        rolls=_rolls(
            two_d6={
                RollName.CHARACTERISTIC: 12,
                RollName.AGING: aging,
                RollName.REENLISTMENT: reenlistment,
            }
        ),
        rules=SRD,
    )
    assert isinstance(result, Character)
    assert result.characteristics["Dexterity"] == dexterity
    assert result.characteristics["Endurance"] == endurance
    assert result.characteristics["Intelligence"] == intelligence


def test_aging_check_triggers_at_term_4_or_later() -> None:
    # Aging starts once age reaches 34, i.e. from term 4. With a 2D6 of 10 the
    # aging roll (10 - terms_served) never drops below 1, so nothing is reduced —
    # this confirms the aging step runs without disturbing the character.
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 4
    assert result.age >= 34


# --- Pension ---


def test_pension_present_at_5_or_more_terms() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 5
    assert result.pension is not None
    assert result.pension > 0


def test_pension_amount_for_seven_terms() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.terms_served == 7
    assert result.pension == 14000


# --- Cash roll cap ---


def test_cash_roll_cap_at_3() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    cash_benefits = [b for b in result.benefits if isinstance(b, Cash)]
    assert len(cash_benefits) <= 3


# --- Rank bonuses on mustering out ---


def test_rank_bonus_muster_rolls_applied() -> None:
    # Every check passing carries the character to rank 6 (Commodore), which is
    # worth +3 muster rolls on top of one per term.
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.rank == 6
    expected_total = result.terms_served + 3  # O6 bonus = 3
    assert len(result.benefits) == expected_total


# --- Benefits non-empty ---


def test_character_has_non_empty_benefits() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert len(result.benefits) > 0


# --- terms_served >= 1 ---


def test_successful_character_served_at_least_one_term() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 1


# --- Skill rolls per term ---


def _failed_commission_navy() -> ScriptedRolls:
    # Commission fails, so neither commission nor advancement is received and two
    # skill rolls must follow. Each picks the Service Skills table (index 1) and
    # rolls its first entry, "Comms". Re-enlistment of 1 ends the career after
    # one term.
    return _rolls(
        checks={RollName.COMMISSION: False},
        two_d6={RollName.CHARACTERISTIC: 8, RollName.REENLISTMENT: 1},
        choices={RollName.SKILL_TABLE: 1},
        d6={RollName.SKILL_ENTRY: 1},
    )


def test_failed_commission_grants_two_skill_rolls() -> None:
    # Comms is level 0 after basic training; two skill rolls push it to level 2.
    # With only 1 roll it would stay at 1.
    result = generate(NAVY_CAREER, _failed_commission_navy())
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.rank == 0
    assert result.skills.get("Comms") == 2, "failed commission should not reduce skill rolls to 1"


def test_per_term_skill_rolls_recorded_in_term_history() -> None:
    result = generate(NAVY_CAREER, _failed_commission_navy())
    assert isinstance(result, Character)
    term = result.terms[0]
    # 6 from basic training + 2 from skill rolls
    assert len(term.skills_gained) == 8
    # "Comms" appears once in basic training and twice from the two skill rolls
    assert term.skills_gained.count("Comms") == 3


# --- Skill table selection (end to end) ---

# A career whose four Skills and Training tables have no entries in common, so
# the skill that comes back names the table it came from.


# --- Rank bonus skill levels ---


def test_rank_bonus_skills_granted_at_level_1() -> None:
    # Every skill roll lands on personal_development[0] = "+1 Str", a stat boost
    # rather than a skill, so Zero-G (rank 0) and Tactics (rank 3) can only have
    # come from rank bonuses — and must start at level 1, not 0.
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.skills.get("Zero-G") == 1, "rank-0 bonus should grant Zero-G-1"
    assert result.skills.get("Tactics") == 1, "rank-3 bonus should grant Tactics-1"


# --- Extensibility (US3 preview) ---


def test_generate_character_accepts_any_career_without_navy_hardcoding() -> None:
    stub_career = dataclasses.replace(NAVY_CAREER, name="Scout")
    result = generate(stub_career, _rolls())
    assert isinstance(result, (Character, GenerationFailure))


# --- Skill levels from a Skills and Training roll (end to end) ---
# SRD: "If you gain a skill as a result and you do not already have levels in
# that skill, take it at level 1. If you already have the skill, increase your
# skill by one level." Basic training is the exception that grants level 0.


def test_skill_rolled_from_a_table_is_granted_at_level_1_end_to_end() -> None:
    # Gravitics is Navy's first Specialist skill (table index 2) and is not in the
    # service skills a Navy character gets from basic training, so a roll on it is
    # the character's first level in it: level 1, not 0.
    result = generate(
        NAVY_CAREER,
        rolls=_rolls(
            choices={RollName.SKILL_TABLE: 2},
            d6={RollName.SKILL_ENTRY: 1},
            two_d6={RollName.REENLISTMENT: 1},  # one term, so exactly one roll lands
        ),
    )
    assert isinstance(result, Character)
    assert "Gravitics" not in NAVY_CAREER.service_skills
    assert result.skills["Gravitics"] == 1


# --- HOUSE rules: you get the career you asked for ---


def test_house_rules_reroll_characteristics_until_the_career_qualifies() -> None:
    # First set of six characteristics is all 2s (Intelligence 2 < 6, fails);
    # the second is all 8s and qualifies. The character is built from the second.
    result = generate(SCOUT_CAREER, _rolls(two_d6={RollName.CHARACTERISTIC: [2] * 6 + [8] * 6}))
    assert isinstance(result, Character)
    assert (
        result.characteristics[SCOUT_CAREER.qualification_stat]
        >= SCOUT_CAREER.qualification_target
    )


def test_house_rules_keep_rerolling_until_qualified() -> None:
    # Three failing sets of characteristics (Intelligence 3 < 6), then a passing
    # one. Every stat coming back as 8 — the fourth block — is only possible if
    # the loop discarded the first three. Re-enlistment of 1 ends the career after
    # one term, before ageing can touch anything.
    result = generate(
        SCOUT_CAREER,
        _rolls(
            two_d6={
                RollName.CHARACTERISTIC: [3] * 18 + [8] * 6,
                RollName.REENLISTMENT: 1,
            }
        ),
    )
    assert isinstance(result, Character)
    # Intelligence and Education are untouched by this career's skill rolls, which
    # only ever grant "+1 Str". An 8 in them is the fourth block: the third would
    # have left a 3.
    assert result.characteristics["Intelligence"] == 8
    assert result.characteristics["Education"] == 8


def test_house_rules_never_fail_enlistment() -> None:
    # The qualification check is scripted to fail, but HOUSE rules never make it:
    # characteristics are rerolled until the career accepts them. Survival then
    # fails, which resolves via the mishap table rather than a GenerationFailure.
    result = generate(
        NAVY_CAREER,
        _rolls(checks={RollName.QUALIFICATION: False, RollName.SURVIVAL: False}),
    )
    assert isinstance(result, Character)


def test_house_rules_hold_the_seven_term_cap_against_a_natural_12() -> None:
    # A natural 12 on re-enlistment would force an eighth term under SRD rules.
    # HOUSE rules hold the cap: the character musters out at seven.
    result = generate(NAVY_CAREER, _rolls(two_d6={RollName.REENLISTMENT: 12}))
    assert isinstance(result, Character)
    assert result.terms_served == 7


def test_scripted_characteristics_are_taken_in_stat_order() -> None:
    # Re-enlistment of 1 ends the career after one term, so nothing has boosted or
    # aged the characteristics away from what was rolled.
    result = generate(
        NAVY_CAREER,
        _rolls(
            two_d6={
                RollName.CHARACTERISTIC: [10, 10, 8, 12, 7, 9],
                RollName.REENLISTMENT: 1,
            },
            choices={RollName.SKILL_TABLE: 1},  # a skill, not a "+1 Str" boost
        ),
    )
    assert isinstance(result, Character)
    assert result.characteristics["Intelligence"] == 12
    assert result.characteristics["Education"] == 7
    assert result.characteristics["Social Standing"] == 9


def test_drafted_defaults_to_false_for_a_chosen_career() -> None:
    result = generate(NAVY_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.drafted is False


# --- T010: generate_career_character with Scout ---


def test_generate_career_character_returns_character() -> None:
    result = generate(SCOUT_CAREER, _rolls())
    assert isinstance(result, Character)


def test_generate_career_character_intelligence_at_least_6() -> None:
    result = generate(SCOUT_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.characteristics["Intelligence"] >= 6


def test_generate_career_character_piloting_at_level_1() -> None:
    # rank-0 bonus grants Piloting+1 before basic training; basic training skips setting it to 0
    result = generate(SCOUT_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.skills.get("Piloting", 0) >= 1


def test_generate_career_character_two_skill_rolls_per_term() -> None:
    # Scout has no commission/advancement → always 2 skill rolls per term
    result = generate(SCOUT_CAREER, _rolls())
    assert isinstance(result, Character)
    for i, term in enumerate(result.terms):
        non_bt = term.skills_gained if i > 0 else term.skills_gained[6:]
        assert len(non_bt) == 2, f"Term {i + 1} expected 2 skill rolls, got {len(non_bt)}"


# --- T010a: Education < 8 restricts Scout skill rolls to 3 tables ---


def test_education_below_8_excludes_advanced_education_skills() -> None:
    # Education 7 (< 8) leaves only 3 skill tables — no Advanced Education.
    # Navigation and Tactics live only in that table, so they must never appear.
    result = generate(SCOUT_CAREER, rolls=_rolls(two_d6={RollName.CHARACTERISTIC: 7}))
    assert isinstance(result, Character)
    exclusively_advanced = {"Navigation", "Tactics"}
    for skill in exclusively_advanced:
        assert (
            skill not in result.skills
        ), f"{skill!r} must not appear when Edu<8 (advanced education excluded)"


def test_education_8_or_above_can_access_advanced_education() -> None:
    # Education 10 (>= 8) opens the 4th table, index 3: advanced_education, whose
    # 4th entry is "Medicine".
    result = generate(
        SCOUT_CAREER,
        rolls=_rolls(
            choices={RollName.SKILL_TABLE: 3},
            d6={RollName.SKILL_ENTRY: 4},
        ),
    )
    assert isinstance(result, Character)
    assert "Medicine" in result.skills


# --- T010b: single-term Scout muster out ---


def test_single_term_scout_muster_out() -> None:
    # Re-enlistment of 4 misses Scout's target of 6, so the career ends after one
    # term: 1 term + rank-0 bonus (0) = a single benefit roll.
    result = generate(
        SCOUT_CAREER,
        rolls=_rolls(two_d6={RollName.CHARACTERISTIC: 8, RollName.REENLISTMENT: 4}),
    )
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.skills.get("Piloting", 0) >= 1
    term = result.terms[0]
    assert len(term.skills_gained) == 8  # 6 basic training + 2 skill rolls
    assert len(term.skills_gained[6:]) == 2
    assert len(result.benefits) == 1


# --- T015: draft_character ---


def test_draft_character_roll_5_gives_scout() -> None:
    # DRAFT_TABLE[4] = "scout"; a draft roll of 5 -> index 4.
    result = generate(DRAFT, _rolls(d6={RollName.DRAFT: 5}))
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career.name == "Scout"


def test_draft_character_roll_1_gives_aerospace() -> None:
    # DRAFT_TABLE[0] = "aerospace system defense"; a draft roll of 1 -> index 0.
    result = generate(DRAFT, _rolls(d6={RollName.DRAFT: 1}))
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career.name == "Aerospace System Defense"


def test_draft_character_sets_drafted_true() -> None:
    result = generate(DRAFT, _rolls(d6={RollName.DRAFT: 3}))
    assert isinstance(result, Character)
    assert result.drafted is True


def test_draft_character_roll_2_gives_marine() -> None:
    # DRAFT_TABLE[1] = "marine"; a draft roll of 2 -> index 1.
    result = generate(DRAFT, _rolls(d6={RollName.DRAFT: 2}))
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career.name == "Marine"


# --- The draft can no longer miss ---
# DRAFT_TABLE holds Career objects, not names, so "the draft assigned a career
# cetools has not implemented" is now unrepresentable rather than merely untested.
# The old test for it monkeypatched a bare string into the table.


def test_every_draft_roll_yields_a_character() -> None:
    for roll in range(1, 7):
        result = generate(DRAFT, _rolls(d6={RollName.DRAFT: roll}))
        assert isinstance(result, Character), f"draft roll {roll} did not produce a character"
        assert result.drafted is True


# --- T017: benefits/pension/debt matrix after 5+ completed terms (US3) ---

_SCOUT_PRESET = {
    "Strength": 10,
    "Dexterity": 10,
    "Endurance": 10,
    "Intelligence": 10,
    "Education": 10,
    "Social Standing": 10,
}


def _generate_scout_mishap_after_five_terms(mishap: int, injury: int | None = None) -> Character:
    # Five terms survived, then the sixth ends in the given mishap.
    d6 = {RollName.MISHAP: mishap}
    if injury is not None:
        d6[RollName.INJURY] = injury
    result = generate(
        SCOUT_CAREER,
        rolls=_rolls(checks={RollName.SURVIVAL: [True] * 5 + [False]}, d6=d6),
    )
    assert isinstance(result, Character)
    return result


def test_mishap_outcome_1_preserves_benefits_and_pension_after_five_terms() -> None:
    # Mishap 1 takes two injury rolls; both land on row 6, "no permanent effect".
    result = _generate_scout_mishap_after_five_terms(mishap=1, injury=6)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


def test_mishap_outcome_2_preserves_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=2)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


def test_mishap_outcome_3_preserves_benefits_and_pension_with_legal_debt() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=3)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 10_000


def test_mishap_outcome_4_forfeits_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=4)
    assert result.terms_served == 5
    assert result.benefits == []
    assert result.pension is None


def test_mishap_outcome_5_forfeits_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=5)
    assert result.terms_served == 5
    assert result.benefits == []
    assert result.pension is None


def test_mishap_outcome_6_preserves_benefits_and_pension_after_five_terms() -> None:
    # Mishap 6 takes a single injury roll; row 6 is "no permanent effect".
    result = _generate_scout_mishap_after_five_terms(mishap=6, injury=6)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


# --- T019: mishap during a character's very first term (edge case) ---


def _generate_scout_first_term_mishap(mishap: int, injury: int | None = None) -> Character:
    d6 = {RollName.MISHAP: mishap}
    if injury is not None:
        d6[RollName.INJURY] = injury
    result = generate(
        SCOUT_CAREER,
        rolls=_rolls(checks={RollName.SURVIVAL: False}, d6=d6),
    )
    assert isinstance(result, Character)
    return result


@pytest.mark.parametrize(
    ("mishap", "injury"),
    [(1, 6), (2, None), (3, None), (4, None), (5, None), (6, 6)],
    ids=["outcome1", "outcome2", "outcome3", "outcome4", "outcome5", "outcome6"],
)
def test_first_term_mishap_yields_no_benefits_or_pension(mishap: int, injury: int | None) -> None:
    result = _generate_scout_first_term_mishap(mishap=mishap, injury=injury)
    assert result.terms_served == 0
    assert result.benefits == []
    assert result.pension is None


# --- T011: two skill rolls per term recorded in term history ---


def test_two_skill_rolls_per_term_in_term_history() -> None:
    result = generate(SCOUT_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 2
    # Term 1: 6 basic training entries + 2 skill roll entries
    assert len(result.terms[0].skills_gained) == 8
    # All subsequent terms: exactly 2 skill roll entries each
    for term in result.terms[1:]:
        assert len(term.skills_gained) == 2


def test_generate_character_grants_background_skills() -> None:
    # Education 10 → 4 background skills, each drawn at index 0: homeworld Animals,
    # Broker; education Admin, Advocate. None of these are Scout service, rank, or
    # skill-roll outputs under this script, so they can only have come from
    # background granting.
    result = generate(SCOUT_CAREER, _rolls(two_d6={RollName.CHARACTERISTIC: 10}))
    assert isinstance(result, Character)
    for skill in ("Animals", "Broker", "Admin", "Advocate"):
        assert skill in result.skills
    assert result.skills["Broker"] == 0


def test_srd_rules_skip_enlistment_for_a_career_without_qualification() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # The qualification check would fail, but a career with no qualification must
    # never run it — so no enlistment failure, even under SRD rules.
    result = generate(no_qual, _rolls(checks={RollName.QUALIFICATION: False}), rules=SRD)
    assert isinstance(result, Character)


def test_srd_rules_gate_a_career_that_has_a_qualification() -> None:
    result = generate(NAVY_CAREER, _rolls(checks={RollName.QUALIFICATION: False}), rules=SRD)
    assert isinstance(result, GenerationFailure)
    assert "enlistment failed" in result.reason


def test_house_rules_do_not_loop_for_a_career_without_qualification() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # Every stat rolls a 1. Navy would reroll for ever chasing Intelligence 6+;
    # a career with no qualification accepts the first set and generation finishes.
    result = generate(no_qual, _rolls(two_d6={RollName.CHARACTERISTIC: 1}))
    assert isinstance(result, Character)
    assert set(result.characteristics.keys()) == set(STAT_NAMES)


def test_generate_career_character_drifter_no_qualification() -> None:
    from cetools.engine.careers.drifter import DRIFTER_CAREER

    result = generate(DRIFTER_CAREER, _rolls())
    assert isinstance(result, Character)
    assert result.career.name == "Drifter"


# --- Psionics ---


def test_generated_character_has_psionics() -> None:
    # The gate passes and the Psi roll is 11, so Psi = max(0, 11 - terms_served).
    # terms_served is on the result, so the relationship holds without predicting
    # the whole generation.
    result = generate(
        NAVY_CAREER,
        _rolls(
            checks={RollName.PSI_GATE: True},
            two_d6={RollName.PSI_STRENGTH: 11},
        ),
    )
    assert isinstance(result, Character)
    assert isinstance(result.talents, dict)
    assert result.psi_strength == max(0, 11 - result.terms_served)


# --- T018: random_career_character ---


def test_random_career_character_selects_career_by_first_roll() -> None:
    # Careers are offered in name order; index 8 is Drifter (which has no
    # qualification, so generation completes on the defaults).
    result = generate(RANDOM, _rolls(choices={RollName.CAREER: 8}))
    assert isinstance(result, Character)
    assert result.career.name == "Drifter"


def test_random_career_character_varies_with_first_roll() -> None:
    drifter = generate(RANDOM, _rolls(choices={RollName.CAREER: 8}))
    aerospace = generate(RANDOM, _rolls(choices={RollName.CAREER: 0}))
    assert aerospace.career.name == "Aerospace System Defense"
    assert drifter.career != aerospace.career


def test_random_career_is_not_drafted() -> None:
    # `drafted` is no longer a parameter — the assignment says so. A random career
    # is chosen, not drafted, and the old "drafted random" combination can no
    # longer be asked for.
    result = generate(RANDOM, _rolls(choices={RollName.CAREER: 8}))
    assert isinstance(result, Character)
    assert result.drafted is False
