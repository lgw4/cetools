"""Direct tests of `ParseContext` (contracts/parse-context.md,
007-parse-context-carrier): what only a carrier can get wrong (FR-027) --
location construction and descent, collection sharing, and per-scope
failure. The eight checks themselves are exercised through
`tests/unit/test_schema.py`, which keeps transcribing the 006 contract.
"""

from cetools.schema import ParseContext


class TestDescent:
    def test_a_top_level_key_joins_the_empty_location_with_nothing(self):
        ctx = ParseContext("f.toml")
        assert ctx.at("task").location == "task"

    def test_a_key_joins_a_non_empty_location_with_a_dot(self):
        ctx = ParseContext("f.toml", "task")
        assert ctx.at("roll").location == "task.roll"

    def test_an_index_joins_as_a_bracketed_suffix(self):
        ctx = ParseContext("f.toml", "names")
        assert ctx.at(0).location == "names[0]"

    def test_multiple_parts_descend_in_one_call(self):
        ctx = ParseContext("f.toml", "tables.service")
        assert ctx.at("entries", 3).location == "tables.service.entries[3]"

    def test_a_key_after_an_index_joins_with_a_dot(self):
        ctx = ParseContext("f.toml", "rows[2].effects[0]")
        assert ctx.at("class").location == "rows[2].effects[0].class"


class TestEmptyParent:
    def test_a_top_level_key_never_gets_a_leading_dot(self):
        ctx = ParseContext("f.toml", "")
        child = ctx.at("task")
        assert child.location == "task"
        assert not child.location.startswith(".")


class TestSharedCollection:
    def test_a_problem_reported_on_a_child_is_visible_through_the_parent(self):
        parent = ParseContext("f.toml")
        child = parent.at("task")
        child.report(found="missing", expected="an integer")
        assert len(parent.problems) == 1
        assert parent.problems[0].location == "task"

    def test_the_collection_is_shared_by_reference_not_copied(self):
        parent = ParseContext("f.toml")
        child = parent.at("task")
        child.report(found="missing", expected="an integer")
        grandchild = child.at("roll")
        grandchild.report(found="missing", expected="a string")
        assert len(parent.problems) == 2
        assert len(child.problems) == 2
        assert len(grandchild.problems) == 2


class TestPerScopeFailure:
    def test_failed_is_false_before_this_scope_has_recorded_anything(self):
        parent = ParseContext("f.toml")
        sibling = parent.at("a")
        sibling.report(found="missing", expected="an integer")
        this_scope = parent.at("b")
        assert this_scope.failed is False

    def test_failed_is_true_once_this_scope_records_a_problem(self):
        ctx = ParseContext("f.toml")
        ctx.report(found="missing", expected="an integer")
        assert ctx.failed is True

    def test_failed_is_true_for_a_problem_recorded_by_a_descendant(self):
        parent = ParseContext("f.toml")
        child = parent.at("task")
        child.report(found="missing", expected="an integer")
        assert parent.failed is True


class TestLoaderCase:
    def test_a_carrier_built_over_a_list_that_already_has_problems_starts_unfailed(self):
        from cetools.errors import ValidationProblem

        existing = [
            ValidationProblem(file="other.toml", location="x", found="missing", expected="y")
        ]
        ctx = ParseContext("f.toml", problems=existing)
        assert ctx.failed is False
        assert len(ctx.problems) == 1
