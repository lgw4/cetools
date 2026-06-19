# Data Model: isort Quality Gate and Pre-Commit Support

This feature introduces no domain entities, database tables, or dataclasses. It is purely
developer-tooling configuration.

## Configuration Entities

The "entities" in this feature are configuration stanzas and files — not Python objects.

### `.pre-commit-config.yaml`

| Field | Value | Notes |
|-------|-------|-------|
| `repos[].repo` | upstream GitHub URL | One entry per tool (isort, black, flake8) + one local |
| `repos[].rev` | exact release tag (e.g., `5.13.2`) | Pinned per FR-005; update via `pre-commit autoupdate` |
| `repos[].hooks[].id` | hook identifier | e.g., `isort`, `black`, `flake8`, `pytest` |
| `repos[].hooks[].stages` | `[pre-push]` | All hooks fire only at push time |
| `repos[].hooks[].args` | `[--check-only, --diff]` for isort | Check mode: report but do not auto-fix during hook run |

**State transitions**: None — this is a static config file.

### `pyproject.toml` additions

| Section | Key | Value |
|---------|-----|-------|
| `[dependency-groups] dev` | `isort` | `>=5.13` |
| `[dependency-groups] dev` | `pre-commit` | `>=3` |
| `[tool.isort]` | `profile` | `"black"` |
| `[tool.isort]` | `line_length` | `99` |
| `[tool.isort]` | `src_paths` | `["src", "tests"]` |

### `AGENTS.md` addition

A new "Hooks" subsection inside the existing "Setup" section, containing:

```
pre-commit install --hook-type pre-push
```

This is a one-time command run after `uv sync`.

## Validation Rules

- `line_length` in `[tool.isort]` MUST equal `line-length` in `[tool.black]` (both 99).
- `profile = "black"` MUST be present; without it, isort and Black will produce conflicting output.
- All `rev` values in `.pre-commit-config.yaml` MUST be pinned to a release tag, not `HEAD` or a branch name.
- The local pytest hook MUST use `language: system` and `pass_filenames: false`.
