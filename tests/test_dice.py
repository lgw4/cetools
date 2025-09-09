"""Tests for dice expression parser and roll engine."""

import pytest

from cetools.core.dice import (
    AdvantageType,
    DiceExpressionError,
    DiceParser,
    DiceRoll,
    DiceType,
    RollResult,
    roll_dice,
)


class TestDiceParser:
    """Test cases for DiceParser."""

    def test_parse_standard_dice_expressions(self):
        """Test parsing of standard dice expressions."""
        parser = DiceParser()

        # Basic dice expressions
        dice_type, params = parser.parse_expression("2d6")
        assert dice_type == DiceType.STANDARD
        assert params == {"count": 2, "size": 6, "modifier": 0}

        dice_type, params = parser.parse_expression("1d20+5")
        assert dice_type == DiceType.STANDARD
        assert params == {"count": 1, "size": 20, "modifier": 5}

        dice_type, params = parser.parse_expression("3d8-2")
        assert dice_type == DiceType.STANDARD
        assert params == {"count": 3, "size": 8, "modifier": -2}

        # Default count of 1
        dice_type, params = parser.parse_expression("d10")
        assert dice_type == DiceType.STANDARD
        assert params == {"count": 1, "size": 10, "modifier": 0}

    def test_parse_d66_expressions(self):
        """Test parsing of D66 expressions."""
        parser = DiceParser()

        # Basic D66
        dice_type, params = parser.parse_expression("d66")
        assert dice_type == DiceType.D66
        assert params == {"modifier": 0}

        # D66 with modifier
        dice_type, params = parser.parse_expression("D66+3")
        assert dice_type == DiceType.D66
        assert params == {"modifier": 3}

        # Unordered D66
        dice_type, params = parser.parse_expression("d66u")
        assert dice_type == DiceType.D66_UNORDERED
        assert params == {"modifier": 0}

        dice_type, params = parser.parse_expression("D66U-1")
        assert dice_type == DiceType.D66_UNORDERED
        assert params == {"modifier": -1}

    def test_parse_invalid_expressions(self):
        """Test that invalid expressions raise DiceExpressionError."""
        parser = DiceParser()

        invalid_expressions = [
            "",
            "invalid",
            "2d",
            "d",
            "0d6",
            "2d0",
            "d6d6",
            "2d6+",
            "d100abc",
            "d66ux",  # Invalid suffix
        ]

        for expr in invalid_expressions:
            with pytest.raises(DiceExpressionError):
                parser.parse_expression(expr)

    def test_roll_dice_basic(self):
        """Test basic dice rolling functionality."""
        parser = DiceParser(seed=42)  # Fixed seed for reproducible tests

        # Roll 2d6
        rolls = parser.roll_dice(2, 6)
        assert len(rolls) == 2
        assert all(isinstance(roll, DiceRoll) for roll in rolls)
        assert all(roll.die_size == 6 for roll in rolls)
        assert all(1 <= roll.result <= 6 for roll in rolls)

        # With fixed seed, results should be reproducible
        parser2 = DiceParser(seed=42)
        rolls2 = parser2.roll_dice(2, 6)
        assert [roll.result for roll in rolls] == [roll.result for roll in rolls2]

    def test_roll_d66(self):
        """Test D66 rolling functionality."""
        parser = DiceParser(seed=42)

        # Test ordered D66
        rolls, composed = parser.roll_d66(unordered=False)
        assert len(rolls) == 2
        assert all(isinstance(roll, DiceRoll) for roll in rolls)
        assert all(roll.die_size == 6 for roll in rolls)
        assert all(1 <= roll.result <= 6 for roll in rolls)
        assert 11 <= composed <= 66
        assert composed == rolls[0].result * 10 + rolls[1].result

        # Test unordered D66
        parser = DiceParser(seed=123)  # Different seed to get different values
        rolls, composed = parser.roll_d66(unordered=True)
        die1, die2 = rolls[0].result, rolls[1].result
        sorted_dice = sorted([die1, die2], reverse=True)
        expected_composed = sorted_dice[0] * 10 + sorted_dice[1]
        assert composed == expected_composed

    def test_apply_advantage_none(self):
        """Test that AdvantageType.NONE returns original rolls."""
        parser = DiceParser(seed=42)
        original_rolls = parser.roll_dice(2, 6)

        selected, all_rolls = parser.apply_advantage(original_rolls, AdvantageType.NONE)

        assert selected == original_rolls
        assert all_rolls == original_rolls

    def test_apply_advantage_advantage(self):
        """Test advantage mechanism."""
        parser = DiceParser(seed=42)
        original_rolls = parser.roll_dice(2, 6)

        selected, all_rolls = parser.apply_advantage(original_rolls, AdvantageType.ADVANTAGE)

        assert len(selected) == len(original_rolls)
        assert len(all_rolls) == len(original_rolls) * 2
        # Each selected roll should be >= its corresponding original
        for i in range(len(original_rolls)):
            original = original_rolls[i]
            extra = all_rolls[len(original_rolls) + i]
            selected_roll = selected[i]
            assert selected_roll.result == max(original.result, extra.result)

    def test_apply_advantage_disadvantage(self):
        """Test disadvantage mechanism."""
        parser = DiceParser(seed=42)
        original_rolls = parser.roll_dice(2, 6)

        selected, all_rolls = parser.apply_advantage(original_rolls, AdvantageType.DISADVANTAGE)

        assert len(selected) == len(original_rolls)
        assert len(all_rolls) == len(original_rolls) * 2
        # Each selected roll should be <= its corresponding original
        for i in range(len(original_rolls)):
            original = original_rolls[i]
            extra = all_rolls[len(original_rolls) + i]
            selected_roll = selected[i]
            assert selected_roll.result == min(original.result, extra.result)

    def test_roll_standard_dice(self):
        """Test complete standard dice rolling."""
        parser = DiceParser(seed=42)

        result = parser.roll("2d6+3")
        assert result.expression == "2d6+3"
        assert result.dice_type == DiceType.STANDARD
        assert len(result.individual_rolls) == 2
        assert result.modifier == 3
        assert result.advantage == AdvantageType.NONE
        assert result.total == sum(roll.result for roll in result.individual_rolls) + 3
        assert result.d66_composed is None
        assert "=" in result.breakdown
        assert str(result.total) in result.breakdown

    def test_roll_standard_dice_with_advantage(self):
        """Test standard dice rolling with advantage."""
        parser = DiceParser(seed=42)

        result = parser.roll("1d20", AdvantageType.ADVANTAGE)
        assert result.dice_type == DiceType.STANDARD
        assert result.advantage == AdvantageType.ADVANTAGE
        assert "adv" in result.breakdown

    def test_roll_standard_dice_with_disadvantage(self):
        """Test standard dice rolling with disadvantage."""
        parser = DiceParser(seed=42)

        result = parser.roll("1d20", AdvantageType.DISADVANTAGE)
        assert result.dice_type == DiceType.STANDARD
        assert result.advantage == AdvantageType.DISADVANTAGE
        assert "dis" in result.breakdown

    def test_roll_d66_ordered(self):
        """Test D66 rolling (ordered)."""
        parser = DiceParser(seed=42)

        result = parser.roll("d66")
        assert result.expression == "d66"
        assert result.dice_type == DiceType.D66
        assert len(result.individual_rolls) == 2
        assert result.modifier == 0
        assert result.advantage == AdvantageType.NONE
        assert result.d66_composed is not None
        assert 11 <= result.d66_composed <= 66
        assert result.total == result.d66_composed
        assert "d66:" in result.breakdown
        assert str(result.d66_composed) in result.breakdown

    def test_roll_d66_unordered(self):
        """Test D66 rolling (unordered)."""
        parser = DiceParser(seed=42)

        result = parser.roll("d66u")
        assert result.expression == "d66u"
        assert result.dice_type == DiceType.D66_UNORDERED
        assert len(result.individual_rolls) == 2
        assert result.d66_composed is not None
        assert "sorted:" in result.breakdown

    def test_roll_d66_with_modifier(self):
        """Test D66 rolling with modifier."""
        parser = DiceParser(seed=42)

        result = parser.roll("D66+5")
        assert result.modifier == 5
        assert result.d66_composed is not None
        assert result.total == result.d66_composed + 5
        assert "+5" in result.breakdown


