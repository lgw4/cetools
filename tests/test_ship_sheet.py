from cetools.engine.ships import (
    AmmoFit,
    Configuration,
    Crew,
    LineItem,
    Ship,
    ShipDesign,
    TurretFit,
    build_ship,
    load_design,
    render_sheet,
)

_EXAMPLES = "specs/010-starship-generator/examples"

_EMPTY_CREW = Crew(
    pilot=1, navigator=1, engineers=0, gunners=0, screen_operators=0, medic=0, stewards=0
)


def _ships():
    for name in ("free-trader", "scout-courier", "warship", "fighter", "heavy-cruiser"):
        yield build_ship(load_design(f"{_EXAMPLES}/{name}.toml"))


def test_render_sheet_includes_every_fr_022_section():
    ship = build_ship(load_design(f"{_EXAMPLES}/warship.toml"))
    sheet = render_sheet(ship)

    assert "Hull:" in sheet
    assert "Jump-" in sheet and "Maneuver-" in sheet and "Power-" in sheet
    assert "Fuel:" in sheet
    assert "assumes range" in sheet  # FR-006: the assumed jump distance
    assert "Computer:" in sheet
    assert "Software:" in sheet
    assert "Electronics:" in sheet
    assert "Crew:" in sheet
    assert "Quarters:" in sheet
    assert "Fittings:" in sheet
    assert "Armor:" in sheet
    assert "Armaments:" in sheet
    assert "Tonnage:" in sheet
    assert "Hull points:" in sheet
    assert "Structure points:" in sheet
    assert "Cost:" in sheet
    assert "Build time:" in sheet


def test_armor_line_includes_the_protection_figure():
    ship = build_ship(load_design(f"{_EXAMPLES}/warship.toml"))
    sheet = render_sheet(ship)
    assert "protection 4" in sheet


def test_render_sheet_is_total_for_every_golden_ship():
    for ship in _ships():
        render_sheet(ship)  # must not raise


def test_render_sheet_is_total_for_a_minimal_ship():
    design = ShipDesign(hull_tons=100, jump_code="A", power_code="A")
    render_sheet(build_ship(design))  # no computer, quarters, fittings, armor, turrets


def test_render_sheet_is_byte_identical_for_equal_ships():
    ship_a = build_ship(load_design(f"{_EXAMPLES}/free-trader.toml"))
    ship_b = build_ship(load_design(f"{_EXAMPLES}/free-trader.toml"))
    assert render_sheet(ship_a) == render_sheet(ship_b)


def test_render_sheet_never_mentions_a_seed():
    for ship in _ships():
        assert "seed" not in render_sheet(ship).lower()


# --- US3: small craft sheet (FR-022: cockpit in place of bridge, no jump lines) ---


def test_render_sheet_small_craft_has_a_cockpit_line():
    ship = build_ship(load_design(f"{_EXAMPLES}/fighter.toml"))
    sheet = render_sheet(ship)
    assert "Cockpit: 1_man" in sheet
    assert "Bridge:" not in sheet


def test_render_sheet_small_craft_has_no_jump_lines():
    ship = build_ship(load_design(f"{_EXAMPLES}/fighter.toml"))
    sheet = render_sheet(ship)
    assert "Jump-" not in sheet
    assert "jump" not in sheet.lower()


# --- US4: bays and screens (research.md Part H) ---


def test_render_sheet_shows_bays_and_screens_in_armaments():
    ship = build_ship(load_design(f"{_EXAMPLES}/heavy-cruiser.toml"))
    sheet = render_sheet(ship)
    assert "Armaments:" in sheet
    assert "particle bay" in sheet
    assert "meson_screen screen" in sheet


def test_render_sheet_shows_screen_operators_in_crew():
    ship = build_ship(load_design(f"{_EXAMPLES}/heavy-cruiser.toml"))
    sheet = render_sheet(ship)
    assert "screen operators 1" in sheet


