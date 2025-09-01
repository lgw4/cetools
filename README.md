# CETools: Tools for use with the _Cepheus Engine SRD_ tabletop role-playing game

## Development with uv

This project uses `uv` for virtual environment and dependency management. Example (macOS, fish shell):

```sh
# create/sync the project environment and install dependencies
uv sync

# run tests inside the uv environment
uv run pytest -q
```

This file contains GitHub Copilot generated content.

Using just

If you have `just` installed you can run common tasks from the project root (macOS, fish shell):

```sh
just test   # run tests (uses uv run pytest)
just lint   # run ruff
just fmt    # format with black
just dev    # open an interactive uv shell
```

Installing dev extras

To install the development extras into the `uv` environment:

```sh
# create/sync the uv environment and install extras
uv sync --extras dev
```

If you are using pip directly (not recommended for this project), you can install dev deps with:

```sh
pip install -e .[dev]
```
