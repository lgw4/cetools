"""`generate_batch` (contracts/library-api.md, research R2): one master
seed and a derivation, not one continuous stream.
"""

import dataclasses

import pytest

from cetools.dice import Roller
from cetools.errors import CetoolsError
from cetools.generator import character_seed, generate_batch, generate_character
from cetools.rules import load_rules
from cetools.seeds import resolve_seed

RULES = load_rules()


class TestPrefixProperty:
    @pytest.mark.parametrize("seed", ["session-alpha", "session-beta", 7, 100])
    @pytest.mark.parametrize("small,large", [(1, 3), (3, 12), (1, 5)])
    def test_the_first_characters_of_a_larger_batch_equal_a_smaller_batch(
        self, seed, small, large
    ):
        smaller = generate_batch(seed, RULES, count=small)
        larger = generate_batch(seed, RULES, count=large)
        for i in range(small):
            assert dataclasses.asdict(smaller.characters[i]) == dataclasses.asdict(
                larger.characters[i]
            )

    def test_position_zero_equals_the_single_character_of_that_seed(self):
        for seed in ("session-alpha", 42):
            batch = generate_batch(seed, RULES, count=1)
            resolved = resolve_seed(seed)
            single = generate_character(Roller(resolved), RULES)
            assert dataclasses.asdict(batch.characters[0]) == dataclasses.asdict(single)
            assert batch.characters[0].seed == resolved


class TestCharacterSeed:
    def test_position_zero_is_the_master_itself(self):
        assert character_seed(123456789, 0) == 123456789

    def test_other_positions_are_a_derivation(self):
        assert character_seed(123456789, 1) != 123456789
        assert character_seed(123456789, 1) != character_seed(123456789, 2)

    def test_each_characters_own_derived_seed_regenerates_it_alone(self):
        batch = generate_batch("session-alpha", RULES, count=5)
        for character in batch.characters:
            regenerated = generate_batch(character.seed, RULES, count=1)
            assert dataclasses.asdict(regenerated.characters[0]) == dataclasses.asdict(character)


class TestUsageErrors:
    def test_count_below_one_raises(self):
        with pytest.raises(CetoolsError):
            generate_batch("session-alpha", RULES, count=0)
        with pytest.raises(CetoolsError):
            generate_batch("session-alpha", RULES, count=-1)

    def test_a_name_with_count_above_one_raises(self):
        with pytest.raises(CetoolsError):
            generate_batch("session-alpha", RULES, count=2, name="Alex Rivera")


def test_generate_batch_from_none_reached_from_the_library():
    """FR-053b, reached without the command line: `generate_batch(None,
    rules)` draws a seed from `secrets` and records it, and that seed
    quoted back reproduces the same character.
    """
    batch = generate_batch(None, RULES)
    assert len(batch.characters) == 1
    reproduced = generate_batch(batch.seed, RULES)
    assert dataclasses.asdict(reproduced.characters[0]) == dataclasses.asdict(batch.characters[0])
