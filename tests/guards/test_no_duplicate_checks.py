"""FR-014a/FR-014c: each of the eight field-checking vocabulary methods
(contracts/parse-context.md, 007-parse-context-carrier; originally
006-validation-vocabulary, contracts/schema-vocabulary.md) is defined
exactly once in the library's own source tree, under `src/`, as a method of
`ParseContext` in `src/cetools/schema.py`. That tree is the scope FR-014b
sets and the scope this guard scans; a definition under `tests/` or
anywhere else in the repository is outside its reach. This is the guard
that holds the rule the migration restored: the duplication removed from
five modules accumulated one locally reasonable copy at a time, and a
comment would not have stopped the seventeenth.

What this does not catch (FR-014b): the guard recognizes a check by its
name, at a module's top level or as a method of `ParseContext`. A check
written fresh and inline, without a name, goes undetected -- which is the
very shape this feature spent eleven conversions removing. Closing that
would mean recognizing a check by its structure, a much larger machine
aimed at a rarer mistake than the one that actually happened: the copies
that accumulated were copies of a named helper, five times over.
"""

import ast
from pathlib import Path

_CHECK_NAMES = frozenset(
    {
        "require_int",
        "require_string",
        "require_bool",
        "require_roll",
        "require_dict",
        "optional_bool",
        "unrecognized_keys",
        "require_list",
    }
)

_PARSE_CONTEXT = "ParseContext"


def _definitions(path: Path) -> list[tuple[str, bool]]:
    """Every (bare name, is_a_parse_context_method) pair for a definition at
    `path` matching one of the check names, at module top level or as a
    method of `ParseContext`, with or without a leading underscore.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, bool]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name.lstrip("_")
            if name in _CHECK_NAMES:
                found.append((name, False))
        elif isinstance(node, ast.ClassDef) and node.name == _PARSE_CONTEXT:
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = member.name.lstrip("_")
                    if name in _CHECK_NAMES:
                        found.append((name, True))
    return found


def _top_level_check_definitions(path: Path) -> set[str]:
    """The bare names of any of the check names defined at `path`'s module
    top level (never as a class method), with or without a leading
    underscore. Kept for the two meta-tests below, which plant a bare
    module-level function.
    """
    return {name for name, is_method in _definitions(path) if not is_method}


def test_the_guard_can_fail(repo_root: Path):
    # Planted, checked, and removed: the case this guard exists to catch,
    # stated directly, so a change that made the detector vacuously true
    # would be caught here rather than by the guard reporting success on
    # nothing (FR-014c).
    planted = repo_root / "src" / "cetools" / "_schema_offender.py"
    assert not planted.exists()
    planted.write_text("def require_int():\n    pass\n", encoding="utf-8")
    try:
        assert _top_level_check_definitions(planted) == {"require_int"}
    finally:
        planted.unlink()


def test_the_guard_catches_an_underscore_prefixed_copy_too(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "_schema_offender.py"
    assert not planted.exists()
    planted.write_text("def _require_int():\n    pass\n", encoding="utf-8")
    try:
        assert _top_level_check_definitions(planted) == {"require_int"}
    finally:
        planted.unlink()


def test_each_check_is_defined_exactly_once_as_a_parse_context_method(repo_root: Path):
    src_dir = repo_root / "src"
    schema_py = src_dir / "cetools" / "schema.py"
    schema_relative = schema_py.relative_to(repo_root).as_posix()

    locations: dict[str, list[str]] = {name: [] for name in _CHECK_NAMES}
    for path in sorted(src_dir.rglob("*.py")):
        relative = path.relative_to(repo_root).as_posix()
        for name, _is_method in _definitions(path):
            locations[name].append(relative)

    problems = [
        f"{name}: {files}" for name, files in locations.items() if files != [schema_relative]
    ]
    assert not problems, (
        "each check must be defined exactly once, as a ParseContext method in "
        "schema.py:\n" + "\n".join(problems)
    )
