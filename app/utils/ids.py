import random
import string
from typing import Callable, Set


def generate_short_id(existing: Set[str] | None = None) -> str:
    """
    Generates IDs like abcd-1234-5 with low collision probability.
    Ensures uniqueness against provided existing set if given.
    """
    existing = existing or set()
    while True:
        prefix = "".join(random.choices(string.ascii_lowercase, k=4))
        mid = "".join(random.choices(string.digits, k=4))
        suffix = random.choice(string.digits)
        candidate = f"{prefix}-{mid}-{suffix}"
        if candidate not in existing:
            return candidate


def make_unique(generator: Callable[[], str], existing: Set[str]) -> str:
    candidate = generator()
    while candidate in existing:
        candidate = generator()
    return candidate
