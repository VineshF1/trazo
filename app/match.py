"""Medicine name matching against the loaded medicine list.

Every name the model read is compared against both the brand and the generic name
of every medicine in the list. Two close candidates are both returned: the module
never picks one silently.

If the medicine list has not been loaded, every row comes back as "not found" with
a reason saying so. That is a limit of the list, not a failure of the reading.
"""

import re
from dataclasses import dataclass, field
from enum import Enum

from rapidfuzz import fuzz

from app.config import MATCH_ACCEPT, MATCH_CLOSE_MARGIN, MATCH_REVIEW
from app.medicines import read_all

_SPACE = re.compile(r"\s+")


class MatchKind(str, Enum):
    ACCEPT = "accept"
    REVIEW = "review"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class Candidate:
    """One medicine the read name might be, and how close it scored."""

    brand_name: str
    generic_name: str | None
    strength: str | None
    matched_field: str
    score: float


@dataclass(frozen=True)
class MatchResult:
    """The outcome of matching one read name."""

    query: str | None
    kind: MatchKind
    best: Candidate | None = None
    close: list[Candidate] = field(default_factory=list)
    reason: str = ""

    @property
    def is_ok(self) -> bool:
        """Accepted, with no second medicine close enough to be ambiguous."""
        return self.kind is MatchKind.ACCEPT and not self.close

    @property
    def suggestion(self) -> str | None:
        """The "Did you mean ...?" text, when there is a candidate to show."""
        if self.best is None:
            return None
        return self.best.brand_name


def normalize(text: str) -> str:
    """Fold case and collapse whitespace. Used before comparing."""
    return _SPACE.sub(" ", (text or "").strip()).casefold()


def match_name(name, medicines=None, threshold=None) -> MatchResult:
    """Match one read name against the medicine list.

    Scores at or above the accept threshold are a match. Scores between the review
    and accept thresholds are a suggested match. Below the review threshold, or a
    missing name, is not found. In every non-accepted case a reason is given.
    """
    threshold = MATCH_ACCEPT if threshold is None else threshold
    query = normalize(name) if name else ""

    if medicines is None:
        medicines = read_all()

    if not medicines:
        return MatchResult(
            query=name,
            kind=MatchKind.NOT_FOUND,
            reason="the medicine list is not loaded, so no name can be matched",
        )

    if not query:
        return MatchResult(
            query=name,
            kind=MatchKind.NOT_FOUND,
            reason="no medicine name to match",
        )

    scored = _score_all(query, medicines)
    if not scored:
        return MatchResult(query=name, kind=MatchKind.NOT_FOUND, reason="no medicine name to match")

    best_score, best = scored[0]
    if best_score >= threshold:
        return MatchResult(
            query=name,
            kind=MatchKind.ACCEPT,
            best=best,
            close=_close_candidates(scored),
            reason=f"matched {best.brand_name} at {best_score:.0f}",
        )

    if best_score >= MATCH_REVIEW:
        return MatchResult(
            query=name,
            kind=MatchKind.REVIEW,
            best=best,
            close=_close_candidates(scored),
            reason=f"best candidate {best.brand_name} scored {best_score:.0f}, below the accept threshold {threshold}",
        )

    return MatchResult(
        query=name,
        kind=MatchKind.NOT_FOUND,
        best=best,
        reason=f"best candidate {best.brand_name} scored {best_score:.0f}, below the review threshold {MATCH_REVIEW}",
    )


def _score_all(query: str, medicines: list[dict]) -> list[tuple[float, Candidate]]:
    """Every medicine scored against the query, highest first.

    A medicine is scored on both its brand and its generic name; its best field
    decides its score. Ties keep the order the medicines were loaded in.
    """
    scored = []
    for medicine in medicines:
        brand = medicine.get("brand_name") or ""
        generic = medicine.get("generic_name") or ""
        best_field = None
        best_score = -1.0
        for field_name, value in (("brand_name", brand), ("generic_name", generic)):
            if not value:
                continue
            score = fuzz.ratio(query, normalize(value))
            if score > best_score:
                best_score = score
                best_field = field_name
        if best_field is None:
            continue
        scored.append(
            (
                float(best_score),
                Candidate(
                    brand_name=brand,
                    generic_name=medicine.get("generic_name"),
                    strength=medicine.get("strength"),
                    matched_field=best_field,
                    score=float(best_score),
                ),
            )
        )
    scored.sort(key=lambda pair: -pair[0])
    return scored


def _close_candidates(scored: list[tuple[float, Candidate]]) -> list[Candidate]:
    """Candidates scoring within the close margin of the best one.

    Only medicines other than the best are considered, so an exact match against
    both the brand and the generic name of the same medicine is not ambiguous.
    """
    if not scored:
        return []
    best_score, best = scored[0]
    close = []
    for score, candidate in scored[1:]:
        if best_score - score > MATCH_CLOSE_MARGIN:
            break
        if candidate.brand_name == best.brand_name and candidate.matched_field == best.matched_field:
            continue
        close.append(candidate)
    return close