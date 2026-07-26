import pytest

from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import (
    AmmoFit,
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    FittingFit,
    ScreenFit,
    ShipDesign,
    SoftwareFit,
    TurretFit,
    build_ship,
    dump_design,
    load_design,
    loads_design,
)
from cetools.engine.ships.description import render_description
from cetools.engine.ships.generator import generate_ship

_EXAMPLES = "specs/010-starship-generator/examples"
_GOLDEN_FILES = (
    f"{_EXAMPLES}/free-trader.toml",
    f"{_EXAMPLES}/scout-courier.toml",
    f"{_EXAMPLES}/warship.toml",
    f"{_EXAMPLES}/fighter.toml",
    f"{_EXAMPLES}/heavy-cruiser.toml",
)


@pytest.mark.parametrize("path", _GOLDEN_FILES)
def test_golden_designs_round_trip_losslessly(path):
    design = load_design(path)
    assert loads_design(dump_design(design)) == design


@pytest.mark.parametrize("path", _GOLDEN_FILES)
def test_golden_ships_round_trip_through_dump_and_build(path):
    ship = build_ship(load_design(path))
    rebuilt = build_ship(loads_design(dump_design(ship.design)))
    assert rebuilt == ship


@pytest.mark.parametrize("path", _GOLDEN_FILES)
def test_load_design_agrees_with_loads_design(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    assert load_design(path) == loads_design(text)


def test_manually_constructed_design_round_trips():
    design = ShipDesign(
        name="Test Ship",
        hull_tons=200,
        configuration=Configuration.STREAMLINED,
        jump_code="A",
        maneuver_code="A",
        power_code="A",
        jump_distance=1,
        computer=ComputerFit(
            model=2,
            jump_control=True,
            hardened=True,
            software=(SoftwareFit(name="fire_control", level=1),),
        ),
        electronics="advanced",
        staterooms=3,
        low_berths=1,
        emergency_low_berths=1,
        armor=(ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=10, options=("reflec",)),),
        fittings=(FittingFit(kind="armory"),),
        turrets=(TurretFit(mount="double", weapons=("pulse_laser", "sandcaster")),),
        passengers_high=2,
        passengers_middle=3,
        standard_design=True,
    )
    assert loads_design(dump_design(design)) == design


def test_loads_design_rejects_malformed_toml():
    with pytest.raises(ValueError, match="malformed TOML"):
        loads_design("not valid toml [[[")


def test_loads_design_rejects_missing_hull_tons():
    with pytest.raises(ValueError, match="hull_tons"):
        loads_design('name = "Ship"')


def test_loads_design_rejects_an_unknown_top_level_key():
    with pytest.raises(ValueError, match="unknown key"):
        loads_design("hull_tons = 200\nbogus = 1")


def test_loads_design_rejects_an_unknown_section_key():
    with pytest.raises(ValueError, match="unknown key"):
        loads_design('hull_tons = 200\n\n[drives]\nbogus = "A"')


def test_loads_design_rejects_a_wrong_value_type():
    with pytest.raises(ValueError, match="must be an integer"):
        loads_design('hull_tons = "200"')


def test_loads_design_rejects_an_unknown_enum_string():
    with pytest.raises(ValueError, match="unknown configuration"):
        loads_design('hull_tons = 200\nconfiguration = "invisible"')


def test_loads_design_rejects_an_unknown_armor_type():
    with pytest.raises(ValueError, match="unknown armor.type"):
        loads_design('hull_tons = 200\n\n[[armor]]\ntype = "wood"\npercent = 5')


def test_a_well_formed_but_rules_illegal_design_loads_cleanly():
    # 150 tons is not a tabulated hull size, but that is build_ship's problem,
    # not loads_design's (FR-015).
    design = loads_design('hull_tons = 150\n\n[drives]\njump = "A"\npower = "A"')
    assert design.hull_tons == 150
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        build_ship(design)


def test_loads_design_accepts_a_7_percent_armor_layer():
    # The 5%-increment rule is build_ship's job, not loads_design's (FR-015;
    # contracts/design-schema.md "Rules enforced at load").
    design = loads_design('hull_tons = 200\n\n[[armor]]\ntype = "titanium_steel"\npercent = 7')
    assert design.armor[0].percent == 7
    with pytest.raises(ValueError, match="armor must be added in 5% increments"):
        build_ship(design)


def test_loads_design_accepts_power_weeks_1_on_a_starship():
    # The >= 2 (starship) / >= 1 (small craft) floor is build_ship's job, not
    # loads_design's (FR-015; contracts/design-schema.md "Rules enforced at load").
    design = loads_design('hull_tons = 200\n\n[drives]\njump = "A"\npower = "A"\npower_weeks = 1')
    assert design.power_weeks == 1
    with pytest.raises(ValueError, match="power_weeks must be >= 2 for a starship"):
        build_ship(design)


