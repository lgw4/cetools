import dataclasses

import pytest

from cetools.engine.benefits import muster_out, roll_material_benefit
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.belter import BELTER_CAREER
from cetools.engine.careers.hunter import HUNTER_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scientist import SCIENTIST_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.models import STAT_NAMES, Cash, Item, Shares
from cetools.engine.rolls import RollName
from conftest import scripted

# --- Rank DM puts the last row of the material table in reach ---


def test_material_benefit_row_7_reachable_at_rank_5_plus() -> None:
    # rank 5 -> material_dm=1, so idx = clamp(roll + 1 - 1) = roll. A material
    # roll of 6 lands on idx 6 -> "Explorers' Society". Without the rank-5+ DM,
    # idx would clamp to 5 (High Passage), so this confirms row 7 is reachable.
    # terms_served=2 + rank-5 bonus (2) = 4 rolls: 3 cash (the cap), 1 material.
    result = muster_out(
        career=NAVY_CAREER,
        terms_served=2,
        rank=5,
        skills={},
        characteristics={},
        rolls=scripted(d6={RollName.CASH_BENEFIT: 6, RollName.MATERIAL_BENEFIT: 6}),
    )
    assert len(result.benefits) == 4
    material = [b for b in result.benefits if not isinstance(b, Cash)]
    assert any(
        b == Item("Explorers' Society") for b in material
    ), "rank 5+ DM should make material benefit row 7 (Explorers' Society) reachable"


def test_muster_out_grants_explorers_society_once_and_rerolls_repeat() -> None:
    # rank 5 -> material_dm=1, so idx = roll. Two material rolls: the first 6
    # grants "Explorers' Society"; the second 6 would repeat it, so the once-only
    # rule rerolls, and the 2 lands on "Weapon".
    result = muster_out(
        career=NAVY_CAREER,
        terms_served=3,
        rank=5,
        skills={},
        characteristics={},
        rolls=scripted(d6={RollName.MATERIAL_BENEFIT: [6, 6, 2]}),
    )
    assert len(result.benefits) == 5  # reroll must not add an extra roll (FR-008)
    material = [b.name for b in result.benefits if isinstance(b, Item)]
    assert material == ["Explorers' Society", "Weapon"]


# --- Cash DM from Gambling ---


def test_gambling_skill_grants_cash_dm_on_muster_out() -> None:
    # A cash roll of 5:
    #   without Gambling: idx = max(0, min(6, 5+0-1)) = 4 -> cash_benefits[4] = 20,000
    #   with Gambling:    idx = max(0, min(6, 5+1-1)) = 5 -> cash_benefits[5] = 50,000
    common = dict(
        career=NAVY_CAREER,
        terms_served=1,
        rank=0,
        characteristics={},
        rolls=scripted(d6={RollName.CASH_BENEFIT: 5}),
    )
    without_dm = muster_out(**common, skills={})
    with_dm = muster_out(**common, skills={"Gambling": 0})
    assert len(without_dm.benefits) == 1
    assert len(with_dm.benefits) == 1
    assert without_dm.benefits[0] == Cash(20000)
    assert with_dm.benefits[0] == Cash(50000)


# --- Once-only benefits: reroll on repeat ---


def test_roll_material_benefit_grants_explorers_society_when_not_yet_granted() -> None:
    # NAVY_CAREER.material_benefits[6] = "Explorers' Society". material_dm=1, so
    # idx = clamp(roll + 1 - 1) = roll; a roll of 6 -> idx 6.
    name = roll_material_benefit(
        NAVY_CAREER, 1, scripted(d6={RollName.MATERIAL_BENEFIT: 6}), set()
    )
    assert name == "Explorers' Society"


def test_roll_material_benefit_rerolls_once_when_already_granted() -> None:
    # First roll 6 -> "Explorers' Society", already granted, so it rerolls:
    # 3 -> idx 3 -> "Mid Passage".
    name = roll_material_benefit(
        NAVY_CAREER,
        1,
        scripted(d6={RollName.MATERIAL_BENEFIT: [6, 3]}),
        {"Explorers' Society"},
    )
    assert name == "Mid Passage"


