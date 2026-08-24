"""research R8: nothing under `src/` imports `locale`, which is what makes
SC-012 unfalsifiable by omission. `str.casefold` is locale-independent by
definition, so a subprocess comparison alone proves nothing about a build
that used `locale.strxfrm` throughout — this guard is what actually forbids
the mistake.
"""

import ast
from pathlib import Path


def _imports_locale(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "locale" or alias.name.startswith("locale.") for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "locale" or (node.module or "").startswith("locale."):
                return True
    return False


def test_nothing_under_src_imports_locale(repo_root: Path):
    src_dir = repo_root / "src"
    offenders = [
        path.relative_to(repo_root).as_posix()
        for path in sorted(src_dir.rglob("*.py"))
        if _imports_locale(path)
    ]
    assert not offenders, f"imports locale: {offenders}"


def test_the_guard_can_fail(repo_root: Path):
    # The rule this guard runs on, stated as a case: planted, checked, and
    # removed, so a change that made `_imports_locale` vacuously false would
    # be caught here rather than by the guard reporting success on nothing.
    planted = repo_root / "src" / "cetools" / "_locale_offender.py"
    assert not planted.exists()
    planted.write_text("import locale\n", encoding="utf-8")
    try:
        assert _imports_locale(planted)
    finally:
        planted.unlink()


def test_the_guard_catches_a_from_import_too(repo_root: Path):
    planted = repo_root / "src" / "cetools" / "_locale_offender.py"
    assert not planted.exists()
    planted.write_text("from locale import strxfrm\n", encoding="utf-8")
    try:
        assert _imports_locale(planted)
    finally:
        planted.unlink()