class TestRollDiceFunction:
    """Test cases for the convenience roll_dice function."""

    def test_roll_dice_basic(self):
        """Test basic functionality of roll_dice function."""
        result = roll_dice("2d6", seed=42)
        assert isinstance(result, RollResult)
        assert result.expression == "2d6"
        assert result.dice_type == DiceType.STANDARD

    def test_roll_dice_with_advantage(self):
        """Test roll_dice with advantage."""
        result = roll_dice("1d20", seed=42, advantage=True)
        assert result.advantage == AdvantageType.ADVANTAGE

    def test_roll_dice_with_disadvantage(self):
        """Test roll_dice with disadvantage."""
        result = roll_dice("1d20", seed=42, disadvantage=True)
        assert result.advantage == AdvantageType.DISADVANTAGE

    def test_roll_dice_advantage_and_disadvantage_error(self):
        """Test that specifying both advantage and disadvantage raises an error."""
        with pytest.raises(ValueError, match="Cannot specify both advantage and disadvantage"):
            roll_dice("1d20", advantage=True, disadvantage=True)

    def test_roll_dice_reproducible(self):
        """Test that same seed produces same results."""
        result1 = roll_dice("2d6+3", seed=42)
        result2 = roll_dice("2d6+3", seed=42)

        assert result1.total == result2.total
        assert [roll.result for roll in result1.individual_rolls] == [
            roll.result for roll in result2.individual_rolls
        ]

    def test_roll_dice_different_seeds(self):
        """Test that different seeds can produce different results."""
        # With different seeds, we should eventually get different results
        # Run multiple times to reduce chance of coincidental same results
        results1 = [roll_dice("2d6", seed=i).total for i in range(10)]
        results2 = [roll_dice("2d6", seed=i + 100).total for i in range(10)]

        # At least some results should be different
        assert results1 != results2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_dice_expressions(self):
        """Test various invalid dice expressions."""
        invalid_expressions = [
            "0d6",  # Zero count
            "1d0",  # Zero size
            "-1d6",  # Negative count
            "1d-6",  # Negative size
            "abc",  # Non-numeric
        ]

        for expr in invalid_expressions:
            with pytest.raises(DiceExpressionError):
                roll_dice(expr)

    def test_large_dice_expressions(self):
        """Test handling of large but valid dice expressions."""
        # Should not crash with reasonable large values
        result = roll_dice("10d10+50", seed=42)
        assert result.dice_type == DiceType.STANDARD
        assert len(result.individual_rolls) == 10
        assert result.modifier == 50

    def test_case_insensitive(self):
        """Test that dice expressions are case-insensitive."""
        result1 = roll_dice("d66", seed=42)
        result2 = roll_dice("D66", seed=42)
        assert result1.total == result2.total

        result3 = roll_dice("d66u", seed=42)
        result4 = roll_dice("D66U", seed=42)
        assert result3.total == result4.total


class TestDiceRollDataclass:
    """Test the DiceRoll dataclass."""

    def test_dice_roll_creation(self):
        """Test creating DiceRoll instances."""
        roll = DiceRoll(die_size=6, result=4)
        assert roll.die_size == 6
        assert roll.result == 4


class TestRollResultDataclass:
    """Test the RollResult dataclass."""

    def test_roll_result_creation(self):
        """Test creating RollResult instances."""
        rolls = [DiceRoll(die_size=6, result=3), DiceRoll(die_size=6, result=5)]
        result = RollResult(
            expression="2d6+1",
            dice_type=DiceType.STANDARD,
            individual_rolls=rolls,
            modifier=1,
            advantage=AdvantageType.NONE,
            total=9,
            breakdown="[3, 5] +1 = 9",
        )

        assert result.expression == "2d6+1"
        assert result.dice_type == DiceType.STANDARD
        assert result.individual_rolls == rolls
        assert result.modifier == 1
        assert result.advantage == AdvantageType.NONE
        assert result.total == 9
        assert result.breakdown == "[3, 5] +1 = 9"
        assert result.d66_composed is None


# This file contains GitHub Copilot generated content.
