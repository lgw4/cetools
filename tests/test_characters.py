"""Tests for the characters generator."""

from cetools.characters import generate


def test_generate_seed_deterministic():
    a = generate(seed=42)
    b = generate(seed=42)
    assert a.model_dump() == b.model_dump()


def test_generate_template_overrides():
    tmpl = {"name": "Alice", "strength": 12, "skills": {"Gunnery": 1}}
    c = generate(seed=1, template=tmpl)
    data = c.model_dump()
    assert data["name"] == "Alice"
    assert data["strength"] == 12
    assert data["skills"]["Gunnery"] == 1


# This file contains GitHub Copilot generated content.
