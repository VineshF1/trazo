"""Row status from the checks in section 8 of the build prompt.

A row is OK only if every check passes: the model did not flag it unclear, the
medicine name was accepted by the match, the timing code is known, and no second
medicine name is close enough to make the reading ambiguous. Anything else is
"Check this" or "Unclear", always with a short reason.
"""

from dataclasses import dataclass, field

from app.match import MatchKind, MatchResult
from app.config import MATCH_CLOSE_MARGIN
from app.schema import STATUS_CHECK, STATUS_OK, STATUS_UNCLEAR
from app.timing import Timing

ACCEPTABLE_STATUSES = (STATUS_OK, STATUS_CHECK, STATUS_UNCLEAR)


@dataclass(frozen=True)
class StatusResult:
    """The status word for one row, and why it was given."""

    status: str
    reasons: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return self.status == STATUS_OK

    @property
    def is_unclear(self) -> bool:
        return self.status == STATUS_UNCLEAR

    @property
    def reason(self) -> str:
        """The reasons as one sentence, for the row's detail text."""
        return " ".join(self.reasons)


def decide_status(match: MatchResult, timing: Timing, item) -> StatusResult:
    """Apply the status rule to one row.

    The checks are evaluated in order, and every failing check adds a reason. The
    reason is written in plain words, because the user sees it.
    """
    reasons: list[str] = []
    unclear = False

    if item is not None and item.is_flagged_unclear:
        unclear = True
        name = getattr(item, "name", None)
        if name is None:
            reasons.append("the medicine name could not be read.")
        else:
            reasons.append("the model was not confident of this reading.")

    if match.kind is MatchKind.NOT_FOUND or match.best is None:
        unclear = True
        reasons.append(match.reason or "no medicine on the list matches this name.")
    elif match.kind is MatchKind.REVIEW:
        reasons.append(f"did you mean {match.best.brand_name}? {match.reason}.")

    if not timing.known:
        unclear = True
        if timing.raw:
            reasons.append(f"the timing code {timing.raw!r} is not one this app knows.")
        else:
            reasons.append("no timing was written for this medicine.")

    if match.close:
        unclear = True
        others = ", ".join(candidate.brand_name for candidate in match.close)
        reasons.append(
            f"another medicine scores within {MATCH_CLOSE_MARGIN} points: {others}."
        )

    if unclear:
        status = STATUS_UNCLEAR
    elif reasons:
        status = STATUS_CHECK
    else:
        status = STATUS_OK
        reasons.append("every check passed.")

    return StatusResult(status=status, reasons=reasons)