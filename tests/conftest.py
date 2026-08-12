from pathlib import Path

import pytest

SEEDED_LITERAL = "session-alpha"


@pytest.fixture(autouse=True)
def _clear_task_parameters_cache():
    from cetools.rules import load_task_parameters

    load_task_parameters.cache_clear()
    yield
    load_task_parameters.cache_clear()


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def seeded_roller():
    from cetools import Roller

    return Roller(SEEDED_LITERAL)


@pytest.fixture
def read_golden():
    golden_dir = Path(__file__).resolve().parent / "golden"

    def _read(name: str) -> str:
        return (golden_dir / name).read_text(encoding="utf-8")

    return _read