# --- US3: small craft cockpit I/O (research.md Part K) ---


@pytest.mark.parametrize("cockpit", ["1_man", "2_man"])
def test_cockpit_round_trips_for_both_srd_cockpits(cockpit):
    design = ShipDesign(
        hull_tons=40, maneuver_code="sB", power_code="sG", bridge=False, cockpit=cockpit
    )
    assert loads_design(dump_design(design)) == design


def test_loads_design_rejects_an_unknown_cockpit():
    with pytest.raises(ValueError, match="unknown cockpit"):
        loads_design(
            'hull_tons = 40\n\n[drives]\nmaneuver = "sB"\npower = "sG"\n\n'
            '[bridge]\ncockpit = "3_man"'
        )


def test_loads_design_rejects_a_bridge_and_cockpit_conflict():
    with pytest.raises(ValueError, match="cannot specify both cockpit and present"):
        loads_design(
            'hull_tons = 40\n\n[drives]\nmaneuver = "sB"\npower = "sG"\n\n'
            '[bridge]\npresent = true\ncockpit = "1_man"'
        )


def test_a_small_craft_carrying_a_jump_drive_loads_cleanly():
    # The jump drive is a small-craft rules violation, not a shape error
    # (FR-015): loads_design accepts it and build_ship rejects it.
    design = loads_design(
        'hull_tons = 40\n\n[drives]\njump = "sB"\nmaneuver = "sB"\npower = "sG"\n\n'
        '[bridge]\ncockpit = "1_man"'
    )
    assert design.jump_code == "sB"
    with pytest.raises(ValueError, match="small craft cannot mount a jump drive"):
        build_ship(design)


# --- US4: bays and screens I/O (research.md Part H) ---


def test_bays_and_screens_round_trip():
    design = ShipDesign(
        hull_tons=1000,
        jump_code="E",
        maneuver_code="E",
        power_code="E",
        bays=(BayFit(kind="particle"),),
        screens=(ScreenFit(kind="meson_screen"),),
    )
    assert loads_design(dump_design(design)) == design


def test_loads_design_rejects_an_unknown_bay_kind():
    with pytest.raises(ValueError, match="unknown bay kind"):
        loads_design('hull_tons = 1000\n\n[[bays]]\nkind = "torpedo"')


def test_loads_design_rejects_an_unknown_screen_kind():
    with pytest.raises(ValueError, match="unknown screen kind"):
        loads_design('hull_tons = 1000\n\n[[screens]]\nkind = "force_field"')


def test_a_bay_on_a_small_craft_hull_loads_cleanly():
    # A bay on a small craft is a rules violation (FR-020), not a shape error:
    # loads_design accepts it and build_ship rejects it.
    design = loads_design(
        'hull_tons = 40\n\n[drives]\nmaneuver = "sB"\npower = "sG"\n\n'
        '[bridge]\ncockpit = "1_man"\n\n[[bays]]\nkind = "particle"'
    )
    assert design.bays == (BayFit(kind="particle"),)
    with pytest.raises(ValueError, match="small craft cannot mount a weapon bay"):
        build_ship(design)


# --- T093: schema sections no golden fixture exercised (FR-010, FR-023, SC-008) ---


def test_loads_design_parses_both_ammunition_forms():
    design = loads_design(
        'hull_tons = 200\n\n[drives]\njump = "A"\npower = "A"\n\n'
        "[[turrets]]\n"
        'mount = "double"\n'
        'weapons = ["missile_rack", "sandcaster"]\n'
        "ammo = [\n"
        '  { kind = "sand_barrels", count = 20 },\n'
        '  { kind = "missile", type = "smart", count = 24 },\n'
        "]\n"
    )

    assert design.turrets[0].ammo == (
        AmmoFit(kind="sand_barrels", count=20),
        AmmoFit(kind="missile", type="smart", count=24),
    )


def test_ammunition_round_trips_losslessly():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        turrets=(
            TurretFit(
                mount="double",
                weapons=("missile_rack", "sandcaster"),
                ammo=(
                    AmmoFit(kind="missile", type="nuclear", count=12),
                    AmmoFit(kind="sand_barrels", count=40),
                ),
            ),
        ),
    )
    assert loads_design(dump_design(design)) == design
    ship = build_ship(design)
    assert build_ship(loads_design(dump_design(ship.design))) == ship


def test_dump_design_emits_every_ammunition_key():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        turrets=(
            TurretFit(
                mount="single",
                weapons=("missile_rack",),
                ammo=(AmmoFit(kind="missile", type="standard", count=12),),
            ),
        ),
    )
    text = dump_design(design)
    assert 'kind = "missile"' in text
    assert 'type = "standard"' in text
    assert "count = 12" in text


