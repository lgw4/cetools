"""FR-047b, SC-018: supplying a name changes nothing else about the
character a seed produces (research R3). Written before the walk existed
in spirit: the natural implementation — rolling the name from the walk's
own roller — fails exactly this while passing everything else.
"""

import dataclasses

from cetools.dice import Roller
from cetools.generator import generate_character
from cetools.rules import load_rules

RULES = load_rules()


def test_supplying_a_name_changes_only_the_naming_fields():
    unnamed = generate_character(Roller("session-alpha"), RULES)
    named = generate_character(Roller("session-alpha"), RULES, name="Alex Rivera")

    unnamed_fields = dataclasses.asdict(unnamed)
    named_fields = dataclasses.asdict(named)

    naming_fields = {"name", "given_name", "surname", "surname_region"}
    for field in naming_fields:
        del unnamed_fields[field]
        del named_fields[field]

    assert unnamed_fields == named_fields
    assert named.name == "Alex Rivera"
    assert named.given_name == ""
    assert named.surname == ""
    assert named.surname_region == ""
