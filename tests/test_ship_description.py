"""Tests for `engine/ships/description.py` -- the Universal Ship Description Format.

Every assertion here traces to a section of
`specs/011-universal-ship-format/contracts/description-format.md`, which is the
authority on the exact text. The fixture below is deliberately over-equipped so
that all sixteen sentence slots are exercised by one ship.
"""

import re
from dataclasses import replace
from pathlib import Path

import pytest

from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import (
    AmmoFit,
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    Crew,
    FittingFit,
    ScreenFit,
    ShipDesign,
    TurretFit,
    build_ship,
    generate_ship,
    load_design,
)
from cetools.engine.ships.description import _SLOTS, render_description
from cetools.engine.ships.prose import count, money, number, signed, tons

# --- Fixtures -------------------------------------------------------------

_TRIPLE = TurretFit(
    mount="triple",
    weapons=("missile_rack", "missile_rack", "pulse_laser"),
    ammo=(AmmoFit(kind="missile", count=40, type="smart"),),
)
_SINGLE = TurretFit(
    mount="single",
    weapons=("sandcaster",),
    ammo=(AmmoFit(kind="sand_barrels", count=20),),
)


def _equipped_design(**overrides) -> ShipDesign:
    """A 1,000-ton starship carrying something for every sentence slot."""
    fields = dict(
        name="Vigilant",
        hull_tons=1000,
        jump_code="E",
        maneuver_code="E",
        power_code="E",
        armor=(
            ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5, options=("stealth",)),
            ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),
        ),
        computer=ComputerFit(model=3, jump_control=True, hardened=True),
        electronics="basic_military",
        staterooms=20,
        low_berths=4,
        emergency_low_berths=2,
        fittings=(
            FittingFit(kind="fuel_processor", quantity=2),
            FittingFit(kind="luxuries", quantity=2),
            FittingFit(kind="detention_cell", quantity=4),
            FittingFit(kind="armory"),
            FittingFit(kind="vehicle_hangar", vehicle_tons=30),
        ),
        turrets=(_TRIPLE, _TRIPLE, _TRIPLE, _SINGLE),
        bays=(BayFit(kind="missile_bank"),),
        screens=(
            ScreenFit(kind="meson_screen"),
            ScreenFit(kind="nuclear_damper"),
            ScreenFit(kind="nuclear_damper"),
        ),
        passengers_middle=4,
    )
    fields.update(overrides)
    return ShipDesign(**fields)


def _simple_design(**overrides) -> ShipDesign:
    """A minimal but legal 200-ton starship, for one-variable cases."""
    fields = dict(
        name="Testbed",
        hull_tons=200,
        jump_code="A",
        maneuver_code="A",
        power_code="A",
    )
    fields.update(overrides)
    return ShipDesign(**fields)


def _equipped_ship():
    return build_ship(_equipped_design())


def _split(text: str) -> tuple[str, str]:
    """The heading line and the single paragraph of a rendered description."""
    heading, blank, paragraph = text.split("\n", 2)
    assert blank == ""
    return heading, paragraph


def _paragraph(ship) -> str:
    return _split(render_description(ship))[1]


def _clause(paragraph: str, opening: str) -> str:
    """The sentence of `paragraph` that starts with `opening`."""
    start = paragraph.index(opening)
    rest = paragraph[start:]
    return rest[: rest.index(".") + 1]


def _slot(ship, name: str) -> str | None:
    """One named sentence slot's own return value, `None` when it is omitted."""
    return {builder.__name__: builder for builder in _SLOTS}[name](ship)


# --- T014: overall shape (FR-001, FR-001a) --------------------------------


def test_description_is_a_heading_a_blank_line_and_one_paragraph():
    lines = render_description(_equipped_ship()).split("\n")

    assert len(lines) == 3
    assert lines[0].startswith("TL")
    assert lines[1] == ""
    assert lines[2]


def test_heading_names_the_tech_level_and_the_ship():
    ship = _equipped_ship()

    assert _split(render_description(ship))[0] == f"TL{ship.tech_level} Vigilant"


def test_paragraph_holds_no_newline_and_the_text_no_trailing_newline():
    text = render_description(_equipped_ship())

    assert "\n" not in _split(text)[1]
    assert not text.endswith("\n")


def test_sentences_are_separated_by_exactly_one_space():
    paragraph = _paragraph(_equipped_ship())

    assert "  " not in paragraph
    assert " ." not in paragraph
    assert " ," not in paragraph
    assert ". " in paragraph
    assert paragraph.endswith(".")


