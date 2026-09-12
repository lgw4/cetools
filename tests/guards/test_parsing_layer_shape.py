"""FR-022/FR-023 (007-parse-context-carrier): the four counts the migration
promises hold in the finished tree, each demonstrably able to fail.

SC-002: no function in the rules-data parsing layer takes the file name as
a parameter, save one named exclusion (FR-011, FR-012) plus `ParseContext`'s
own constructor, which is where a file name enters the carrier rather than
being threaded by hand.

SC-003: the header-key constant is defined exactly once, in `schema.py`.

SC-004: no function in the parsing layer takes or returns
`list[ValidationProblem]`, save `ParseContext.__init__`, which is what
implements the one problem-passing convention the migration leaves standing
(the carrier's own shared collection) rather than a convention a caller
chooses.

SC-005: the non-empty-array idiom's `"an empty array"` literal exists
nowhere under `src/` but inside `ParseContext` in `schema.py`.
"""

import ast
from pathlib import Path

_PARSING_LAYER_MODULES = ("careers.py", "chargen.py", "names.py", "registries.py", "schema.py")
_FILE_PARAM_EXCLUSIONS = frozenset({"_unreadable", "__init__"})
_LIST_VALIDATION_PROBLEM_EXCLUSIONS = frozenset({"__init__"})
_EMPTY_ARRAY_LITERAL = "an empty array"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _iter_functions(tree: ast.Module):
    """Every function or method defined anywhere in `tree`, at any nesting
    depth, paired with its own name (not its qualified name: `_unreadable`
    and `ParseContext.__init__` are named exclusions by their own bare
    name, and nothing else in this package repeats either).
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _param_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = node.args
    names = {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    if args.vararg is not None:
        names.add(args.vararg.arg)
    if args.kwarg is not None:
        names.add(args.kwarg.arg)
    return names


def _annotation_mentions_list_of_validation_problem(node: ast.AST | None) -> bool:
    if node is None:
        return False
    return "list[ValidationProblem]" in ast.unparse(node)


def _function_mentions_list_of_validation_problem(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    if _annotation_mentions_list_of_validation_problem(node.returns):
        return True
    args = node.args
    for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs):
        if _annotation_mentions_list_of_validation_problem(arg.annotation):
            return True
    return False


def _string_constants_excluding_docstrings(tree: ast.Module):
    """Every `ast.Constant` string literal in `tree`, except the first
    statement of the module, a class, or a function when that statement is
    itself a bare string (a docstring) -- `errors.py:37` names the SC-005
    phrase inside prose explaining the vocabulary, and a docstring is not a
    reportable string a check builds.
    """
    docstring_nodes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstring_nodes.add(id(body[0].value))

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_nodes
        ):
            yield node.value


def _sc002_violations(src_dir: Path) -> list[str]:
    violations = []
    for name in _PARSING_LAYER_MODULES:
        for node in _iter_functions(_parse(src_dir / "cetools" / name)):
            if "file" in _param_names(node) and node.name not in _FILE_PARAM_EXCLUSIONS:
                violations.append(f"{name}:{node.name}")
    rules_tree = _parse(src_dir / "cetools" / "rules.py")
    for node in _iter_functions(rules_tree):
        if "file" in _param_names(node) and node.name != "_unreadable":
            violations.append(f"rules.py:{node.name}")
    return violations


def _sc003_locations(src_dir: Path) -> list[str]:
    locations = []
    for path in sorted(src_dir.rglob("*.py")):
        tree = _parse(path)
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign) and node.target is not None:
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.lstrip("_") == "HEADER_KEYS":
                    locations.append(path.relative_to(src_dir).as_posix())
    return locations


def _sc004_violations(src_dir: Path) -> list[str]:
    violations = []
    for name in _PARSING_LAYER_MODULES:
        for node in _iter_functions(_parse(src_dir / "cetools" / name)):
            if (
                node.name not in _LIST_VALIDATION_PROBLEM_EXCLUSIONS
                and _function_mentions_list_of_validation_problem(node)
            ):
                violations.append(f"{name}:{node.name}")
    return violations


def _sc005_locations(src_dir: Path) -> list[str]:
    locations = []
    for path in sorted(src_dir.rglob("*.py")):
        if path.name == "schema.py":
            continue
        tree = _parse(path)
        for value in _string_constants_excluding_docstrings(tree):
            if value == _EMPTY_ARRAY_LITERAL:
                locations.append(path.relative_to(src_dir).as_posix())
                break
    return locations


def test_sc002_no_parsing_layer_function_takes_a_file_name(repo_root: Path):
    violations = _sc002_violations(repo_root / "src")
    assert not violations, (
        "no function may take `file` except rules._unreadable (FR-012) and "
        f"ParseContext.__init__: {violations}"
    )


def test_sc002_can_fail(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "careers.py"
    original = planted.read_text(encoding="utf-8")
    try:
        planted.write_text(original + "\n\ndef _offender(file):\n    pass\n", encoding="utf-8")
        assert "careers.py:_offender" in _sc002_violations(repo_root / "src")
    finally:
        planted.write_text(original, encoding="utf-8")


def test_sc003_header_keys_is_defined_exactly_once(repo_root: Path):
    locations = _sc003_locations(repo_root / "src")
    assert locations == ["cetools/schema.py"], locations


def test_sc003_can_fail(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "_header_keys_offender.py"
    assert not planted.exists()
    planted.write_text('HEADER_KEYS = frozenset({"schema"})\n', encoding="utf-8")
    try:
        locations = _sc003_locations(repo_root / "src")
        assert locations == ["cetools/_header_keys_offender.py", "cetools/schema.py"]
    finally:
        planted.unlink()


def test_sc004_no_parsing_layer_function_carries_a_problem_list(repo_root: Path):
    violations = _sc004_violations(repo_root / "src")
    assert not violations, (
        "no function may take or return list[ValidationProblem] except "
        f"ParseContext.__init__: {violations}"
    )


def test_sc004_can_fail(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "chargen.py"
    original = planted.read_text(encoding="utf-8")
    offender = "\n\ndef _offender(problems: list[ValidationProblem]) -> None:\n    pass\n"
    try:
        planted.write_text(original + offender, encoding="utf-8")
        assert "chargen.py:_offender" in _sc004_violations(repo_root / "src")
    finally:
        planted.write_text(original, encoding="utf-8")


def test_sc005_the_empty_array_literal_lives_only_in_parse_context(repo_root: Path):
    locations = _sc005_locations(repo_root / "src")
    assert not locations, f"'an empty array' must appear only in schema.py: {locations}"


def test_sc005_can_fail(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "_empty_array_offender.py"
    assert not planted.exists()
    planted.write_text('X = "an empty array"\n', encoding="utf-8")
    try:
        assert "cetools/_empty_array_offender.py" in _sc005_locations(repo_root / "src")
    finally:
        planted.unlink()


def test_sc005_skips_docstrings(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "_empty_array_docstring.py"
    assert not planted.exists()
    planted.write_text('"""Mentions an empty array in prose."""\n', encoding="utf-8")
    try:
        assert "cetools/_empty_array_docstring.py" not in _sc005_locations(repo_root / "src")
    finally:
        planted.unlink()
