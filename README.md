# cetools

A dice and task-check engine for Cepheus Engine SRD-based games: seeded,
reproducible dice throws and 2D6 task resolution, available as a Python
library and as the `cetools` command-line tool.

## Development

```sh
uv sync
uv run pytest
```

## Licensing

This repository carries two licenses. `src/cetools/data/tasks.toml` is Open
Game Content under the Open Game License v1.0a (see `LICENSE-OGL.txt`).
Everything else — the library and CLI source, tests, and packaging — is
licensed under the GNU General Public License v3.0 (see `LICENSE`).
