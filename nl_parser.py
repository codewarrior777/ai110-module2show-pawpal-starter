"""Natural language parser for PawPal+ tasks.

Converts free-form text like "walk Cooper at 7am daily, high priority"
into structured task data.

This module uses deterministic regex-based parsing (no LLM required).

Examples:
    >>> from nl_parser import parse_task
    >>> parse_task("walk Cooper at 7am daily, high priority", ["Cooper"])
    ParsedTask(description='Walk Cooper', time='07:00', frequency='daily',
               priority='high', pet_name='Cooper')
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass


# ----------------------------------------------------------------------
# Result type
# ----------------------------------------------------------------------
@dataclass
class ParsedTask:
    """Structured output of a natural language task description."""

    description: str
    time: str
    frequency: str = "once"
    priority: str = "medium"
    pet_name: str | None = None

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict."""
        return asdict(self)


# ----------------------------------------------------------------------
# Token patterns
# ----------------------------------------------------------------------
_TIME_PATTERN = re.compile(
    r"""
    \b
    (?P<hour>\d{1,2})
    (?::(?P<minute>\d{2}))?
    \s*
    (?P<meridiem>am|pm|AM|PM)?
    \b
    """,
    re.VERBOSE,
)

_FREQUENCY_PATTERNS = [
    (re.compile(r"\b(every\s*day|daily)\b", re.IGNORECASE), "daily"),
    (re.compile(r"\b(every\s*week|weekly)\b", re.IGNORECASE), "weekly"),
    (re.compile(r"\b(once|one[\s-]?time|just once)\b", re.IGNORECASE), "once"),
]

_PRIORITY_PATTERNS = [
    (re.compile(r"\b(high|urgent|critical|important)\b", re.IGNORECASE), "high"),
    (re.compile(r"\b(medium|normal|regular)\b", re.IGNORECASE), "medium"),
    (re.compile(r"\b(low|minor|eventually)\b", re.IGNORECASE), "low"),
]

# Connective words and date modifiers that pollute the description.
_NOISE_PATTERN = re.compile(
    r"""
    \b(
        at|on|for|every|each|the|a|an|
        priority|prio|
        next\s*week|this\s*week|next\s*month|
        tomorrow|today|tonight|
        every\s*day|every\s*week
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ----------------------------------------------------------------------
# Extractors
# ----------------------------------------------------------------------
def _extract_time(text: str) -> tuple[str | None, str]:
    """Find the first time-like token. Returns (HH:MM, cleaned_text)."""
    for match in _TIME_PATTERN.finditer(text):
        hour = int(match.group("hour"))
        minute = int(match.group("minute") or 0)
        meridiem = (match.group("meridiem") or "").lower()

        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            continue

        time_str = f"{hour:02d}:{minute:02d}"
        cleaned = text[: match.start()] + " " + text[match.end() :]
        return time_str, cleaned

    return None, text


def _extract_frequency(text: str) -> tuple[str, str]:
    """Return (frequency, cleaned_text). Defaults to 'once'."""
    for pattern, freq in _FREQUENCY_PATTERNS:
        match = pattern.search(text)
        if match:
            cleaned = text[: match.start()] + " " + text[match.end() :]
            return freq, cleaned
    return "once", text


def _extract_priority(text: str) -> tuple[str, str]:
    """Return (priority, cleaned_text). Defaults to 'medium'."""
    for pattern, prio in _PRIORITY_PATTERNS:
        match = pattern.search(text)
        if match:
            cleaned = text[: match.start()] + " " + text[match.end() :]
            return prio, cleaned
    return "medium", text


def _extract_pet_name(text: str, known_pets: list[str]) -> tuple[str | None, str]:
    """Find the first known pet name (case-insensitive)."""
    for pet in known_pets:
        pattern = re.compile(rf"\b{re.escape(pet)}\b", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            cleaned = text[: match.start()] + " " + text[match.end() :]
            return pet, cleaned
    return None, text


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def parse_task(text: str, known_pets: list[str] | None = None) -> ParsedTask:
    """
    Parse free-form text into a ParsedTask.

    Args:
        text: The natural language description.
        known_pets: List of registered pet names to match against.

    Returns:
        A ParsedTask with description, time, frequency, priority,
        and optional pet_name.

    Raises:
        ValueError: if no time could be extracted.

    Examples:
        >>> parse_task("walk Cooper at 7am daily, high priority", ["Cooper"])
        ParsedTask(description='Walk Cooper', time='07:00', frequency='daily',
                   priority='high', pet_name='Cooper')
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty.")

    working = text.strip()

    # 1. Strip noise words (connectives + date modifiers)
    working = _NOISE_PATTERN.sub(" ", working)

    # 2. Extract pet name from a COPY (pet name MUST stay in description)
    pet_name, _ = _extract_pet_name(working, known_pets or [])

    # 3. Extract the rest, mutating `working`
    frequency, working = _extract_frequency(working)
    priority, working = _extract_priority(working)
    time_str, working = _extract_time(working)

    if time_str is None:
        raise ValueError(
            f"Could not find a time in: {text!r}. "
            "Try formats like '7am', '7:30pm', or '14:00'."
        )

    # 4. Clean up the remaining description
    description = re.sub(r"[\s,]+", " ", working).strip(" ,.-")
    if not description:
        description = "Task"

    description = description[0].upper() + description[1:]

    return ParsedTask(
        description=description,
        time=time_str,
        frequency=frequency,
        priority=priority,
        pet_name=pet_name,
    )


# ----------------------------------------------------------------------
# Smoke test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    examples = [
        ("walk Cooper at 7am daily, high priority", ["Cooper", "Prince"]),
        ("feed the cat at 18:30", ["Prince"]),
        ("vet visit for Prince at 2pm next week", ["Cooper", "Prince"]),
        ("playtime with Cooper at 3:15pm, low priority", ["Cooper"]),
        ("Morning grooming at 09:00", []),
    ]

    print("=" * 70)
    print("Natural Language Parser — Smoke Test")
    print("=" * 70)

    for text, pets in examples:
        try:
            result = parse_task(text, pets)
            print(f"\nInput:  {text!r}")
            print(f"Output: {result.to_dict()}")
        except ValueError as e:
            print(f"\nInput:  {text!r}")
            print(f"Error:  {e}")
