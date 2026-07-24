import pytest

from cetools.engine.ships import (
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
