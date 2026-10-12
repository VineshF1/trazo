"""Schema for one extraction result, and the normalization applied to it.

The schema follows section 8 of the build prompt. Normalization never invents a
value: a field that is missing, empty or unreadable stays null, and an item whose
readability cannot be confirmed is marked unclear.
"""

from pydantic import BaseModel, ConfigDict, field_validator

# Status words. Fixed strings, used by status.py and the API.
STATUS_OK = "OK"
STATUS_CHECK = "Check this"
STATUS_UNCLEAR = "Unclear"


class MedicineItem(BaseModel):
    """One medicine row as read from the page."""

    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    strength: str | None = None
    timing_code: str | None = None
    duration: str | None = None
    confidence: float = 0.0
    unclear: bool | None = None

    @field_validator("name", "strength", "timing_code", "duration", mode="before")
    @classmethod
    def _text(cls, value):
        """Coerce a scalar to text and treat blank as missing.

        A number such as 650 is what was written on the page, so it is kept as
        text rather than discarded. An empty or whitespace-only string carries no
        reading, so it becomes null instead of looking like a readable value.
        """
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        if isinstance(value, (int, float, bool)):
            return str(value)
        return None

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence(cls, value):
        """Keep the model's confidence signal inside 0.0 to 1.0, or 0.0."""
        if value is None:
            return 0.0
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        return min(1.0, max(0.0, number))

    @field_validator("unclear", mode="before")
    @classmethod
    def _unclear(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip().lower() in {"true", "yes", "1"}
        return bool(value)

    @property
    def is_flagged_unclear(self) -> bool:
        """True unless the model positively stated the row is readable.

        Only an explicit false means readability was confirmed. A missing flag
        means it was never confirmed, so the row is treated as unclear. This is the
        safe direction: it can add a flag, it can never remove one.
        """
        return self.unclear is not False


class ExtractionResult(BaseModel):
    """The whole page: the medicine rows plus a note about what was unreadable."""

    model_config = ConfigDict(extra="ignore")

    medicines: list[MedicineItem] = []
    notes: str = ""

    @field_validator("notes", mode="before")
    @classmethod
    def _notes(cls, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value)