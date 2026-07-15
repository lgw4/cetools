from cetools.engine.worlds.tables import (
    GOVERNMENT_TYPES,
    HYDRO_DM_BY_ATMOSPHERE,
    LAW_LEVELS,
    POPULATION_DMS,
    STARPORT_BY_ROLL,
    TL_DM_BY_VALUE,
    TL_MINIMUMS,
    matches_conditions,
)


def test_starport_by_roll_matches_primary_starport_table():
    assert STARPORT_BY_ROLL == {
        2: "X",
        3: "E",
        4: "E",
        5: "D",
        6: "D",
        7: "C",
        8: "C",
        9: "B",
        10: "B",
        11: "A",
    }


def test_hydro_dm_by_atmosphere_matches_srd_dms():
    for atmosphere in (0, 1, 10, 11, 12):
        assert HYDRO_DM_BY_ATMOSPHERE[atmosphere] == -4
    assert HYDRO_DM_BY_ATMOSPHERE[14] == -2
    for atmosphere in (2, 3, 4, 5, 6, 7, 8, 9, 13, 15):
        assert HYDRO_DM_BY_ATMOSPHERE.get(atmosphere, 0) == 0


def _population_dm(size, atmosphere, hydrographics):
    values = {"size": size, "atmosphere": atmosphere, "hydrographics": hydrographics}
    return sum(
        rule["dm"] for rule in POPULATION_DMS if matches_conditions(rule["conditions"], values)
    )


def test_population_dms_reproduce_the_five_srd_rules():
    assert len(POPULATION_DMS) == 5
    assert _population_dm(size=2, atmosphere=7, hydrographics=5) == -1  # size <= 2
    assert _population_dm(size=5, atmosphere=10, hydrographics=5) == -2  # atmosphere >= A
    assert _population_dm(size=5, atmosphere=6, hydrographics=5) == 3  # atmosphere == 6
    assert _population_dm(size=5, atmosphere=5, hydrographics=5) == 1  # atmosphere == 5
    assert _population_dm(size=5, atmosphere=8, hydrographics=5) == 1  # atmosphere == 8
    assert _population_dm(size=5, atmosphere=2, hydrographics=0) == -2  # hydro 0 and atmo < 3
    assert _population_dm(size=5, atmosphere=6, hydrographics=5) == 3  # no stacking surprises
    assert _population_dm(size=8, atmosphere=7, hydrographics=5) == 0  # no rule applies


def _tl_minimum(atmosphere, hydrographics, population):
    values = {"atmosphere": atmosphere, "hydrographics": hydrographics, "population": population}
    applicable = [
        rule["min"] for rule in TL_MINIMUMS if matches_conditions(rule["conditions"], values)
    ]
    return max(applicable, default=0)


def test_tl_minimums_matches_appendix_c2():
    assert _tl_minimum(atmosphere=6, hydrographics=0, population=6) == 4
    assert _tl_minimum(atmosphere=6, hydrographics=10, population=8) == 4
    assert _tl_minimum(atmosphere=6, hydrographics=0, population=5) == 0
    assert _tl_minimum(atmosphere=4, hydrographics=5, population=5) == 5
    assert _tl_minimum(atmosphere=2, hydrographics=5, population=5) == 7
    assert _tl_minimum(atmosphere=11, hydrographics=5, population=5) == 7
    assert _tl_minimum(atmosphere=13, hydrographics=10, population=5) == 7
    assert _tl_minimum(atmosphere=13, hydrographics=5, population=5) == 0
    assert _tl_minimum(atmosphere=9, hydrographics=9, population=9) == 5


def test_tl_dm_by_value_matches_appendix_c1():
    assert TL_DM_BY_VALUE["starport"] == {"A": 6, "B": 4, "C": 2, "X": -4}
    assert TL_DM_BY_VALUE["size"] == {0: 2, 1: 2, 2: 1, 3: 1, 4: 1}
    assert TL_DM_BY_VALUE["atmosphere"] == {
        0: 1,
        1: 1,
        2: 1,
        3: 1,
        10: 1,
        11: 1,
        12: 1,
        13: 1,
        14: 1,
        15: 1,
    }
    assert TL_DM_BY_VALUE["hydrographics"] == {0: 1, 9: 1, 10: 2}
    assert TL_DM_BY_VALUE["population"] == {
        1: 1,
        2: 1,
        3: 1,
        4: 1,
        5: 1,
        9: 1,
        10: 2,
        11: 3,
        12: 4,
    }
    assert TL_DM_BY_VALUE["government"] == {0: 1, 5: 1, 7: 2, 13: -2, 14: -2}


def test_tl_dm_hydrographics_zero_entry_present():
    # An earlier §8 summary omitted this; Appendix C1 confirms it belongs.
    assert TL_DM_BY_VALUE["hydrographics"][0] == 1


def test_government_types_has_sixteen_srd_labels_in_order():
    assert len(GOVERNMENT_TYPES) == 16
    assert GOVERNMENT_TYPES[0] == "None"
    assert GOVERNMENT_TYPES[6] == "Captive Government"
    assert GOVERNMENT_TYPES[10] == "Charismatic Dictator"
    assert GOVERNMENT_TYPES[15] == "Totalitarian Oligarchy"


def test_law_levels_has_the_srd_descriptor_bands():
    assert LAW_LEVELS[0] == "No Law"
    assert LAW_LEVELS[1] == "Low Law"
    assert LAW_LEVELS[3] == "Low Law"
    assert LAW_LEVELS[4] == "Medium Law"
    assert LAW_LEVELS[6] == "Medium Law"
    assert LAW_LEVELS[7] == "High Law"
    assert LAW_LEVELS[9] == "High Law"
    assert LAW_LEVELS[10] == "Extreme Law"


def test_matches_conditions_requires_every_field_within_its_allowed_set():
    conditions = {"atmosphere": frozenset({0, 1}), "hydrographics": frozenset({0})}
    assert matches_conditions(conditions, {"atmosphere": 0, "hydrographics": 0}) is True
    assert matches_conditions(conditions, {"atmosphere": 2, "hydrographics": 0}) is False


def test_matches_conditions_is_vacuously_true_for_no_conditions():
    assert matches_conditions({}, {"anything": 1}) is True