def test_roll_material_benefit_rerolls_repeatedly_until_non_duplicate() -> None:
    # Three more 6s in a row (each still "Explorers' Society", already granted)
    # before a 2 finally lands on idx 2 -> "Weapon".
    name = roll_material_benefit(
        NAVY_CAREER,
        1,
        scripted(d6={RollName.MATERIAL_BENEFIT: [6, 6, 6, 2]}),
        {"Explorers' Society"},
    )
    assert name == "Weapon"


def test_roll_material_benefit_unaffected_for_career_without_explorers_society() -> None:
    # AEROSPACE_CAREER.material_benefits[6] = "+1 Soc" (no "Explorers' Society" entry
    # exists in this table at all), so the uniqueness check can never match —
    # behavior is identical to before this feature, even when `granted` already
    # contains that string. material_dm=1, so idx = clamp(6 + 1 - 1) = 6.
    name = roll_material_benefit(
        AEROSPACE_CAREER,
        1,
        scripted(d6={RollName.MATERIAL_BENEFIT: 6}),
        {"Explorers' Society"},
    )
    assert name == "+1 Soc"


def test_roll_material_benefit_grants_research_vessel_when_not_yet_granted() -> None:
    name = roll_material_benefit(
        SCIENTIST_CAREER, 1, scripted(d6={RollName.MATERIAL_BENEFIT: 6}), set()
    )
    assert name == "Research Vessel"


def test_roll_material_benefit_rerolls_research_vessel_when_already_granted() -> None:
    # First roll 6 -> "Research Vessel", already granted, so it rerolls:
    # 4 -> idx 4 -> "+1 Soc".
    name = roll_material_benefit(
        SCIENTIST_CAREER,
        1,
        scripted(d6={RollName.MATERIAL_BENEFIT: [6, 4]}),
        {"Research Vessel"},
    )
    assert name == "+1 Soc"


def test_roll_material_benefit_grants_courier_vessel_when_not_yet_granted() -> None:
    # SCOUT_CAREER.material_benefits has 6 entries; [5] = "Courier Vessel".
    # material_dm=1, roll 6 -> idx = clamp(6, 0, 5) = 5.
    name = roll_material_benefit(
        SCOUT_CAREER, 1, scripted(d6={RollName.MATERIAL_BENEFIT: 6}), set()
    )
    assert name == "Courier Vessel"


def test_roll_material_benefit_rerolls_courier_vessel_when_already_granted() -> None:
    name = roll_material_benefit(
        SCOUT_CAREER,
        1,
        scripted(d6={RollName.MATERIAL_BENEFIT: [6, 3]}),
        {"Courier Vessel"},
    )
    assert name == "Mid Passage"


def test_roll_material_benefit_terminates_with_fixed_script_on_granted_unique() -> None:
    # A material roll of 6 always lands on SCOUT_CAREER.material_benefits[5]
    # ("Courier Vessel"). With it already granted, the reroll loop would spin
    # forever without a cap; the fallback must return a non-duplicate benefit.
    name = roll_material_benefit(
        SCOUT_CAREER,
        1,
        scripted(d6={RollName.MATERIAL_BENEFIT: 6}),
        {"Courier Vessel"},
    )
    assert name != "Courier Vessel"
    assert name in SCOUT_CAREER.material_benefits


def test_roll_material_benefit_raises_when_no_eligible_benefit_remains() -> None:
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
        roll_material_benefit(degenerate, 0, scripted(), granted)


# --- Ship shares ---


