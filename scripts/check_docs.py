"""Check the docs against the code.

Documentation drifts faster than code, and nothing else tests it. Every check here
exists because the thing it catches actually happened:

1. `models.boost()` survived in CONTRIBUTING.md after a rename, and
   CAREER_REGISTRY / is_military_career survived a rewrite that deleted them.
2. Every README example called entry points that no longer existed, and one
   printed a whole dataclass where it meant to print a name.
3. CONTRIBUTING.md's module map silently omitted ranks.py the day it was added.
4. Spaced em-dashes accumulated against the project's punctuation rule.

Run: uv run python scripts/check_docs.py
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import io
import pkgutil
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The docs we maintain. docs/superpowers/ holds the historical plans and specs of
# past features: they are a record of what was decided at the time, not a
# description of the code as it stands, so they are deliberately not checked.
DOCS = ("README.md", "CONTEXT.md", "CONTRIBUTING.md", "AGENTS.md")
PROSE = [ROOT / doc for doc in DOCS] + sorted(ROOT.glob("docs/adr/*.md"))
SOURCES = sorted((ROOT / "src").rglob("*.py"))
ENGINE = ROOT / "src" / "cetools" / "engine"

# Backticked things that are prose, tooling, or SRD notation rather than cetools code.
NOT_CODE = {
    # tooling, files, git
    "uv",
    "uvx",
    "pytest",
    "black",
    "isort",
    "flake8",
    "pre-commit",
    "python",
    "bash",
    "text",
    "console",
    "markdown",
    "main",
    "HEAD",
    "cetools",
    "src",
    "tests",
    "docs",
    "scripts",
    # SRD notation and pseudo-hex digits
    "Psi",
    "Edu",
    "Soc",
    "Str",
    "Dex",
    "End",
    "Int",
    "A",
    "B",
    "I",
    "O",
    # standard-library methods used in prose
    "lower",
    "strip",
    "items",
    "keys",
    "values",
    "get",
}

failures: list[str] = []


def public_names() -> set[str]:
    """Every public name cetools defines: modules, module-level names, and the
    attributes of its classes (a dataclass field is a name the docs can cite)."""
    names: set[str] = set()
    package = importlib.import_module("cetools")
    for info in pkgutil.walk_packages(package.__path__, "cetools."):
        try:
            module = importlib.import_module(info.name)
        except Exception as exc:  # pragma: no cover
            failures.append(f"cannot import {info.name}: {exc}")
            continue
        names.add(info.name.rsplit(".", 1)[-1])
        for attr, value in vars(module).items():
            if attr.startswith("_"):
                continue
            names.add(attr)
            if inspect.isclass(value):
                names.update(a for a in dir(value) if not a.startswith("_"))
                names.update(getattr(value, "__annotations__", {}))
    return names


def check_symbols(known: set[str]) -> None:
    """Every backticked identifier in the prose must exist in the package."""
    token = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*(?:\(\))?)`")
    for path in PROSE:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for raw in token.findall(line):
                name = raw.removesuffix("()")
                if name in NOT_CODE or name.endswith((".md", ".toml", ".lock")):
                    continue
                if name.endswith(".py"):
                    if not list(ROOT.rglob(name)):
                        failures.append(f"{rel}:{lineno}: no such file `{name}`")
                    continue
                leaf = name.rsplit(".", 1)[-1]
                if leaf and leaf not in known and leaf not in NOT_CODE:
                    failures.append(f"{rel}:{lineno}: `{raw}` is not defined anywhere in cetools")


def check_readme_examples() -> None:
    """Every Python example in the README must run.

    The examples are one narrative: later blocks build on earlier imports, so they
    share a namespace and run in order, exactly as a reader would follow them.
    """
    blocks = re.findall(r"```python\n(.*?)```", (ROOT / "README.md").read_text(), re.S)
    if not blocks:
        failures.append("README.md: no Python examples found; did the fences change?")
        return

    namespace: dict = {"__name__": "__readme__"}
    for i, block in enumerate(blocks, 1):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(block, f"README.md[example {i}]", "exec"), namespace)
        except Exception as exc:
            failures.append(f"README.md: example {i} fails to run: {type(exc).__name__}: {exc}")


def check_module_map() -> None:
    """CONTRIBUTING.md's module map must name every engine module.

    Only the tree diagram counts: the prose elsewhere cites `tests/test_foo.py` as
    an example of the mirroring rule, and that is not a claim about a real file.
    """
    tree = [line for line in (ROOT / "CONTRIBUTING.md").read_text().splitlines() if "──" in line]
    listed = set(re.findall(r"([a-z_]+\.py)", "\n".join(tree)))
    actual = {p.name for p in ENGINE.glob("*.py") if p.name != "__init__.py"}
    for missing in sorted(actual - listed):
        failures.append(f"CONTRIBUTING.md: module map omits engine/{missing}")
    for extra in sorted(listed - actual):
        if not list(ROOT.rglob(extra)):
            failures.append(f"CONTRIBUTING.md: module map names {extra}, which does not exist")


def check_punctuation() -> None:
    """Em-dashes and en-dashes are tight: no leading or trailing spaces."""
    for path in PROSE + SOURCES:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if re.search(r" [—–] ", line):
                failures.append(f"{rel}:{lineno}: spaced em/en-dash; tighten it or use a comma")


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    check_symbols(public_names())
    check_readme_examples()
    check_module_map()
    check_punctuation()

    if failures:
        print(f"{len(failures)} docs problem(s):\n", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print("docs OK: symbols resolve, README examples run, module map complete, dashes tight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
