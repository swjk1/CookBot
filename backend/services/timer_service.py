import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pattern: matches "X hours Y minutes", "X minutes", "X seconds", etc.
_TIME_PATTERN = re.compile(
    r"""
    (?:(\d+)\s*h(?:ours?)?[\s,]*)?   # hours (optional)
    (?:(\d+)\s*m(?:in(?:utes?)?)?)   # minutes (optional)
    (?:\s*(?:and\s*)?(\d+)\s*s(?:ec(?:onds?)?)?)? # seconds (optional)
    """,
    re.IGNORECASE | re.VERBOSE,
)

_SIMPLE_PATTERN = re.compile(
    r"(\d+)\s*(hour|hr|minute|min|second|sec)s?",
    re.IGNORECASE,
)


def extract_duration_seconds(text: str) -> Optional[int]:
    """Extract the first time duration from text, return total seconds or None."""
    total = 0
    found = False

    for m in _SIMPLE_PATTERN.finditer(text):
        value = int(m.group(1))
        unit = m.group(2).lower()
        if unit in ("hour", "hr"):
            total += value * 3600
        elif unit in ("minute", "min"):
            total += value * 60
        elif unit in ("second", "sec"):
            total += value
        found = True

    return total if found else None
