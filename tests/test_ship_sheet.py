from cetools.engine.ships import ShipDesign, build_ship, load_design, render_sheet

_EXAMPLES = "specs/010-starship-generator/examples"


def _ships():
    for name in ("free-trader", "scout-courier", "warship", "fighter"):
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
