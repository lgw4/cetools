from cetools.errors import ValidationProblem
from cetools.names import GivenNameTable, SurnameEntry, SurnameTable, parse_given_names, parse_surnames


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
        table, problems = parse_given_names(
            self._data(gender="neutral"), "given-names.toml"
        )
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
        table, problems = parse_surnames(
            self._data(gender="neutral"), "surnames-europe.toml"
        )
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
