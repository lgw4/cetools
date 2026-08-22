"""SC-015b: properties of the shipped name tables asserted directly against
the packaged data, not merely implied by the schema (FR-043b, FR-043d,
FR-043e, FR-043i).
"""

import tomllib
from pathlib import Path

_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "names"


def _load(name: str) -> dict:
    return tomllib.loads((_DATA / name).read_text(encoding="utf-8"))


def _surname_files() -> list[Path]:
    return sorted(_DATA.glob("surnames-*.toml"))


def test_the_given_names_table_records_a_source():
    data = _load("given-names.toml")
    assert data["source"]


def test_the_given_names_table_holds_at_least_sixty_entries():
    data = _load("given-names.toml")
    assert len(data["names"]) >= 60


def test_the_given_names_table_carries_no_gender_field():
    data = _load("given-names.toml")
    assert "gender" not in data


def test_every_surname_table_records_a_source():
    for path in _surname_files():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        assert data["source"], path.name


def test_every_surname_table_holds_at_least_forty_entries():
    for path in _surname_files():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        assert len(data["names"]) >= 40, path.name


def test_no_surname_table_carries_a_gender_field():
    for path in _surname_files():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        assert "gender" not in data, path.name
        for entry in data["names"]:
            assert "gender" not in entry, path.name


def test_every_indigenous_peoples_entry_names_its_people():
    data = _load("surnames-indigenous.toml")
    assert data["region"] == "Indigenous peoples"
    for entry in data["names"]:
        assert entry.get("people"), entry
