import pytest

from cetools.engine.ships import (
    ArmorFit,
    ArmorType,
    ComputerFit,
    Configuration,
    FittingFit,
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
