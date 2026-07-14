import dataclasses
import random
from collections import Counter

import pytest

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.rolls import RandomRolls, RollName
from cetools.engine.training import apply_entry, roll_skill
from conftest import scripted

# A career whose four Skills and Training tables have no entries in common, so
# the skill that comes back names the table it came from.
_TAGGED_CAREER = dataclasses.replace(
    NAVY_CAREER,
    personal_development=("PD",) * 6,
    service_skills=("SERVICE",) * 6,
    specialist_skills=("SPECIALIST",) * 6,
    advanced_education=("ADVANCED",) * 6,
)

_EDU_8 = {"Education": 8}  # opens the Advanced Education table


# --- Choosing a table ---


@pytest.mark.parametrize(
    ("index", "table"),
    [(0, "PD"), (1, "SERVICE"), (2, "SPECIALIST"), (3, "ADVANCED")],
)
def test_skill_table_is_chosen_by_index_not_by_a_die(index: int, table: str) -> None:
    # The SRD says to *choose* a Skills and Training table, so cetools picks one
    # uniformly rather than rolling a die and taking it modulo the table count.
    # Each table is addressed by its position, with no die in between.
    training = roll_skill(
        _TAGGED_CAREER,
        dict(_EDU_8),
        {},
        scripted(choices={RollName.SKILL_TABLE: index}),
    )
    assert training.entry == table


def test_skill_table_selection_is_uniform_across_all_four_tables() -> None:
    # Regression: the table used to be picked with (1D6 - 1) % len(tables). With
    # Advanced Education in play there are four tables, so a d6 modulo 4 gave
    # 0,1,2,3,0,1 — Personal Development and Service Skills came up twice as
    # often as Specialist and Advanced Education. Every table must be equally
    # likely.
    rolls = RandomRolls(random.Random(20260713))
    counts = Counter(
        roll_skill(_TAGGED_CAREER, dict(_EDU_8), {}, rolls).entry for _ in range(4000)
    )
    assert set(counts) == {"PD", "SERVICE", "SPECIALIST", "ADVANCED"}
    for table, count in counts.items():
        assert 850 <= count <= 1150, f"{table} came up {count} times in 4000, expected ~1000"


def test_skill_table_selection_covers_three_tables_below_education_8() -> None:
    # Without Advanced Education there are only three tables, and all three must
    # be reachable.
    rolls = RandomRolls(random.Random(20260713))
    counts = Counter(
        roll_skill(_TAGGED_CAREER, {"Education": 7}, {}, rolls).entry for _ in range(1200)
    )
    assert set(counts) == {"PD", "SERVICE", "SPECIALIST"}


def test_rolling_on_the_chosen_table_uses_a_real_d6() -> None:
    # Navy's Specialist table (index 2), 4th entry.
    training = roll_skill(
        NAVY_CAREER,
        dict(_EDU_8),
        {},
        scripted(choices={RollName.SKILL_TABLE: 2}, d6={RollName.SKILL_ENTRY: 4}),
    )
    assert training.entry == NAVY_CAREER.specialist_skills[3]


# --- Applying an entry ---
# SRD: "If you gain a skill as a result and you do not already have levels in
# that skill, take it at level 1. If you already have the skill, increase your
# skill by one level." Basic training is the exception that grants level 0.


def test_entry_grants_an_unheld_skill_at_level_1() -> None:
    _, skills = apply_entry("Gravitics", {}, {})
    assert skills["Gravitics"] == 1


def test_entry_increments_a_level_zero_skill_to_1() -> None:
    # Basic training and background skills grant level 0; a roll increases it.
    _, skills = apply_entry("Comms", {}, {"Comms": 0})
    assert skills["Comms"] == 1


def test_entry_increments_a_held_skill_by_one_level() -> None:
    _, skills = apply_entry("Comms", {}, {"Comms": 2})
    assert skills["Comms"] == 3


def test_entry_applies_a_stat_boost_instead_of_granting_a_skill() -> None:
    characteristics, skills = apply_entry("+1 Str", {"Strength": 7}, {})
    assert characteristics["Strength"] == 8
    assert skills == {}


def test_entry_caps_a_boosted_stat_at_33() -> None:
    characteristics, _ = apply_entry("+1 Str", {"Strength": 33}, {})
    assert characteristics["Strength"] == 33


def test_entry_does_not_mutate_its_arguments() -> None:
    characteristics = {"Strength": 7}
    skills = {"Comms": 0}
    apply_entry("+1 Str", characteristics, skills)
    apply_entry("Comms", characteristics, skills)
    assert characteristics == {"Strength": 7}
    assert skills == {"Comms": 0}
