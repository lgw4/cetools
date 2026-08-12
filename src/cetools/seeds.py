import hashlib
import re
import secrets

_DIGIT_STRING = re.compile(r"^[+-]?[0-9]+$")


def resolve_seed(seed: int | str | None) -> int:
    """Resolve a caller-supplied seed to the integer a `Roller` is built from.

    `None` draws 64 bits from `secrets`. An `int` is used as given. A string
    of digits (optionally signed) is read as that integer, so a seed echoed
    back by a previous run round-trips exactly. Any other string is folded
    with a blake2b-64 digest over its UTF-8 bytes, never handed to
    `random.Random` directly (see research.md R1, R2).
    """
    if seed is None:
        return secrets.randbits(64)
    if isinstance(seed, int):
        return seed
    if _DIGIT_STRING.match(seed):
        return int(seed)
    digest = hashlib.blake2b(seed.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")
