"""Guard the premise basename positioning rests on: every `.toml` under
`src/cetools/data/` has a unique basename, since the basename is the
composition key (FR-029, research R3). This fails the moment a second
`navy.toml` is added under another directory.
"""

from collections import Counter
from pathlib import Path


def test_data_file_basenames_are_unique(repo_root: Path):
    data_dir = repo_root / "src" / "cetools" / "data"
    basenames = [path.name for path in data_dir.rglob("*.toml")]

    counts = Counter(basenames)
    duplicates = {name: count for name, count in counts.items() if count > 1}

    assert not duplicates, f"duplicate basenames under {data_dir}: {duplicates}"
    assert basenames, f"no .toml files found under {data_dir}"
