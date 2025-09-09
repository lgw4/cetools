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
- Follow [PEP 484](https://peps.python.org/pep-0484/) for type annotations. Code must be compliant with strict PEP 484 enforcement.
- Use initial underscores in variable names to indicate variables intended to be private.
- *Never* use single letters for variable names. Variable names must be a *minimum* of two characters in length.
- Prefer Python functions and built-in data types to classes. Only use classes when necessary.
- Prefer straightforward code to complex code.
- Always use the constants defined in `http.HTTPStatus` for HTTP status codes.

## Type Annotations

- All functions and methods must include proper type annotations for parameters and return values.
- Use `Optional[Type]` for parameters that can be None.
- When using Pydantic models, use explicit default syntax: `Field(default=None, ...)` instead of `Field(None, ...)` for better type checker compatibility.
- Ensure all code passes strict type checking tools like Pylance with PEP 484 enforcement enabled.


## Documentation

- Generate docstrings for all functions and classes.

## Libraries

- Prefer `attrs` to Python dataclasses.
- Use `httpx` for HTTP requests.
- Use `pathlib` for filesystem operations.
- Use `pytest` for writing tests.
- Use `structlog` for all logging statements.

## Pydantic Guidelines

- When defining Pydantic models, use explicit default syntax for better type checker compatibility:
  - ✅ Use: `field: Optional[str] = Field(default=None, description="...")`
  - ❌ Avoid: `field: Optional[str] = Field(None, description="...")`
  - ✅ Use: `field: int = Field(default=0, description="...")`
  - ❌ Avoid: `field: int = Field(0, description="...")`
- This ensures compatibility with strict PEP 484 type checkers like Pylance.
- All Pydantic model instantiations should work without explicitly providing optional parameters.
