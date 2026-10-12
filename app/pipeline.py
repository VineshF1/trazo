"""The full reading pipeline: extraction, matching, timing, status, corrections.

This is the one place the steps are combined, so the API and the evaluation
harness cannot drift apart. Everything here works on data passed in: no file is
written, and no photo is stored.
"""

from app.config import SAFETY_BANNER
from app.corrections import find_suggestion
from app.extract import run_extraction
from app.match import match_name
from app.schema import STATUS_CHECK, STATUS_OK, ExtractionResult
from app.status import decide_status
from app.timing import decode


def build_rows(
    result: ExtractionResult,
    medicines: list[dict],
    corrections_db=None,
    use_corrections: bool = True,
) -> list[dict]:
    """Turn one extraction into the rows the API and the results CSV carry.

    Each row has the reading, the decoded timing in plain words, the status word
    and a plain-words reason for any flag.
    """
    rows = []
    for item in result.medicines:
        match = match_name(item.name, medicines)
        timing = decode(item.timing_code)
        status = decide_status(match, timing, item)

        suggestion = find_suggestion(item.name, corrections_db, medicines) if use_corrections else None

        row = {
            "name": item.name,
            "strength": item.strength,
            "duration": item.duration,
            "timing_code": item.timing_code,
            "timing_text": timing.display,
            "timing_known": timing.known,
            "status": status.status,
            "reason": status.reason,
            "unclear": item.is_flagged_unclear,
            "candidates": _candidates(match),
            "suggestion": suggestion,
        }
        rows.append(_keep_suggestion_flagged(row, suggestion))
    return rows


def _candidates(match) -> list[dict]:
    out = []
    if match.best is not None:
        out.append(
            {
                "brand_name": match.best.brand_name,
                "generic_name": match.best.generic_name,
                "strength": match.best.strength,
                "matched_field": match.best.matched_field,
                "score": round(match.best.score, 1),
            }
        )
    for candidate in match.close:
        out.append(
            {
                "brand_name": candidate.brand_name,
                "generic_name": candidate.generic_name,
                "strength": candidate.strength,
                "matched_field": candidate.matched_field,
                "score": round(candidate.score, 1),
            }
        )
    return out


def _keep_suggestion_flagged(row: dict, suggestion: str | None) -> dict:
    """A learned suggestion never makes a row OK.

    If there is a suggestion and the row passed every check, it is moved to
    "Check this" and the reason says so. A correction is a hint, never a confirmation.
    """
    if not suggestion:
        return row
    if row["status"] == STATUS_OK:
        row["status"] = STATUS_CHECK
        row["reason"] = (
            f"{row['reason']} A saved correction suggests {suggestion}. "
            "Confirm it before relying on it."
        )
    elif suggestion not in row["reason"]:
        row["reason"] = f"{row['reason']} A saved correction suggests {suggestion}."
    return row


def process(
    image_bytes: bytes,
    prompt: str,
    medicines: list[dict] | None = None,
    client=None,
    corrections_db=None,
    use_corrections: bool = True,
) -> tuple[dict | None, str, str | None]:
    """The whole pipeline for one image.

    Returns (payload, raw_text, error). The payload carries the rows plus the
    safety banner, which goes on every result.
    """
    result, raw_text, error = run_extraction(image_bytes, prompt, client=client)
    if error:
        return None, raw_text, error

    rows = build_rows(
        result,
        medicines if medicines is not None else [],
        corrections_db=corrections_db,
        use_corrections=use_corrections,
    )
    return (
        {
            "medicines": rows,
            "notes": result.notes,
            "banner": SAFETY_BANNER,
        },
        raw_text,
        None,
    )
