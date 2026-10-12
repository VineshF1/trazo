"""Timing code decoder.

Every code in the dictionary is translated to plain words. Any code that is not
in the dictionary, including a missing one, is shown exactly as written and
flagged. A meaning is never guessed.
"""

from dataclasses import dataclass

TIMING = {
    "1-0-1": "Morning and night",
    "1-1-1": "Morning, afternoon and night",
    "1-0-0": "Morning only",
    "0-0-1": "Night only",
    "0-1-0": "Afternoon only",
    "OD": "Once a day",
    "BD": "Twice a day",
    "TDS": "Three times a day",
    "QID": "Four times a day",
    "SOS": "Only when needed",
    "HS": "At bedtime",
    "AC": "Before food",
    "PC": "After food",
}


@dataclass(frozen=True)
class Timing:
    """The decoded timing.

    meaning: plain words when the code is known, otherwise None.
    known: whether the code was in the dictionary.
    raw: the code exactly as written on the page, or None if there was none.
    """

    meaning: str | None
    known: bool
    raw: str | None

    @property
    def display(self) -> str:
        """What to show the user. Always the real reading, never an invented one."""
        if self.known:
            return self.meaning or ""
        return self.raw or ""


def decode(code) -> Timing:
    """Decode one timing code.

    A known code returns its meaning. An unknown code returns the code as written
    and is flagged. A missing code returns nothing and is flagged.
    """
    if code is None:
        return Timing(meaning=None, known=False, raw=None)
    raw = str(code).strip()
    if not raw:
        return Timing(meaning=None, known=False, raw=None)
    key = raw.upper()
    if key in TIMING:
        return Timing(meaning=TIMING[key], known=True, raw=raw)
    return Timing(meaning=None, known=False, raw=raw)