# --- T077: sheet variant follows design.hull_class, not the cockpit/bridge field ---
#
# `build_ship` now rejects a hull_class/bridge-cockpit mismatch (T078), so these
# `Ship` instances are built by hand rather than via `build_ship`, to exercise
# `render_sheet`'s branching in isolation.


def test_render_sheet_shows_jump_lines_for_a_starship_carrying_a_cockpit_field():
    # A 200-ton hull is a STARSHIP by hull_tons alone, even though `cockpit` is
    # set here (an SRD-illegal combination render_sheet must not be fooled by).
    design = ShipDesign(
        hull_tons=200, jump_code="B", power_code="B", cockpit="1_man", bridge=False
    )
    ship = Ship(
        design=design,
        hull_tons=200,
        configuration=Configuration.STANDARD,
        jump_rating=2,
        maneuver_rating=0,
        power_rating=2,
        jump_fuel=40.0,
        assumed_jump_distance=2,
        power_fuel=2.0,
        tonnage_used=22.0,
        cargo_tons=178.0,
        hull_points=4,
        structure_points=4,
        armor_protection=0,
        hardpoints=2,
        hardpoints_used=0,
        crew=_EMPTY_CREW,
        total_cost=36.0,
        build_weeks=44,
        line_items=(LineItem(name="power plant B", tons=7, cost=16),),
    )
    sheet = render_sheet(ship)
    assert "Jump-2 (B)" in sheet
    assert "40t jump" in sheet


def test_render_sheet_omits_jump_lines_for_a_small_craft_carrying_a_bridge_field():
    # A 95-ton hull is SMALL_CRAFT by hull_tons alone, even though `bridge` is
    # set here (an SRD-illegal combination render_sheet must not be fooled by).
    design = ShipDesign(hull_tons=95, bridge=True, power_code="sJ")
    ship = Ship(
        design=design,
        hull_tons=95,
        configuration=Configuration.STANDARD,
        jump_rating=0,
        maneuver_rating=1,
        power_rating=3,
        jump_fuel=0.0,
        assumed_jump_distance=0,
        power_fuel=7.3,
        tonnage_used=30.0,
        cargo_tons=65.0,
        hull_points=1,
        structure_points=2,
        armor_protection=0,
        hardpoints=1,
        hardpoints_used=0,
        crew=_EMPTY_CREW,
        total_cost=20.0,
        build_weeks=35,
        line_items=(LineItem(name="power plant sJ", tons=25, cost=140),),
    )
    sheet = render_sheet(ship)
    assert "Jump-" not in sheet
    assert "jump" not in sheet.lower()


# --- T080: the drives line names the drive codes and power-plant tonnage ---


def test_render_sheet_drives_line_names_the_drive_codes():
    ship = build_ship(load_design(f"{_EXAMPLES}/free-trader.toml"))
    sheet = render_sheet(ship)
    assert "Jump-1 (A)" in sheet
    assert "Maneuver-1 (A)" in sheet
    assert "Power-1 (A)" in sheet
    assert "4t power plant" in sheet


# --- T085: hull code and standard/custom marker ---


def test_render_sheet_names_the_hull_code_and_standard_marker():
    ship = build_ship(load_design(f"{_EXAMPLES}/free-trader.toml"))
    sheet = render_sheet(ship)
    assert "Ship: Beowulf (standard)" in sheet
    assert "Hull: 200 tons, standard (hull 2)" in sheet


def test_render_sheet_shows_the_custom_marker_for_a_non_standard_design():
    ship = build_ship(load_design(f"{_EXAMPLES}/scout-courier.toml"))
    sheet = render_sheet(ship)
    assert "(custom)" in sheet
    assert "(hull 1)" in sheet


def test_render_sheet_names_the_small_craft_hull_code():
    ship = build_ship(load_design(f"{_EXAMPLES}/fighter.toml"))
    sheet = render_sheet(ship)
    assert "(hull s" in sheet


def test_render_sheet_shows_loaded_ammunition_in_armaments():
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
    ship = build_ship(design)
    sheet = render_sheet(ship)
    assert "Armaments:" in sheet
    assert "standard missile ammo x12" in sheet