# --- T015: slot order (FR-004, SC-004) ------------------------------------

_SLOT_ORDER = (
    "_hull",
    "_drives",
    "_fuel",
    "_computer",
    "_sensors",
    "_quarters",
    "_hardpoints",
    "_weapons",
    "_screens",
    "_hangars",
    "_cargo",
    "_configuration",
    "_special_features",
    "_crew",
    "_passengers",
    "_cost",
)


def test_there_are_exactly_sixteen_slots_in_the_fr_004_order():
    assert tuple(slot.__name__ for slot in _SLOTS) == _SLOT_ORDER


def test_every_slot_renders_for_the_equipped_ship_in_slot_order():
    ship = _equipped_ship()
    paragraph = _paragraph(ship)

    positions = []
    for slot in _SLOTS:
        text = slot(ship)
        assert text is not None, f"{slot.__name__} was omitted for the equipped ship"
        assert text in paragraph
        positions.append(paragraph.index(text))

    assert positions == sorted(positions)
    assert len(set(positions)) == len(_SLOT_ORDER)


def test_a_slot_may_carry_more_than_one_sentence():
    """Slot 8 emits the weapons sentence plus one sentence per ammunition group,
    so a paragraph has sixteen slots but more than sixteen sentences."""
    sentences = [s for s in _paragraph(_equipped_ship()).split(". ") if s]

    assert len(sentences) > len(_SLOT_ORDER)


# --- T016: sentences 1-3 (FR-005, FR-006, FR-007, FR-007a) ----------------


def test_hull_sentence_states_tonnage_hull_and_structure():  # FR-005
    ship = _equipped_ship()

    assert (
        f"Using a 1000-ton hull ({ship.hull_points} Hull, "
        f"{ship.structure_points} Structure), the Vigilant is a starship."
    ) in _paragraph(ship)


def test_hull_sentence_uses_an_before_an_eight_hundred_ton_hull():
    design = _simple_design(hull_tons=800, jump_code="E", maneuver_code="E", power_code="E")

    assert "Using an 800-ton hull" in _paragraph(build_ship(design))


def test_drives_sentence_names_every_fitted_drive_and_the_performance():  # FR-006
    assert (
        "It mounts jump drive E, maneuver drive E and power plant E, "
        "giving a performance of Jump-1 and 1-G acceleration."
    ) in _paragraph(_equipped_ship())


def test_fuel_sentence_states_tankage_weeks_and_jumps():  # FR-007
    ship = _equipped_ship()
    tankage = ship.jump_fuel + ship.power_fuel

    assert (
        f"Fuel tankage of {tons(tankage)} tons supports the power plant "
        "for two weeks and one Jump-1 jump."
    ) in _paragraph(ship)


def test_fuel_sentence_keeps_a_zero_jump_clause():  # FR-007a
    ship = build_ship(_simple_design(jump_distance=0))

    assert "and zero Jump-1 jumps." in _paragraph(ship)


# --- T017: sentences 4-6 (FR-008, FR-009, FR-009a, FR-010, FR-030a) -------


@pytest.mark.parametrize(
    "jump_control,hardened,suffix",
    [
        (False, False, ""),
        (True, False, "/bis"),
        (False, True, "/fib"),
        (True, True, "/bis/fib"),
    ],
)
def test_computer_sentence_carries_the_option_suffixes(jump_control, hardened, suffix):  # FR-008
    design = _simple_design(
        computer=ComputerFit(model=2, jump_control=jump_control, hardened=hardened)
    )

    assert f"Adjacent to the bridge is a computer Model 2{suffix}." in _paragraph(
        build_ship(design)
    )


@pytest.mark.parametrize(
    "package,name,dm",
    [
        ("standard", "Standard", "-4"),
        ("basic_civilian", "Basic Civilian", "-2"),
        ("basic_military", "Basic Military", "+0"),
        ("advanced", "Advanced", "+1"),
        ("very_advanced", "Very Advanced", "+2"),
    ],
)
def test_sensors_sentence_names_the_package_and_signs_the_dm(package, name, dm):  # FR-009
    ship = build_ship(_simple_design(electronics=package))

    assert f"The ship is equipped with {name} sensors (DM{dm})." in _paragraph(ship)


