"""Dice expression parser and roll engine for Cepheus Engine."""

import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

from .config import get_config_value


class DiceType(Enum):
    """Types of dice expressions supported."""

    STANDARD = "standard"  # 2d6+3, 1d20, etc.
    D66 = "d66"  # Special Cepheus Engine d66 roll
    D66_UNORDERED = "d66u"  # Unordered d66 variant


class AdvantageType(Enum):
    """Types of advantage/disadvantage rolls."""

    NONE = "none"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


@dataclass
class DiceRoll:
    """Result of a single die roll."""

    die_size: int
    result: int


@dataclass
class RollResult:
    """Complete result of a dice expression evaluation."""

    expression: str
    dice_type: DiceType
    individual_rolls: List[DiceRoll]
    modifier: int
    advantage: AdvantageType
    total: int
    breakdown: str
    d66_composed: Optional[int] = None  # For D66 rolls only


class DiceExpressionError(Exception):
    """Raised when a dice expression cannot be parsed."""

    pass


class DiceParser:
    """Parser for dice expressions with Cepheus Engine support."""

    # Regex patterns for different dice expressions
    STANDARD_PATTERN = re.compile(
        r"^(?P<count>\d+)?d(?P<size>\d+)(?P<modifier>[+\-]\d+)?$", re.IGNORECASE
    )
    D66_PATTERN = re.compile(r"^d66(?P<unordered>u)?(?P<modifier>[+\-]\d+)?$", re.IGNORECASE)

    def __init__(self, seed: Optional[int] = None):
        """Initialize the dice parser with optional seed for reproducible results."""
        self._rng = random.Random(seed)

    def parse_expression(self, expression: str) -> Tuple[DiceType, dict]:
        """
        Parse a dice expression and return the type and parameters.

        Args:
            expression: The dice expression to parse

        Returns:
            Tuple of (DiceType, parameters dict)

        Raises:
            DiceExpressionError: If expression cannot be parsed
        """
        expression = expression.strip()

        # Try D66 pattern first
        d66_match = self.D66_PATTERN.match(expression)
        if d66_match:
            dice_type = DiceType.D66_UNORDERED if d66_match.group("unordered") else DiceType.D66
            modifier = int(d66_match.group("modifier") or "0")
            return dice_type, {"modifier": modifier}

        # Try standard dice pattern
        std_match = self.STANDARD_PATTERN.match(expression)
        if std_match:
            count = int(std_match.group("count") or "1")
            size = int(std_match.group("size"))
            modifier = int(std_match.group("modifier") or "0")

            if count <= 0 or size <= 0:
                raise DiceExpressionError("Dice count and size must be positive")

            return DiceType.STANDARD, {"count": count, "size": size, "modifier": modifier}

        raise DiceExpressionError(f"Invalid dice expression: {expression}")

    def roll_dice(self, count: int, size: int) -> List[DiceRoll]:
        """Roll multiple dice of the same size."""
        return [DiceRoll(die_size=size, result=self._rng.randint(1, size)) for _ in range(count)]

    def roll_d66(self, unordered: bool = False) -> Tuple[List[DiceRoll], int]:
        """
        Roll a D66 (two d6 composed into a single value).

        Args:
            unordered: If True, sort dice descending before composition

        Returns:
            Tuple of (list of DiceRoll objects, composed D66 value)
        """
        # Use config to determine default behavior if not explicitly specified
        if not unordered:
            unordered = get_config_value("dice", "d66_unordered", False)

        rolls = self.roll_dice(2, 6)
        die1, die2 = rolls[0].result, rolls[1].result

        if unordered:
            # Sort descending for unordered D66
            die1, die2 = sorted([die1, die2], reverse=True)

        composed = die1 * 10 + die2
        return rolls, composed

    def apply_advantage(
        self, rolls: List[DiceRoll], advantage: AdvantageType
    ) -> Tuple[List[DiceRoll], List[DiceRoll]]:
        """
        Apply advantage/disadvantage to dice rolls.

        Args:
            rolls: Original dice rolls
            advantage: Type of advantage to apply

        Returns:
            Tuple of (selected rolls, all rolls including extras)
        """
        if advantage == AdvantageType.NONE:
            return rolls, rolls

        # For advantage/disadvantage, we need to roll extra dice
        extra_rolls = []
        for roll in rolls:
            extra_roll = DiceRoll(
                die_size=roll.die_size, result=self._rng.randint(1, roll.die_size)
            )
            extra_rolls.append(extra_roll)

        all_rolls = rolls + extra_rolls

        # Select the best/worst dice based on advantage type
        selected_rolls = []
        for i in range(len(rolls)):
            original = rolls[i]
            extra = extra_rolls[i]

            if advantage == AdvantageType.ADVANTAGE:
                selected = original if original.result >= extra.result else extra
            else:  # DISADVANTAGE
                selected = original if original.result <= extra.result else extra

            selected_rolls.append(selected)

        return selected_rolls, all_rolls

    def roll(
        self,
        expression: str,
        advantage: AdvantageType = AdvantageType.NONE,
    ) -> RollResult:
        """
        Roll a dice expression and return the complete result.

        Args:
            expression: Dice expression to roll
            advantage: Advantage/disadvantage type

        Returns:
            RollResult with complete information about the roll
        """
        dice_type, params = self.parse_expression(expression)

        if dice_type == DiceType.STANDARD:
            count = params["count"]
            size = params["size"]
            modifier = params["modifier"]

            # Roll the dice
            initial_rolls = self.roll_dice(count, size)

            # Apply advantage/disadvantage if specified
            if advantage != AdvantageType.NONE:
                selected_rolls, all_rolls = self.apply_advantage(initial_rolls, advantage)
                breakdown_rolls = all_rolls
            else:
                selected_rolls = initial_rolls
                breakdown_rolls = initial_rolls

            # Calculate total
            dice_total = sum(roll.result for roll in selected_rolls)
            final_total = dice_total + modifier

            # Build breakdown string
            breakdown_parts = []
            if advantage != AdvantageType.NONE:
                adv_str = "adv" if advantage == AdvantageType.ADVANTAGE else "dis"
                all_results = [str(roll.result) for roll in breakdown_rolls]
                selected_results = [str(roll.result) for roll in selected_rolls]
                breakdown_parts.append(
                    f"[{', '.join(all_results)}] ({adv_str}: {', '.join(selected_results)})"
                )
            else:
                results = [str(roll.result) for roll in selected_rolls]
                breakdown_parts.append(f"[{', '.join(results)}]")

            if modifier != 0:
                op = "+" if modifier >= 0 else ""
                breakdown_parts.append(f" {op}{modifier}")

            breakdown = "".join(breakdown_parts) + f" = {final_total}"

            return RollResult(
                expression=expression,
                dice_type=dice_type,
                individual_rolls=selected_rolls,
                modifier=modifier,
                advantage=advantage,
                total=final_total,
                breakdown=breakdown,
            )

        elif dice_type in (DiceType.D66, DiceType.D66_UNORDERED):
            modifier = params["modifier"]
            unordered = dice_type == DiceType.D66_UNORDERED

            # Roll D66
            rolls, composed = self.roll_d66(unordered)
            final_total = composed + modifier

            # Build breakdown string
            roll_str = f"d66: {rolls[0].result},{rolls[1].result}"
            if unordered:
                sorted_dice = sorted([rolls[0].result, rolls[1].result], reverse=True)
                roll_str += f" (sorted: {sorted_dice[0]},{sorted_dice[1]})"
            roll_str += f" → {composed}"

            if modifier != 0:
                op = "+" if modifier >= 0 else ""
                roll_str += f" {op}{modifier} = {final_total}"

            return RollResult(
                expression=expression,
                dice_type=dice_type,
                individual_rolls=rolls,
                modifier=modifier,
                advantage=advantage,
                total=final_total,
                breakdown=roll_str,
                d66_composed=composed,
            )

        else:
            raise DiceExpressionError(f"Unsupported dice type: {dice_type}")


def roll_dice(
    expression: str,
    seed: Optional[int] = None,
    advantage: bool = False,
    disadvantage: bool = False,
) -> RollResult:
    """
    Convenience function to roll dice with a simple interface.

    Args:
        expression: Dice expression to roll
        seed: Optional seed for reproducible results
        advantage: Roll with advantage
        disadvantage: Roll with disadvantage

    Returns:
        RollResult with complete roll information
    """
    if advantage and disadvantage:
        raise ValueError("Cannot specify both advantage and disadvantage")

    adv_type = AdvantageType.NONE
    if advantage:
        adv_type = AdvantageType.ADVANTAGE
    elif disadvantage:
        adv_type = AdvantageType.DISADVANTAGE

    parser = DiceParser(seed=seed)
    return parser.roll(expression, advantage=adv_type)


# This file contains GitHub Copilot generated content.