def test_a_non_default_power_weeks_round_trips():
    design = ShipDesign(hull_tons=200, jump_code="A", power_code="A", power_weeks=8)
    text = dump_design(design)
    assert "power_weeks = 8" in text
    assert loads_design(text) == design


def test_a_default_power_weeks_is_omitted_from_the_dump():
    starship = ShipDesign(hull_tons=200, jump_code="A", power_code="A")
    assert "power_weeks" not in dump_design(starship)

    small_craft = ShipDesign(
        hull_tons=40, maneuver_code="sB", power_code="sG", bridge=False, cockpit="1_man"
    )
    assert "power_weeks" not in dump_design(small_craft)


def test_a_fitting_quantity_and_vehicle_tons_round_trip():
    design = ShipDesign(
        hull_tons=200,
        jump_code="A",
        power_code="A",
        fittings=(
            FittingFit(kind="armory", quantity=3),
            FittingFit(kind="vehicle_hangar", vehicle_tons=13),
        ),
    )
    text = dump_design(design)
    assert "quantity = 3" in text
    assert "vehicle_tons = 13" in text
    assert loads_design(text) == design


def test_a_single_quantity_fitting_omits_the_quantity_key():
    design = ShipDesign(
        hull_tons=200, jump_code="A", power_code="A", fittings=(FittingFit(kind="armory"),)
    )
    assert "quantity" not in dump_design(design)


# --- T032: `purpose` and `tech_level` (011 contracts/design-schema.md) -----


def _describable(**overrides) -> ShipDesign:
    fields = dict(name="Beowulf", hull_tons=200, jump_code="A", power_code="A")
    fields.update(overrides)
    return ShipDesign(**fields)


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"purpose": "a fast courier"},
        {"tech_level": 11},
        {"purpose": "a fast courier", "tech_level": 11},
    ],
    ids=["neither", "purpose", "tech_level", "both"],
)
def test_the_new_design_keys_round_trip_losslessly(overrides):  # FR-033
    design = _describable(**overrides)
    assert loads_design(dump_design(design)) == design


def test_dump_design_omits_an_unset_new_key():
    text = dump_design(_describable())
    assert "purpose" not in text
    assert "tech_level" not in text


def test_dump_design_emits_the_new_keys_in_canonical_order():
    text = dump_design(_describable(purpose="a fast courier", tech_level=11))
    keys = [line.split(" =")[0] for line in text.splitlines() if " = " in line]
    assert keys[:4] == ["name", "purpose", "hull_tons", "tech_level"]


def test_a_purpose_containing_a_quote_or_a_backslash_round_trips():
    design = _describable(purpose='a "subsidized" merchant \\ hauling mail')
    assert loads_design(dump_design(design)) == design


def test_loads_design_rejects_a_non_string_purpose():
    with pytest.raises(ValueError, match="purpose must be a string"):
        loads_design("hull_tons = 200\npurpose = 7\n")


def test_loads_design_rejects_a_non_integer_tech_level():
    with pytest.raises(ValueError, match="tech_level must be an integer"):
        loads_design('hull_tons = 200\ntech_level = "11"\n')


def test_loads_design_rejects_a_boolean_tech_level():
    with pytest.raises(ValueError, match="tech_level must be an integer"):
        loads_design("hull_tons = 200\ntech_level = true\n")


def test_a_misspelled_new_key_still_fails_as_an_unknown_key():  # FR-033
    with pytest.raises(ValueError, match="unknown key\\(s\\) in design"):
        loads_design('hull_tons = 200\npurspose = "a fast courier"\n')


# --- T055: the same rejection reached through a hand-authored file ---------


@pytest.mark.parametrize(
    "purpose",
    ['"a fast trader."', '"a trader "', '"""a trader\nof repute"""'],
    ids=["trailing period", "trailing space", "line break"],
)
def test_loads_design_rejects_a_purpose_the_paragraph_cannot_carry(purpose):
    with pytest.raises(ValueError, match="purpose"):
        loads_design(f"hull_tons = 200\npurpose = {purpose}\n")


def test_loads_design_rejects_a_name_the_heading_cannot_carry():
    with pytest.raises(ValueError, match="name"):
        loads_design('hull_tons = 200\nname = "Beowulf "\n')


def test_a_blank_name_round_trips_and_still_means_no_name():  # FR-029b
    design = _describable(name="")
    assert loads_design(dump_design(design)) == design


# --- T011 (US1): a generated ship's name survives a dump/load round trip -----