def test_sensors_sentence_falls_back_to_standard():  # FR-009a, FR-030a
    ship = build_ship(_simple_design())

    assert ship.design.electronics is None
    assert "The ship is equipped with Standard sensors (DM-4)." in _paragraph(ship)


def test_quarters_sentence_distinguishes_the_three_kinds():  # FR-010
    assert (
        "There are 20 staterooms, four low berths and two emergency low berths."
    ) in _paragraph(_equipped_ship())


def test_quarters_sentence_agrees_in_number_for_a_single_berth():  # FR-023
    assert "There is one stateroom." in _paragraph(build_ship(_simple_design(staterooms=1)))


def test_quarters_sentence_uses_are_for_one_clause_above_one():
    assert "There are two low berths." in _paragraph(build_ship(_simple_design(low_berths=2)))


def test_quarters_sentence_uses_are_for_two_clauses_of_one():
    design = _simple_design(staterooms=1, emergency_low_berths=1)

    assert "There are one stateroom and one emergency low berth." in _paragraph(build_ship(design))


# --- T018: sentences 7-10 (FR-011, FR-012, FR-012a, FR-013, FR-014) -------


def test_hardpoint_sentence_reports_fire_control_tons_as_the_hardpoint_count():  # FR-011
    ship = _equipped_ship()

    assert ship.hardpoints == 10
    assert ("The ship has ten hardpoints and ten tons allocated to fire control.") in _paragraph(
        ship
    )


def test_weapons_sentence_puts_bays_before_turrets_and_groups_repeats():  # FR-012
    paragraph = _paragraph(_equipped_ship())

    assert (
        "Installed on the hardpoints are one missile bay, "
        "three triple turrets armed with missiles and a pulse laser "
        "and one single turret armed with a sandcaster."
    ) in paragraph
    assert paragraph.index("missile bay") < paragraph.index("triple turrets")


def test_ammunition_sentences_aggregate_by_kind_and_type_and_name_the_weapon():  # FR-012a
    paragraph = _paragraph(_equipped_ship())

    assert "120 smart missiles are carried as ammunition for the missile turrets." in paragraph
    assert "20 canisters are carried as ammunition for the sandcaster turret." in paragraph


def test_weapons_sentence_agrees_in_number_for_a_lone_system():
    design = _simple_design(turrets=(TurretFit(mount="single", weapons=("sandcaster",)),))

    assert (
        "Installed on the hardpoint is one single turret armed with a sandcaster."
    ) in _paragraph(build_ship(design))


def test_screens_sentence_states_the_total_then_the_groups():  # FR-013
    assert ("This ship has three screens: a meson screen and two nuclear dampers.") in _paragraph(
        _equipped_ship()
    )


def test_hangar_sentence_states_count_and_capacity_without_naming_the_craft():  # FR-014
    paragraph = _paragraph(_equipped_ship())

    assert "There is one small craft hangar holding 30 tons of small craft." in paragraph
    assert "vehicle" not in paragraph


def test_hangar_sentence_says_each_above_one():
    design = _simple_design(
        fittings=(FittingFit(kind="vehicle_hangar", quantity=2, vehicle_tons=20),)
    )

    assert (
        "There are two small craft hangars, each holding 20 tons of small craft."
    ) in _paragraph(build_ship(design))


def test_hangar_sentence_lists_entries_when_more_than_one_fitting():
    design = _simple_design(
        fittings=(
            FittingFit(kind="vehicle_hangar", vehicle_tons=20),
            FittingFit(kind="vehicle_hangar", quantity=2, vehicle_tons=10),
        )
    )

    assert (
        "There are three small craft hangars, one holding 20 tons of small craft "
        "and two holding ten tons of small craft."
    ) in _paragraph(build_ship(design))


# --- T019: sentences 11-13 (FR-015, FR-016, FR-016a, FR-016b, FR-017) -----


def test_cargo_sentence_states_the_capacity():  # FR-015
    ship = _equipped_ship()

    assert f"Cargo capacity is {tons(ship.cargo_tons)} tons." in _paragraph(ship)


def test_configuration_sentence_renders_two_layers_as_one_clause_and_one_rating():  # FR-016a
    paragraph = _paragraph(_equipped_ship())

    assert (
        "The hull is standard, armored with Titanium Steel and Crystaliron (6 points), "
        "and possesses a stealth coating."
    ) in paragraph
    assert paragraph.count("points)") == 1
    assert paragraph.count("armored with") == 1


