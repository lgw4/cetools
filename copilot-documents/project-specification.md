# Cepheus Engine Tools (cetools) — Project Specification

## Overview

This project provides a suite of command-line utilities to help players and referees of the Cepheus Engine roleplaying game ([Cepheus SRD](https://cepheus-srd.opengamingnetwork.com)). The primary delivery is a CLI, but the design and implementation should enable reuse as a library and easily expose functionality via a RESTful API or web application.

## Goals

- Provide compact, well-tested CLI tools for common tasks: character generation, NPC creation, equipment and vehicle lookup, random encounters, and dice utilities.
- Modernize the codebase to use current Python standards (>= 3.13), with a clean package layout, type hints, and test coverage.
- Ensure code is reusable in other contexts (importable library, REST API, web UI).
- Provide clear documentation and developer experience (pyproject.toml, uv environment usage, tests, linting, CI-ready structure).

## Audience

- Players who want quick character tools and dice utilities.
- Referees who need rapid NPC, encounter, and equipment generation.
- Developers integrating cetools into web or API services.

## High-level Scope

- Core domain modules: characters, NPCs, gear, vehicles, encounters, dice, rules lookups.
- CLI entry points for each core domain with well-documented flags and a JSON output option.
- Library API that mirrors CLI functionality with clear function contracts and types.
- Test suite (pytest) with unit tests for core logic and small integration tests for CLI entry points.
- Formatting and linting configuration (Black, isort, ruff) via pyproject.toml.

## Non-functional Requirements

- Compatibility: Python >= 3.13.
- Packaging: installable via pip (editable during development).
- Performance: responsive for single-run CLI commands; no heavy long-running tasks.
- Reliability: deterministic RNG options and seed input for reproducible outputs.
- Security: avoid executing untrusted code and do not include network calls by default.
- Accessibility: CLI should have clear help and machine-friendly JSON output.

- Build system: do NOT use `setuptools` as the project's PEP 517 build backend. Prefer a modern, PEP 517-compatible backend such as `hatchling` or `flit` (for example, `hatchling.build`). Declare the chosen backend explicitly in the `[build-system]` table in `pyproject.toml` and avoid referencing `setuptools` in that section.

## Design and Architecture

- Layered design:
  - Core library (pure Python, typed) exposes domain APIs.
  - CLI module(s) that call into core library; use `argparse` or `click`.
  - Optional adapter layer to expose a small REST API (FastAPI recommended for async-first, type-driven design).

- Data shapes: all domain outputs should be serializable to JSON with pydantic models or typed dataclasses and explicit `to_dict` methods.

- Configuration: support environment variables and CLI flags; use a small config module.

## Command-Line Utilities (initial set)

- `cetools character create` — generate a character with options for career, template, and output format (text/JSON). Inputs: career(s), template file, seed. Output: character JSON.
- `cetools npc generate` — quick NPC creation with role, threat level, and seed.
- `cetools dice roll` — roll one or more dice expressions (e.g., "2d6+3") with verbose and JSON modes.
- `cetools equipment find` — lookup equipment by name or category; output descriptive stats.
- `cetools encounter random` — build a random encounter given party level/size and terrain.

## Library API Contract (example)

- `characters.generate(career: str | None, seed: int | None, template: dict | None) -> Character`
- `dice.roll(expression: str, seed: int | None) -> RollResult`
- `npc.create(role: str | None, threat: int | None, seed: int | None) -> NPC`

## Data Formats

- JSON: All primary outputs must support a machine-readable JSON representation.
- YAML (optional): Add as an output format if requested later.

## Error Handling

- CLI: return non-zero exit codes for errors and print helpful messages to stderr.
- Library: raise typed exceptions (e.g., `InvalidInputError`, `NotFoundError`) so callers can handle errors.

## Testing Strategy

- Unit tests for core logic with deterministic seeds.
- Fixture files for example templates and small reference datasets.
- CLI smoke tests using the `subprocess` module or `click` testing utilities.

## CI and Quality

- Use GitHub Actions (or similar) to run tests, linting, and type checks on PRs.
- Enforce formatting with pre-commit hooks.

## Implementation Roadmap (phases)

1. Repository cleanup and modernize packaging (pyproject, uv/venv notes).
2. Implement core library modules with type hints and tests (characters, dice, npc).
3. Implement CLI wrappers for the core modules.
4. Add adapter layer for FastAPI and a small demo web UI (optional).
5. Improve docs, add examples, and finish CI pipelines.

## Open Questions / Assumptions

- Assumption: The existing code in `src/cetools` contains useful domain logic to be refactored rather than rewritten from scratch.
- Question: Are there external data files (equipment lists, vehicles) that should be bundled? If large, they should be stored in a data subpackage or fetched via optional extras.

## Deliverables

- `src/cetools/` — modernized library code with type hints.
- `console_scripts` entry points in `pyproject.toml` for the CLI.
- `tests/` — pytest tests.
- `copilot-documents/project-specification.md` — this file.

<!-- This file contains GitHub Copilot generated content. -->
