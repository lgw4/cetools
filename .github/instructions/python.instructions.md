---
applyTo: "**/*.py"
---

# Python Guidelines

## General Guidelines

- Use [`uv`](https://docs.astral.sh/uv/) for Python virtual environment and Python dependency management.
- Use `pyproject.toml` for configuring all Python-related tools (such as Black) that support it.
- Use Python >= 3.13.

## Style Guidelines

- Follow [Black](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html) and [PEP 8](https://peps.python.org/pep-0008/) for code style. Where there is a conflict, prefer Black code style. Override Black's line length to 99 characters.
- Use initial underscores in variable names to indicate variables intended to be private.
- *Never* use single letters for variable names. Variable names must be a *minimum* of two characters in length.
- Prefer functions to classes. Only use classes when necessary.
- Prefer straightforward code to complex code.
- Always use the constants defined in `http.HTTPStatus` for HTTP status codes.


## Documentation

- Generate docstrings for all functions and classes.

## Libraries

- Prefer `attrs` to Python dataclasses.
- Use `httpx` for HTTP requests.
- Use `pathlib` for filesystem operations.
- Use `pytest` for writing tests.
- Use `structlog` for all logging statements.
