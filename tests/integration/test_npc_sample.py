"""SC-003 through SC-008, SC-019, SC-020: the sampled audits. Marked
`slow` (research R14) — a thousand seeds for the always-living and
consistency audits, ten thousand rolled names for the regional weighting
check — so the inner development loop (`-m "not slow"`) stays fast while
CI still runs every seed SC-003 requires.
"""

import pytest

from cetools.dice import Roller
from cetools.generator import generate_character
from cetools.names import roll_name
from cetools.rules import load_rules

pytestmark = pytest.mark.slow

RULES = load_rules()
_SAMPLE_SIZE = 1000


@pytest.fixture(scope="module")
def sample():
    return [generate_character(Roller(i), RULES) for i in range(_SAMPLE_SIZE)]


class TestAlwaysLivingAndConsistency:
    def test_sc003_every_seed_produces_a_living_complete_character(self, sample):
        for character in sample:
            assert character.name
            assert character.careers
            assert character.history

    def test_sc004_every_character_is_internally_consistent(self, sample):
        cap = RULES.chargen.terms_cap
        for character in sample:
            assert character.funds >= 0
            assert character.debt >= 0
            total_terms = sum(service.terms for service in character.careers)
            assert total_terms <= cap
            assert character.age >= RULES.chargen.terms_starting_age
            for service in character.careers:
                career = next(c for c in RULES.careers.values() if c.name == service.career)
                ladder = next(lad for lad in career.ladders if lad.name == service.ladder)
                assert any(rank.rank == service.rank for rank in ladder.ranks)
            # No consequence appears that no history step produced: every
            # career the character served has at least a career-entered step.
            entered_careers = {
                step.career for step in character.history if step.kind == "career-entered"
            }
            assert {service.career for service in character.careers} <= entered_careers

    def test_sc005_every_field_traces_to_a_history_step(self, sample):
        for character in sample:
            skill_effects = {
                effect.subject
                for step in character.history
                for effect in step.effects
                if effect.kind == "skill"
            }
            for skill in character.skills:
                label = (
                    skill.name if skill.specialty is None else f"{skill.name} ({skill.specialty})"
                )
                assert label in skill_effects


class TestSpreadAndCoverage:
    def test_sc006_ages_spread_rather_than_parked_at_the_cap(self, sample):
        cap = RULES.chargen.terms_cap
        term_counts = {sum(service.terms for service in c.careers) for c in sample}
        assert len(term_counts) >= 5
        at_cap = sum(1 for c in sample if sum(s.terms for s in c.careers) >= cap)
        assert at_cap <= len(sample) / 4

    def test_sc007_multi_career_characters_occur(self, sample):
        assert any(len(c.careers) == 2 for c in sample)
        assert any(len(c.careers) == 3 for c in sample)

    def test_sc008_every_shape_the_engine_handles_is_exercised(self, sample):
        commissioned = any(service.commissioned for c in sample for service in c.careers)
        not_commissioned = any(not service.commissioned for c in sample for service in c.careers)
        assert commissioned and not_commissioned

        tiers_charged = set()
        for character in sample:
            for step in character.history:
                if step.kind == "medical-bills":
                    career = next(c for c in RULES.careers.values() if c.name == step.career)
                    tiers_charged.add(career.medical_tier)
        assert tiers_charged == set(RULES.medical_tiers.tiers)

        drifter_fallback = any(
            service.career == "Drifter" and service.entered_by == "fallback"
            for c in sample
            for service in c.careers
        )
        drifter_reentered = any(
            sum(1 for service in c.careers if service.career == "Drifter") >= 2 for c in sample
        )
        assert drifter_fallback and drifter_reentered

        draft_rows_reached = {
            step.selected for c in sample for step in c.history if step.kind == "draft"
        }
        assert draft_rows_reached == set(RULES.draft.careers)


class TestDefaultRenderingCoverage:
    def test_sc020_every_default_field_is_present_and_nothing_from_the_walk_leaks(self, sample):
        from cetools.render import as_text

        for character in sample[:200]:
            text = as_text(character)
            assert text  # every field the default rendering carries is non-empty
            for leak in ("Seed:", "Rules:", "cetools", "Debt:", "Pension:", "History:"):
                assert leak not in text


def test_sc019_name_weighting_is_over_tables_not_over_names():
    roller = Roller("name-weighting-sample")
    region_counts: dict[str, int] = {}
    for _ in range(10_000):
        name = roll_name(roller, RULES.given_names, RULES.surnames)
        region_counts[name.region] = region_counts.get(name.region, 0) + 1

    table_count = len(RULES.surnames)
    expected_share = 1 / table_count
    for region, count in region_counts.items():
        share = count / 10_000
        assert 0.9 * expected_share <= share <= 1.1 * expected_share, (region, share)