def test_muster_out_ship_shares_rolls_quantity() -> None:
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
    # (3 cash, the cap, then 1 material). The material roll of 6 lands on idx 6 ->
    # "1D6 Ship Shares", whose quantity is then rolled separately.
    result = muster_out(
        ship_career,
        2,
        5,
        {},
        characteristics,
        scripted(
            d6={
                RollName.CASH_BENEFIT: 1,
                RollName.MATERIAL_BENEFIT: 6,
                RollName.SHIP_SHARES: 3,
            }
        ),
    )
    material = [b for b in result.benefits if not isinstance(b, Cash)]
    assert len(material) == 1
    assert material[0] == Shares(quantity=3)
    # ship shares do not touch characteristics
    assert all(value == 7 for value in result.characteristics.values())


def test_muster_out_hunter_ship_shares() -> None:
    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0 -> material_dm=0; terms=4 -> 4 rolls (3 cash, the cap, then 1
    # material). The material roll of 5 lands on idx 4 -> "1D6 Ship Shares".
    result = muster_out(
        HUNTER_CAREER,
        4,
        0,
        {},
        characteristics,
        scripted(
            d6={
                RollName.CASH_BENEFIT: 1,
                RollName.MATERIAL_BENEFIT: 5,
                RollName.SHIP_SHARES: 3,
            }
        ),
    )
    material = [b for b in result.benefits if not isinstance(b, Cash)]
    assert len(material) == 1
    assert material[0] == Shares(quantity=3)


def test_muster_out_belter_ship_shares() -> None:
    characteristics = {stat: 7 for stat in STAT_NAMES}
    result = muster_out(
        BELTER_CAREER,
        4,
        0,
        {},
        characteristics,
        scripted(
            d6={
                RollName.CASH_BENEFIT: 1,
                RollName.MATERIAL_BENEFIT: 5,
                RollName.SHIP_SHARES: 3,
            }
        ),
    )
    material = [b for b in result.benefits if not isinstance(b, Cash)]
    assert len(material) == 1
    assert material[0] == Shares(quantity=3)


# --- Cash ---


def test_muster_out_zero_cash_benefit() -> None:
    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0, terms=1 -> 1 roll (cash). A cash roll of 1 with no Gambling DM
    # -> idx 0 -> cash_benefits[0] == 0.
    result = muster_out(
        BARBARIAN_CAREER, 1, 0, {}, characteristics, scripted(d6={RollName.CASH_BENEFIT: 1})
    )
    cash = [b for b in result.benefits if isinstance(b, Cash)]
    assert len(cash) == 1
    assert cash[0] == Cash(0)


def test_scout_material_roll_5_gives_explorers_society() -> None:
    # rank 0 -> material_dm=0, so idx = clamp(roll + 0 - 1) = roll - 1. A material
    # roll of 5 lands on idx 4 -> SCOUT_CAREER.material_benefits[4] = "Explorers'
    # Society", confirming row 5 is reachable with no rank DM.
    # terms_served=4 + rank-0 bonus (0) = 4 rolls: 3 cash (the cap), 1 material.
    result = muster_out(
        career=SCOUT_CAREER,
        terms_served=4,
        rank=0,
        skills={},
        characteristics={},
        rolls=scripted(d6={RollName.CASH_BENEFIT: 5, RollName.MATERIAL_BENEFIT: 5}),
    )
    assert len(result.benefits) == 4
    material = [b for b in result.benefits if not isinstance(b, Cash)]
    assert any(b == Item("Explorers' Society") for b in material)


# --- The interface returns; it does not mutate ---


def test_muster_out_returns_boosted_characteristics_without_mutating() -> None:
    # NAVY_CAREER.material_benefits[1] = "+1 Edu": a material benefit that is a
    # stat boost. The caller's dict is left alone; the boost comes back on the
    # result.
    characteristics = {stat: 7 for stat in STAT_NAMES}
    result = muster_out(
        NAVY_CAREER,
        4,
        0,
        {},
        characteristics,
        scripted(d6={RollName.CASH_BENEFIT: 1, RollName.MATERIAL_BENEFIT: 2}),
    )
    assert result.characteristics["Education"] == 8
    assert characteristics["Education"] == 7, "muster_out must not mutate its argument"
