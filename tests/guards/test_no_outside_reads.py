"""SC-007: with no override supplied, no filesystem location outside the
installed package is opened during a load, verified automatically via an
audit hook rather than by inspection (research R6).

Audit hooks cannot be removed once installed, so the hook is installed once
at module import here and does nothing unless armed. Import everything
before arming, and filter `__pycache__`: the hook also fires for import
machinery reads of compiled bytecode.
"""

import sys
from pathlib import Path

import cetools  # noqa: F401  (import everything before the hook is armed)
from cetools.rules import load_rules

_opened: list[str] = []
_armed = False


def _audit_hook(event: str, args: tuple) -> None:
    if not _armed or event != "open":
        return
    path = args[0]
    if isinstance(path, (str, bytes, Path)):
        _opened.append(str(path))


sys.addaudithook(_audit_hook)


def test_no_outside_reads_during_a_packaged_load():
    global _armed
    load_rules.cache_clear()
    _opened.clear()
    _armed = True
    try:
        load_rules()
    finally:
        _armed = False
        load_rules.cache_clear()

    package_dir = Path(cetools.__file__).resolve().parent
    # `resources.files(...)` and `importlib.metadata.version(...)` are read
    # through the interpreter's own installation: the base interpreter (whose
    # stdlib may ship as a zip, as it does under a uv-managed toolchain) and
    # the virtualenv's site-packages, where this package's own `.dist-info`
    # metadata lives alongside `cetools/` rather than inside it. Both are
    # "the installed package" in the sense SC-007 means; a mistyped config
    # path or a working-directory read is what this guard exists to catch.
    installation_roots = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}

    def _inside(root: Path, resolved: Path) -> bool:
        return resolved == root or root in resolved.parents

    outside = []
    for raw in _opened:
        resolved = Path(raw).resolve()
        if "__pycache__" in resolved.parts:
            continue
        if _inside(package_dir, resolved):
            continue
        if any(_inside(root, resolved) for root in installation_roots):
            continue
        outside.append(str(resolved))

    assert not outside, f"opened a location outside the installed package: {outside}"
    assert _opened, "the audit hook recorded nothing; is it actually firing?"
