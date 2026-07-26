"""Catalogue-invariant tests for `engine/ships/names.py`.

V1-V6 pin the per-entry shape every `SHIP_NAMES` row must have (data-model.md
"Validation rules"). V7 and the composition floors C1-C3 arrive with the
catalogue itself (tasks.md T024); selection is tested separately through
`ScriptedRolls` (tasks.md T008).
"""

import pytest

from cetools.engine.rolls import RollName, ScriptedRolls
from cetools.engine.ships.models import ShipDesign
from cetools.engine.ships.names import SHIP_NAMES, BasisKind, Tradition, generate_ship_name

FICTION_TRADITIONS = (Tradition.WRITTEN_SF, Tradition.SCREEN_SF)

# research.md Part E: a ship-type designation would duplicate what the
# description's own sentences already state, and would be wrong whenever the
# generated hull is not that type.
DESIGNATION_DENYLIST = (
    "Free Trader",
    "Scout",
    "Yacht",
    "Corsair",
    "Liner",
    "Courier",
    "Merchant",
    "Cruiser",
    "Frigate",
    "Destroyer",
    "Carrier",
    "Transport",
    "Shuttle",
    "Tender",
    "USS",
    "HMS",
    "ISS",
    "SS",
)


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v1_fiction_entries_carry_a_basis_kind(entry):
    if entry.tradition in FICTION_TRADITIONS:
        assert isinstance(entry.basis_kind, BasisKind)


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v2_fiction_entries_carry_a_non_empty_basis_reference(entry):
    if entry.tradition in FICTION_TRADITIONS:
        assert entry.basis_reference.strip() != ""


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v3_mythology_entries_carry_no_basis(entry):
    if entry.tradition is Tradition.MYTHOLOGY_FOLKLORE:
        assert entry.basis_kind is None
        assert entry.basis_reference == ""


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v4_name_is_non_empty_and_ascii(entry):
    assert entry.name != ""
    assert entry.name.isascii()


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v4a_name_has_no_stray_whitespace(entry):
    assert entry.name == entry.name.strip()
    assert "  " not in entry.name
    assert all(char == " " or not char.isspace() for char in entry.name)


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v5_name_does_not_begin_with_a_ship_type_designation(entry):
    for designation in DESIGNATION_DENYLIST:
        assert not entry.name.startswith(
            designation
        ), f"{entry.name!r} begins with the designation {designation!r}"


@pytest.mark.parametrize("entry", SHIP_NAMES, ids=lambda e: e.name)
def test_v6_name_survives_ship_design_construction(entry):
    ShipDesign(hull_tons=100, name=entry.name)


# --- T008: selection (FR-003, FR-011; contracts §generate_ship_name) -------


def test_generate_ship_name_returns_the_scripted_catalogue_entry():
    rolls = ScriptedRolls(choices={RollName.SHIP_NAME: 0})
    assert generate_ship_name(rolls) == SHIP_NAMES[0].name


def test_generate_ship_name_accepts_a_negative_index_from_the_end():
    rolls = ScriptedRolls(choices={RollName.SHIP_NAME: -1})
    assert generate_ship_name(rolls) == SHIP_NAMES[-1].name


def test_generate_ship_name_always_returns_a_catalogue_name():
    catalogue_names = {entry.name for entry in SHIP_NAMES}
    for index in range(len(SHIP_NAMES)):
        rolls = ScriptedRolls(choices={RollName.SHIP_NAME: index})
        assert generate_ship_name(rolls) in catalogue_names


# --- T024 (US3): catalogue composition floors and caps (FR-008, FR-009, SC-005) ---
# Assert floors and caps only, never exact counts, so adding a name is never a test edit.


def test_c1_catalogue_has_at_least_150_entries():
    assert len(SHIP_NAMES) >= 150


@pytest.mark.parametrize("tradition", list(Tradition))
def test_c2_every_tradition_has_at_least_20_entries(tradition):
    count = sum(1 for entry in SHIP_NAMES if entry.tradition is tradition)
    assert count >= 20


@pytest.mark.parametrize("tradition", list(Tradition))
def test_c3_no_tradition_exceeds_half_the_catalogue(tradition):
    count = sum(1 for entry in SHIP_NAMES if entry.tradition is tradition)
    assert count <= len(SHIP_NAMES) // 2


def test_v7_no_duplicate_names_after_stripping_and_casefolding():
    keys = {entry.name.strip().casefold() for entry in SHIP_NAMES}
    assert len(keys) == len(SHIP_NAMES)