def test_configuration_sentence_without_options():  # FR-016
    design = _simple_design(armor=(ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),))

    assert "The hull is standard, and is armored with Crystaliron (4 points)." in _paragraph(
        build_ship(design)
    )


def test_configuration_sentence_names_the_configuration():  # FR-016b
    design = _simple_design(configuration=Configuration.STREAMLINED)

    assert "The hull is streamlined," in _paragraph(build_ship(design))


def test_special_features_renders_the_fuel_processor_throughput():  # FR-017
    assert (
        "two tons of fuel processors (processes 40 tons of unrefined fuel "
        "into refined fuel per day)"
    ) in _paragraph(_equipped_ship())


def test_special_features_measures_a_counted_in_tons_fitting():  # FR-017
    assert "two tons of luxuries" in _paragraph(_equipped_ship())


def test_special_features_names_a_single_fitting_without_a_count():  # FR-017
    design = _simple_design(fittings=(FittingFit(kind="fuel_scoops"),))

    assert "Special features include fuel scoops." in _paragraph(build_ship(design))


def test_special_features_counts_a_repeated_fitting():  # FR-017
    assert "four detention cells" in _paragraph(_equipped_ship())


def test_special_features_excludes_the_hangar():
    features = _clause(_paragraph(_equipped_ship()), "Special features include")

    assert "hangar" not in features


# --- T020: sentences 14-16 (FR-018, FR-019, FR-019a, FR-020, FR-025) ------


def test_crew_sentence_breaks_down_in_table_order_omitting_zeroes():  # FR-018
    assert (
        "The ship requires a crew of 14: one pilot, one navigator, two engineers, "
        "five gunners, three screen operators, one medic and one steward."
    ) in _paragraph(_equipped_ship())


def test_crew_sentence_omits_a_zero_count_position():  # FR-018
    crew = _clause(_paragraph(build_ship(_simple_design())), "The ship requires a crew of")

    assert "gunner" not in crew
    assert "screen operator" not in crew
    assert "one pilot" in crew


def test_passenger_sentence_doubles_up_the_spare_staterooms():  # FR-019
    assert (
        "The ship can carry up to 12 additional passengers at double occupancy "
        "and four low passengers."
    ) in _paragraph(_equipped_ship())


def test_passenger_sentence_excludes_emergency_low_berths():  # FR-019a
    carry = _clause(_paragraph(_equipped_ship()), "The ship can carry up to")

    assert "emergency" not in carry


def test_cost_sentence_states_the_cost_and_the_build_time():  # FR-020, FR-025
    ship = _equipped_ship()

    assert (
        f"The ship costs MCr{money(ship.total_cost)} (including discounts and fees) "
        f"and takes {count(ship.build_weeks)} weeks to build."
    ) in _paragraph(ship)


# --- T020a: every numeric slot is classified (FR-022c) --------------------

# The complete inventory of numbers the sixteen sentences can print. A numeric
# slot added to `description.py` without an entry in `_SLOT_HELPERS` below
# fails `test_every_numeric_slot_is_classified`.
_NUMERIC_SLOTS = frozenset(
    {
        "hull displacement",
        "hull points",
        "structure points",
        "jump rating",
        "maneuver rating",
        "fuel tankage",
        "power weeks",
        "jump count",
        "computer model",
        "sensor dm",
        "staterooms",
        "low berths",
        "emergency low berths",
        "hardpoints",
        "fire control tons",
        "turret count",
        "bay count",
        "screen count",
        "hangar count",
        "hangar capacity",
        "ammunition count",
        "cargo tons",
        "armor points",
        "fitting quantity",
        "fitting tonnage",
        "crew total",
        "crew position count",
        "passenger count",
        "low passenger count",
        "cost",
        "build weeks",
        "tech level",
    }
)