def test_a_generated_ships_name_survives_dump_load_and_build():
    # Asserted through `loads_design`, not against the emitted TOML text: the
    # guarantee FR-013 makes is that the name round trips, and matching a
    # `name = "..."` substring would additionally pin dump_design's quoting and
    # break on the first catalogue name needing an escape. That the key reaches
    # the file at all is the CLI contract's concern, pinned in test_cli.py.
    ship = generate_ship(RandomRolls.seeded(42))
    reloaded = loads_design(dump_design(ship.design))

    assert reloaded.name == ship.design.name
    assert ship.design.name in render_description(build_ship(reloaded))


# --- T094: FR-021 schema-invalid load errors (design-schema.md "Rules enforced at load") ---


def test_loads_design_rejects_a_section_that_is_not_a_table():
    with pytest.raises(ValueError, match="must be a table"):
        loads_design("hull_tons = 200\ndrives = 5")


def test_loads_design_rejects_a_non_string_drive_code():
    with pytest.raises(ValueError, match="must be a string"):
        loads_design("hull_tons = 200\n\n[drives]\njump = 5")


def test_loads_design_rejects_a_non_boolean_bridge_present():
    with pytest.raises(ValueError, match="must be a boolean"):
        loads_design('hull_tons = 200\n\n[bridge]\npresent = "yes"')


def test_loads_design_rejects_a_computer_without_a_model():
    with pytest.raises(ValueError, match="requires 'model'"):
        loads_design("hull_tons = 200\n\n[computer]\nhardened = true")


def test_loads_design_rejects_software_without_a_name():
    with pytest.raises(ValueError, match="entry requires 'name'"):
        loads_design("hull_tons = 200\n\n[computer]\nmodel = 1\nsoftware = [{ level = 1 }]")


def test_loads_design_rejects_software_without_a_level():
    with pytest.raises(ValueError, match="entry requires 'level'"):
        loads_design('hull_tons = 200\n\n[computer]\nmodel = 1\nsoftware = [{ name = "evade" }]')


def test_loads_design_rejects_armor_without_a_type():
    with pytest.raises(ValueError, match="entry requires 'type'"):
        loads_design("hull_tons = 200\n\n[[armor]]\npercent = 5")


def test_loads_design_rejects_armor_without_a_percent():
    with pytest.raises(ValueError, match="entry requires 'percent'"):
        loads_design('hull_tons = 200\n\n[[armor]]\ntype = "titanium_steel"')


def test_loads_design_rejects_a_fitting_without_a_kind():
    with pytest.raises(ValueError, match="entry requires 'kind'"):
        loads_design("hull_tons = 200\n\n[[fittings]]\nquantity = 2")


def test_loads_design_rejects_a_non_integer_vehicle_tons():
    with pytest.raises(ValueError, match="must be an integer"):
        loads_design(
            'hull_tons = 200\n\n[[fittings]]\nkind = "vehicle_hangar"\nvehicle_tons = "13"'
        )


def test_loads_design_rejects_a_turret_without_a_mount():
    with pytest.raises(ValueError, match="entry requires 'mount'"):
        loads_design('hull_tons = 200\n\n[[turrets]]\nweapons = ["pulse_laser"]')


def test_loads_design_rejects_ammunition_without_a_kind():
    with pytest.raises(ValueError, match="entry requires 'kind'"):
        loads_design(
            'hull_tons = 200\n\n[[turrets]]\nmount = "single"\n'
            'weapons = ["missile_rack"]\nammo = [{ count = 12 }]'
        )


def test_loads_design_rejects_ammunition_without_a_count():
    with pytest.raises(ValueError, match="entry requires 'count'"):
        loads_design(
            'hull_tons = 200\n\n[[turrets]]\nmount = "single"\n'
            'weapons = ["missile_rack"]\nammo = [{ kind = "sand_barrels" }]'
        )


def test_loads_design_rejects_an_unknown_ammunition_key():
    with pytest.raises(ValueError, match="unknown key"):
        loads_design(
            'hull_tons = 200\n\n[[turrets]]\nmount = "single"\n'
            'weapons = ["missile_rack"]\nammo = [{ kind = "sand_barrels", count = 1, bogus = 2 }]'
        )


def test_loads_design_rejects_a_bay_without_a_kind():
    with pytest.raises(ValueError, match="entry requires 'kind'"):
        loads_design("hull_tons = 1000\n\n[[bays]]\n")


def test_loads_design_rejects_a_screen_without_a_kind():
    with pytest.raises(ValueError, match="entry requires 'kind'"):
        loads_design("hull_tons = 1000\n\n[[screens]]\n")


def test_loads_design_rejects_a_non_string_enum_value():
    with pytest.raises(ValueError, match="must be a string"):
        loads_design("hull_tons = 200\nconfiguration = 5")
