from cetools.dice import Roller
from cetools.errors import ValidationProblem
from cetools.names import (
    GivenNameTable,
    Name,
    SurnameEntry,
    SurnameTable,
    parse_given_names,
    parse_surnames,
    roll_name,
)


class TestGivenNameTable:
    def _data(self, **overrides):
        data = {
            "schema": "given-names",
            "schema-version": 1,
            "source": "Public domain census data",
            "names": ["Alex", "Jordan", "Sam"],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_given_names(self._data(), "given-names.toml")
        assert problems == ()
        assert isinstance(table, GivenNameTable)
        assert table.source == "Public domain census data"
        assert table.names == ("Alex", "Jordan", "Sam")

    def test_gender_key_is_rejected(self):
        # FR-043b: no name table may carry a gender field. The key set is
        # closed, so a `gender` key is an unrecognized key.
        table, problems = parse_given_names(self._data(gender="neutral"), "given-names.toml")
        assert table is None
        assert any(p.location == "gender" for p in problems)

    def test_missing_source_is_a_problem(self):
        data = self._data()
        del data["source"]
        table, problems = parse_given_names(data, "given-names.toml")
        assert table is None
        assert any(p.location == "source" and p.found == "missing" for p in problems)

    def test_empty_source_is_a_problem(self):
        table, problems = parse_given_names(self._data(source=""), "given-names.toml")
        assert table is None
        assert any(p.location == "source" for p in problems)

    def test_empty_names_array_is_a_problem_naming_the_file(self):
        table, problems = parse_given_names(self._data(names=[]), "given-names.toml")
        assert table is None
        matching = [p for p in problems if p.location == "names"]
        assert len(matching) == 1
        assert matching[0].file == "given-names.toml"

    def test_missing_names_is_a_problem(self):
        data = self._data()
        del data["names"]
        table, problems = parse_given_names(data, "given-names.toml")
        assert table is None
        assert any(p.location == "names" and p.found == "missing" for p in problems)

    def test_non_string_name_entry_is_a_type_problem(self):
        table, problems = parse_given_names(self._data(names=["Alex", 5]), "given-names.toml")
        assert table is None
        assert any(p.location == "names[1]" for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_given_names(self._data(extra="nope"), "given-names.toml")
        assert table is None
        assert any(p.location == "extra" for p in problems)


class TestSurnameTable:
    def _data(self, **overrides):
        data = {
            "schema": "surnames",
            "schema-version": 1,
            "region": "Indigenous peoples",
            "source": "Public domain census data",
            "names": [{"name": "Example", "people": "Example Nation"}, {"name": "Other"}],
        }
        data.update(overrides)
        return data

    def test_parses_valid_file(self):
        table, problems = parse_surnames(self._data(), "surnames-indigenous.toml")
        assert problems == ()
        assert isinstance(table, SurnameTable)
        assert table.region == "Indigenous peoples"
        assert table.source == "Public domain census data"
        assert len(table.names) == 2
        assert table.names[0] == SurnameEntry(name="Example", people="Example Nation")

    def test_people_is_optional(self):
        # FR-043d: required of the shipped indigenous-peoples table by a
        # test, optional in the schema — an override adding a region carries
        # no such obligation.
        table, problems = parse_surnames(self._data(), "surnames-indigenous.toml")
        assert problems == ()
        assert table.names[1] == SurnameEntry(name="Other", people="")

    def test_gender_key_is_rejected(self):
        table, problems = parse_surnames(self._data(gender="neutral"), "surnames-europe.toml")
        assert table is None
        assert any(p.location == "gender" for p in problems)

    def test_missing_region_is_a_problem(self):
        data = self._data()
        del data["region"]
        table, problems = parse_surnames(data, "surnames-europe.toml")
        assert table is None
        assert any(p.location == "region" and p.found == "missing" for p in problems)

    def test_empty_names_array_is_a_problem_naming_the_file(self):
        table, problems = parse_surnames(self._data(names=[]), "surnames-europe.toml")
        assert table is None
        matching = [p for p in problems if p.location == "names"]
        assert len(matching) == 1
        assert matching[0].file == "surnames-europe.toml"

    def test_missing_name_within_an_entry_is_a_problem(self):
        table, problems = parse_surnames(
            self._data(names=[{"people": "Example Nation"}]), "surnames-europe.toml"
        )
        assert table is None
        assert any(p.location == "names[0].name" for p in problems)

    def test_non_string_people_is_a_type_problem(self):
        table, problems = parse_surnames(
            self._data(names=[{"name": "Example", "people": 5}]), "surnames-europe.toml"
        )
        assert table is None
        assert any(p.location == "names[0].people" for p in problems)

    def test_unrecognized_key_within_an_entry_is_a_problem(self):
        table, problems = parse_surnames(
            self._data(names=[{"name": "Example", "extra": "nope"}]), "surnames-europe.toml"
        )
        assert table is None
        assert any(p.location == "names[0].extra" for p in problems)

    def test_unrecognized_top_level_key_is_a_problem(self):
        table, problems = parse_surnames(self._data(extra="nope"), "surnames-europe.toml")
        assert table is None
        assert any(p.location == "extra" for p in problems)

    def test_problems_are_validation_problem_instances(self):
        _, problems = parse_surnames(self._data(gender="x"), "surnames-europe.toml")
        assert all(isinstance(p, ValidationProblem) for p in problems)


_GIVEN = GivenNameTable(source="test", names=("Alex", "Jordan", "Sam"))
_EUROPE = SurnameTable(
    region="Europe", source="test", names=(SurnameEntry(name="Smith"), SurnameEntry(name="Jones"))
)
_ASIA = SurnameTable(
    region="Asia", source="test", names=(SurnameEntry(name="Tanaka"), SurnameEntry(name="Kim"))
)
_SURNAMES = {"surnames-europe": _EUROPE, "surnames-asia": _ASIA}


class TestRollName:
    def test_returns_a_name_with_full_composed_as_given_space_surname(self):
        name = roll_name(Roller(1), _GIVEN, _SURNAMES)
        assert isinstance(name, Name)
        assert name.full == f"{name.given_name} {name.surname}"

    def test_full_is_never_reordered(self):
        # FR-047a: given name first, surname second, always — never
        # `f"{surname} {given_name}"`.
        for seed in range(20):
            name = roll_name(Roller(seed), _GIVEN, _SURNAMES)
            assert name.full.startswith(name.given_name)
            assert name.full.endswith(name.surname)

    def test_region_is_one_of_the_tables_in_force(self):
        for seed in range(20):
            name = roll_name(Roller(seed), _GIVEN, _SURNAMES)
            assert name.region in {"Europe", "Asia"}

    def test_surname_is_drawn_from_the_selected_region(self):
        for seed in range(20):
            name = roll_name(Roller(seed), _GIVEN, _SURNAMES)
            region_names = {
                entry.name for entry in (_EUROPE if name.region == "Europe" else _ASIA).names
            }
            assert name.surname in region_names

    def test_given_name_is_drawn_from_the_given_table(self):
        for seed in range(20):
            name = roll_name(Roller(seed), _GIVEN, _SURNAMES)
            assert name.given_name in _GIVEN.names

    def test_same_seed_produces_the_same_name(self):
        assert roll_name(Roller(1), _GIVEN, _SURNAMES) == roll_name(Roller(1), _GIVEN, _SURNAMES)

    def test_both_regions_are_reachable_over_many_seeds(self):
        # Uniform over the tables in force, not weighted toward the first:
        # with two regions, both must appear across a modest sample.
        regions = {roll_name(Roller(seed), _GIVEN, _SURNAMES).region for seed in range(40)}
        assert regions == {"Europe", "Asia"}

    def test_a_single_surname_table_is_always_selected(self):
        name = roll_name(Roller(1), _GIVEN, {"surnames-europe": _EUROPE})
        assert name.region == "Europe"

    def test_order_of_the_mapping_does_not_affect_which_region_can_be_drawn(self):
        # roll_name sorts by region itself rather than trusting the caller's
        # mapping order, so a mapping built in a different key order still
        # reaches both regions.
        reordered = {"surnames-asia": _ASIA, "surnames-europe": _EUROPE}
        regions = {roll_name(Roller(seed), _GIVEN, reordered).region for seed in range(40)}
        assert regions == {"Europe", "Asia"}