# Each slot paired with the single `prose.py` helper that renders it, and with
# the value the equipped fixture puts in that slot. `signed` joins
# `count`/`tons`/`number`/`money` here because the sensor DM is the one numeric
# slot the SRD always prints with an explicit sign (FR-009).
_SLOT_HELPERS = {
    "hull displacement": (number, lambda s: s.hull_tons),
    "hull points": (number, lambda s: s.hull_points),
    "structure points": (number, lambda s: s.structure_points),
    "jump rating": (number, lambda s: s.jump_rating),
    "maneuver rating": (number, lambda s: s.maneuver_rating),
    "fuel tankage": (tons, lambda s: s.jump_fuel + s.power_fuel),
    "power weeks": (count, lambda s: s.design.power_weeks),
    "jump count": (count, lambda s: s.assumed_jump_distance // s.jump_rating),
    "computer model": (number, lambda s: s.design.computer.model),
    "sensor dm": (signed, lambda s: 0),
    "staterooms": (count, lambda s: s.design.staterooms),
    "low berths": (count, lambda s: s.design.low_berths),
    "emergency low berths": (count, lambda s: s.design.emergency_low_berths),
    "hardpoints": (count, lambda s: s.hardpoints),
    "fire control tons": (tons, lambda s: s.hardpoints),
    "turret count": (count, lambda s: 3),
    "bay count": (count, lambda s: len(s.design.bays)),
    "screen count": (count, lambda s: len(s.design.screens)),
    "hangar count": (count, lambda s: 1),
    "hangar capacity": (tons, lambda s: 30),
    "ammunition count": (count, lambda s: 120),
    "cargo tons": (tons, lambda s: s.cargo_tons),
    "armor points": (number, lambda s: s.armor_protection),
    "fitting quantity": (count, lambda s: 4),
    "fitting tonnage": (tons, lambda s: 2),
    "crew total": (count, lambda s: s.crew.total),
    "crew position count": (count, lambda s: s.crew.gunners),
    "passenger count": (count, lambda s: 12),
    "low passenger count": (count, lambda s: s.design.low_berths),
    "cost": (money, lambda s: s.total_cost),
    "build weeks": (count, lambda s: s.build_weeks),
    "tech level": (number, lambda s: s.tech_level),
}


def test_every_numeric_slot_is_classified():
    assert set(_SLOT_HELPERS) == set(_NUMERIC_SLOTS)
    assert {helper for helper, _ in _SLOT_HELPERS.values()} <= {count, tons, number, money, signed}


@pytest.mark.parametrize("slot", sorted(_NUMERIC_SLOTS))
def test_each_numeric_slot_renders_through_its_classified_helper(slot):
    ship = _equipped_ship()
    helper, value = _SLOT_HELPERS[slot]

    assert helper(value(ship)) in render_description(ship)


# --- T021: determinism (FR-003, SC-003) -----------------------------------


def test_equal_ships_render_byte_identically():
    first = build_ship(_equipped_design())
    second = build_ship(_equipped_design())

    assert first == second
    assert render_description(first) == render_description(second)


def test_description_never_mentions_a_seed():
    assert "seed" not in render_description(_equipped_ship()).lower()


# --- T033: purpose, name fallback and authored tech level ------------------


def _small_craft_design(**overrides) -> ShipDesign:
    """A minimal but legal 40-ton small craft."""
    fields = dict(
        name="Gig",
        hull_tons=40,
        maneuver_code="sB",
        power_code="sG",
        bridge=False,
        cockpit="1_man",
    )
    fields.update(overrides)
    return ShipDesign(**fields)


def test_an_authored_purpose_completes_the_first_sentence():  # FR-029
    purpose = "a subsidized merchant plying routes the mail contracts do not reach"
    ship = build_ship(_simple_design(purpose=purpose))

    assert f"the Testbed is {purpose}." in _paragraph(ship)


def test_the_renderer_supplies_the_first_sentence_period():  # FR-029
    ship = build_ship(_simple_design(purpose="a fast courier"))

    assert "the Testbed is a fast courier." in _paragraph(ship)
    assert "courier.." not in _paragraph(ship)


def test_a_starship_without_a_purpose_falls_back_to_its_hull_class():  # FR-029a
    ship = build_ship(_simple_design())

    assert ship.design.purpose is None
    assert "the Testbed is a starship." in _paragraph(ship)


def test_a_small_craft_without_a_purpose_falls_back_to_its_hull_class():  # FR-029a
    ship = build_ship(_small_craft_design())

    assert "the Gig is a small craft." in _paragraph(ship)


def test_a_small_craft_purpose_is_used_when_authored():  # FR-029
    ship = build_ship(_small_craft_design(purpose="a ship's boat"))

    assert "the Gig is a ship's boat." in _paragraph(ship)


def test_a_nameless_design_is_unnamed_ship_in_both_places():  # FR-029b
    heading, paragraph = _split(render_description(build_ship(_simple_design(name=None))))

    assert heading.endswith(" Unnamed Ship")
    assert "the Unnamed Ship is a starship." in paragraph


def test_an_authored_tech_level_above_the_derived_one_appears_unchanged():  # FR-028b
    derived = build_ship(_simple_design()).tech_level
    ship = build_ship(_simple_design(tech_level=derived + 7))

    assert ship.tech_level == derived + 7
    assert _split(render_description(ship))[0] == f"TL{derived + 7} Testbed"


def test_an_authored_tech_level_below_the_derived_one_appears_unchanged():  # FR-028b
    ship = build_ship(_simple_design(tech_level=3))

    assert _split(render_description(ship))[0] == "TL3 Testbed"


# --- T037: the checked-in fixture carrying both new keys -------------------

_SUBSIDIZED_MERCHANT = "specs/011-universal-ship-format/examples/subsidized-merchant.toml"


def test_the_subsidized_merchant_renders_its_authored_purpose_and_tech_level():
    ship = build_ship(load_design(_SUBSIDIZED_MERCHANT))
    heading, paragraph = _split(render_description(ship))

    assert heading == "TL11 Beowulf"
    assert (
        "the Beowulf is a subsidized merchant plying the routes an interstellar "
        "polity's mail contracts do not reach."
    ) in paragraph


def test_the_subsidized_merchant_changes_no_computed_value():  # FR-032
    merchant = build_ship(load_design(_SUBSIDIZED_MERCHANT))
    free_trader = build_ship(load_design("specs/010-starship-generator/examples/free-trader.toml"))

    assert merchant.tonnage_used == free_trader.tonnage_used
    assert merchant.cargo_tons == free_trader.cargo_tons
    assert merchant.crew.total == free_trader.crew.total
    assert merchant.total_cost == free_trader.total_cost
    assert merchant.build_weeks == free_trader.build_weeks


# --- T038: whole-sentence omission (FR-021, data-model.md section 6) -------
#
# `_simple_design()` carries no computer, no quarters, no weapon system, no
# screen and no fitting, so it exercises every omittable slot at once.


def test_no_computer_fitted_drops_the_computer_sentence():
    ship = build_ship(_simple_design())

    assert ship.design.computer is None
    assert _slot(ship, "_computer") is None
    assert "computer" not in _paragraph(ship)


def test_a_fitted_computer_restores_the_sentence():
    ship = build_ship(_simple_design(computer=ComputerFit(model=1)))

    assert _slot(ship, "_computer") is not None


def test_no_berths_of_any_kind_drops_the_quarters_sentence():  # FR-010a
    ship = build_ship(_simple_design())

    assert ship.design.staterooms == 0
    assert ship.design.low_berths == 0
    assert ship.design.emergency_low_berths == 0
    assert _slot(ship, "_quarters") is None
    assert "There is" not in _paragraph(ship)
    assert "stateroom" not in _paragraph(ship)


@pytest.mark.parametrize("field_name", ["staterooms", "low_berths", "emergency_low_berths"])
def test_any_one_kind_of_berth_restores_the_quarters_sentence(field_name):  # FR-010a
    ship = build_ship(_simple_design(**{field_name: 1}))

    assert _slot(ship, "_quarters") is not None


def test_no_turrets_and_no_bays_drops_the_weapons_sentence():  # FR-011a
    ship = build_ship(_simple_design())
    paragraph = _paragraph(ship)

    assert _slot(ship, "_weapons") is None
    assert "Installed on the" not in paragraph
    assert (
        "The ship has two hardpoints and two tons allocated to fire control, "
        "but has no weapons installed."
    ) in paragraph


def test_the_hardpoint_sentence_drops_its_no_weapons_clause_once_armed():  # FR-011a
    design = _simple_design(turrets=(TurretFit(mount="single", weapons=("sandcaster",)),))
    paragraph = _paragraph(build_ship(design))

    assert "but has no weapons installed" not in paragraph
    assert "The ship has two hardpoints and two tons allocated to fire control." in paragraph


def test_no_screens_drops_the_screens_sentence():
    ship = build_ship(_simple_design())

    assert _slot(ship, "_screens") is None
    assert "screen" not in _paragraph(ship)


def test_no_vehicle_sized_fitting_drops_the_hangar_sentence():
    ship = build_ship(_simple_design(fittings=(FittingFit(kind="armory"),)))

    assert _slot(ship, "_hangars") is None
    assert "hangar" not in _paragraph(ship)


def test_no_non_hangar_fitting_drops_the_special_features_sentence():  # FR-021
    design = _simple_design(fittings=(FittingFit(kind="vehicle_hangar", vehicle_tons=20),))
    paragraph = _paragraph(build_ship(design))

    assert _slot(build_ship(design), "_special_features") is None
    assert "Special features" not in paragraph
    assert "There is one small craft hangar holding 20 tons of small craft." in paragraph


def test_a_stripped_ship_omits_exactly_the_six_omittable_slots():  # FR-021
    ship = build_ship(_simple_design())

    omitted = [slot.__name__ for slot in _SLOTS if slot(ship) is None]

    assert omitted == [
        "_computer",
        "_quarters",
        "_weapons",
        "_screens",
        "_hangars",
        "_special_features",
    ]


# --- T039: clause-level omission (FR-006a, FR-007a, FR-016, FR-019b) ------


def test_no_maneuver_drive_drops_both_the_drive_and_performance_clauses():  # FR-006a
    ship = build_ship(_simple_design(maneuver_code=None))
    paragraph = _paragraph(ship)

    assert ship.design.maneuver_code is None
    assert "It mounts jump drive A and power plant A, giving a performance of Jump-1." in paragraph
    assert "maneuver" not in paragraph
    assert "acceleration" not in paragraph
    assert " and ." not in paragraph


def test_no_jump_fuel_keeps_the_jump_clause_at_zero():  # FR-007a
    ship = build_ship(_simple_design(jump_distance=0))

    assert ship.jump_fuel == 0
    assert (
        "Fuel tankage of two tons supports the power plant for two weeks " "and zero Jump-1 jumps."
    ) in _paragraph(ship)


def test_no_armor_states_so_rather_than_rendering_a_zero_rating():  # FR-016
    ship = build_ship(_simple_design())
    paragraph = _paragraph(ship)

    assert ship.armor_protection == 0
    assert "The hull is standard, and no additional armor has been installed." in paragraph
    assert "armored with" not in paragraph
    assert "0 points" not in paragraph


def test_neither_spare_staterooms_nor_low_berths_states_no_capacity():  # FR-019b
    ship = build_ship(_simple_design())

    assert _slot(ship, "_passengers") == "The ship cannot carry any additional passengers."


def test_staterooms_the_crew_fills_offer_no_passenger_capacity():  # FR-019, FR-019b
    ship = build_ship(_simple_design(staterooms=3))

    assert ship.crew.total == 3
    assert "The ship cannot carry any additional passengers." in _paragraph(ship)


def test_low_berths_alone_still_offer_passenger_capacity():  # FR-019
    ship = build_ship(_simple_design(low_berths=2))

    assert "The ship can carry up to two low passengers." in _paragraph(ship)


# --- T040: the remaining spec edge cases ----------------------------------


def test_zero_cargo_renders_as_a_word():  # SC-001, FR-021a
    ship = build_ship(_simple_design(staterooms=38))

    assert ship.cargo_tons == 0
    assert "Cargo capacity is zero tons." in _paragraph(ship)


def test_fractional_cargo_renders_in_digits():  # FR-022b
    ship = build_ship(load_design("specs/010-starship-generator/examples/fighter.toml"))

    # The accumulated float is 6.200000000000003; the sentence states 6.2.
    assert ship.cargo_tons != 6.2
    assert "Cargo capacity is 6.2 tons." in _paragraph(ship)


def test_a_crew_of_one_agrees_in_number():  # FR-022, FR-023
    # `build_ship` never derives a crew this small -- every powered hull needs
    # an engineer -- so the agreement is asserted against the renderer directly.
    lone = Crew(
        pilot=1, navigator=0, engineers=0, gunners=0, screen_operators=0, medic=0, stewards=0
    )
    ship = replace(build_ship(_simple_design()), crew=lone)

    assert _slot(ship, "_crew") == "The ship requires a crew of one: one pilot."


def test_a_fractional_cost_renders_at_full_precision():  # FR-025, FR-025a
    design = _simple_design(
        standard_design=True, staterooms=4, fittings=(FittingFit(kind="fuel_processor"),)
    )
    ship = build_ship(design)

    # The accumulated float is 29.744999999999997; the sentence states MCr29.745.
    assert ship.total_cost != 29.745
    assert "The ship costs MCr29.745 (including discounts and fees)" in _paragraph(ship)


def test_a_cost_carrying_a_float_artefact_is_not_rendered_verbatim():  # FR-025a
    ship = build_ship(_simple_design(standard_design=True))

    assert repr(ship.total_cost) == "27.900000000000002"
    assert "The ship costs MCr27.9 (including discounts and fees)" in _paragraph(ship)


def test_no_cost_is_rendered_in_scientific_notation_or_left_dangling():  # FR-025
    for design in (_equipped_design(), _simple_design(standard_design=True)):
        # `_clause` cuts at the first period, which a fractional cost carries,
        # so the closing sentence is matched whole instead.
        cost = re.search(r"The ship costs .*? to build\.", _paragraph(build_ship(design)))

        assert cost is not None
        assert re.match(r"The ship costs MCr\d{1,3}(,\d{3})*(\.\d+)? \(", cost.group())
        assert "e+" not in cost.group()
        assert "e-" not in cost.group()
        assert ". " not in cost.group()


# --- T041: the grammar sweep (FR-021a, SC-001) -----------------------------

_EXAMPLES = sorted(Path("specs/010-starship-generator/examples").glob("*.toml")) + sorted(
    Path("specs/011-universal-ship-format/examples").glob("*.toml")
)

_SEEDS = (1, 7, 42, 99, 12345)


def _swept_descriptions() -> list[tuple[str, str]]:
    """Every checked-in example plus a spread of generated ships, as
    `(label, rendered text)` pairs."""
    swept = [
        (str(path), render_description(build_ship(load_design(str(path))))) for path in _EXAMPLES
    ]
    for seed in _SEEDS:
        for small_craft in (False, True):
            ship = generate_ship(RandomRolls.seeded(seed), small_craft=small_craft)
            label = f"seed {seed}{' small craft' if small_craft else ''}"
            swept.append((label, render_description(ship)))
    return swept


_SWEPT = _swept_descriptions()

# `count(0)` and `tons(0)` render "zero", so scanning for the word finds every
# clause stating a quantity of zero -- and only those, since measured values
# render in digits (FR-022a) and a "0 Hull" rating is not a quantity.
_ZERO_IS_REQUIRED = ("Jump-", "Cargo capacity is zero tons.")


def _sentences(paragraph: str) -> list[str]:
    """The paragraph's sentences. A boundary is a period followed by a space,
    which no decimal, MCr figure or Model number can produce."""
    return re.split(r"(?<=\.) ", paragraph)


def test_the_sweep_covers_every_example_and_seed():
    assert len(_SWEPT) == len(_EXAMPLES) + 2 * len(_SEEDS)
    assert len(_EXAMPLES) >= 6


@pytest.mark.parametrize("label,text", _SWEPT, ids=[label for label, _ in _SWEPT])
def test_every_rendered_ship_is_one_heading_and_one_paragraph(label, text):
    lines = text.split("\n")

    assert len(lines) == 3
    assert re.fullmatch(r"TL\d+ .+", lines[0])
    assert lines[1] == ""
    assert "\n" not in lines[2]


@pytest.mark.parametrize("label,text", _SWEPT, ids=[label for label, _ in _SWEPT])
def test_every_paragraph_survives_its_omissions_grammatically(label, text):  # FR-021a
    paragraph = text.split("\n", 2)[2]

    assert "  " not in paragraph
    assert " ." not in paragraph
    assert " ," not in paragraph
    assert " and." not in paragraph
    assert ", ." not in paragraph
    assert "()" not in paragraph
    assert "None" not in paragraph
    assert ".." not in paragraph
    assert paragraph.endswith(".")


@pytest.mark.parametrize("label,text", _SWEPT, ids=[label for label, _ in _SWEPT])
def test_every_sentence_opens_and_closes_like_a_sentence(label, text):  # FR-021a
    for sentence in _sentences(text.split("\n", 2)[2]):
        assert sentence.endswith(".")
        # An ammunition sentence opens with its count, which is digits above ten
        # ("120 smart missiles are carried ..."), so a leading digit is as much a
        # sentence opening as a capital.
        assert sentence[0].isupper() or sentence[0].isdigit()


@pytest.mark.parametrize("label,text", _SWEPT, ids=[label for label, _ in _SWEPT])
def test_no_clause_states_a_quantity_of_zero_unbidden(label, text):  # FR-021a
    for sentence in _sentences(text.split("\n", 2)[2]):
        if "zero" not in sentence:
            continue
        assert any(required in sentence for required in _ZERO_IS_REQUIRED), sentence
