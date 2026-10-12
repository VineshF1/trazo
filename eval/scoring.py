"""Scoring and pairing for the evaluation harness.

The rules are described in section 8 of the build prompt and can be changed by the
human in eval/scoring_rules.md. Where that file is silent, the rules here apply.
Every pairing decision is returned, so the results CSV can be audited.

No number in this module is a result. It only counts what it was given.
"""

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from app.config import PAIRING_THRESHOLD
from app.schema import STATUS_OK, STATUS_UNCLEAR

# Outcome groups. The third one is the safety number that matters.
CORRECT = "correct"
WRONG_FLAGGED = "wrong_but_flagged"
DANGEROUS = "wrong_and_not_flagged"

_PUNCTUATION = re.compile(r"[^a-z0-9]+")


def normalize_timing(code) -> str:
    """Timing comparison form: strip, uppercase. Same normalization as the decoder."""
    if code is None:
        return ""
    return str(code).strip().upper()


def normalize_name(name) -> str:
    """Comparison form: lowercase, with spaces and punctuation removed.

    So "Dolo 650", "dolo650" and "DOLO-650" are the same string.
    """
    return _PUNCTUATION.sub("", str(name or "").casefold())


def names_equal(left, right) -> bool:
    """Whether two medicine names count as the same medicine.

    TODO: replace with the equivalence rules in eval/scoring_rules.md once the
    human has filled them in. Until then: lowercase, and drop spaces and
    punctuation. So "Dolo 650" equals "dolo650" but not "Paracetamol".
    """
    return normalize_name(left) == normalize_name(right)


def _similarity(left, right) -> float:
    return float(fuzz.ratio(normalize_name(left), normalize_name(right)))


@dataclass
class Item:
    """One scored medicine row: the pairing, the checks, and the outcome."""

    image_file: str
    group: str
    kind: str
    outcome: str
    origin: str  # "paired", "missed" or "extra"
    key_name: str | None = None
    model_name: str | None = None
    status: str = ""
    key_timing: str = ""
    model_timing: str = ""
    name_correct: bool | None = None
    timing_correct: bool | None = None
    pair_score: float | None = None
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "image_file": self.image_file,
            "group": self.group,
            "kind": self.kind,
            "origin": self.origin,
            "outcome": self.outcome,
            "key_name": self.key_name or "",
            "model_name": self.model_name or "",
            "status": self.status,
            "key_timing": self.key_timing,
            "model_timing": self.model_timing,
            "name_correct": _tri(self.name_correct),
            "timing_correct": _tri(self.timing_correct),
            "pair_score": "" if self.pair_score is None else round(self.pair_score, 1),
            "note": self.note,
        }


def _tri(value):
    if value is None:
        return ""
    return "yes" if value else "no"


def pair_and_score(
    image_file: str,
    group: str,
    kind: str,
    model_rows: list[dict],
    key_rows: list[dict],
    fields: tuple[str, ...] = ("name", "timing"),
    pairing_threshold: float = PAIRING_THRESHOLD,
) -> list[Item]:
    """Pair one image's model rows with its answer-key rows, then score them.

    Steps, in order: pair one to one by name similarity, highest first; pair
    leftover unreadable model rows with leftover key rows in reading order; then
    count whatever is left over as missed (key rows) or extra (model rows).
    """
    if not key_rows:
        return []

    key_names = [row.get("medicine_name") for row in key_rows]
    remaining_models = list(range(len(model_rows)))
    remaining_keys = list(range(len(key_rows)))
    items: list[Item] = []

    for key_index, model_index, score in _greedy_pairs(model_rows, key_names, pairing_threshold):
        remaining_models.remove(model_index)
        remaining_keys.remove(key_index)
        items.append(
            _score_pair(image_file, group, kind, model_rows[model_index], key_rows[key_index], fields, score)
        )

    # Leftover unreadable rows pair with leftover key rows in reading order.
    unreadable = [i for i in remaining_models if model_rows[i].get("unclear")]
    for model_index in unreadable:
        if not remaining_keys:
            break
        key_index = remaining_keys.pop(0)
        remaining_models.remove(model_index)
        items.append(
            _score_pair(
                image_file,
                group,
                kind,
                model_rows[model_index],
                key_rows[key_index],
                fields,
                None,
                note="paired to an unreadable row in reading order",
            )
        )

    for key_index in remaining_keys:
        items.append(
            Item(
                image_file=image_file,
                group=group,
                kind=kind,
                outcome=DANGEROUS,
                origin="missed",
                key_name=key_rows[key_index].get("medicine_name"),
                key_timing=normalize_timing(key_rows[key_index].get("timing_code")),
                note="no model row was paired with this medicine",
            )
        )

    for model_index in remaining_models:
        row = model_rows[model_index]
        flagged = _is_flagged(row)
        items.append(
            Item(
                image_file=image_file,
                group=group,
                kind=kind,
                outcome=WRONG_FLAGGED if flagged else DANGEROUS,
                origin="extra",
                model_name=row.get("name"),
                status=row.get("status", ""),
                model_timing=normalize_timing(row.get("timing_code")),
                note="this medicine is not in the answer key",
            )
        )

    items.sort(key=lambda item: (item.origin, item.key_name or item.model_name or ""))
    return items


def _greedy_pairs(model_rows, key_names, threshold):
    """Pair by name similarity, highest score first, each row used once."""
    scored = []
    for model_index, row in enumerate(model_rows):
        for key_index, key_name in enumerate(key_names):
            score = _similarity(row.get("name"), key_name)
            if score >= threshold:
                scored.append((score, model_index, key_index))
    scored.sort(key=lambda triple: -triple[0])

    used_models = set()
    used_keys = set()
    pairs = []
    for score, model_index, key_index in scored:
        if model_index in used_models or key_index in used_keys:
            continue
        used_models.add(model_index)
        used_keys.add(key_index)
        pairs.append((key_index, model_index, score))
    return pairs


def _score_pair(image_file, group, kind, model_row, key_row, fields, pair_score, note="") -> Item:
    name_ok = names_equal(model_row.get("name"), key_row.get("medicine_name"))
    timing_ok = _timing_ok(model_row, key_row)
    checked = []
    if "name" in fields:
        checked.append(name_ok)
    if "timing" in fields:
        checked.append(timing_ok)

    correct = all(checked)
    flagged = _is_flagged(model_row)
    outcome = CORRECT if correct else (WRONG_FLAGGED if flagged else DANGEROUS)
    return Item(
        image_file=image_file,
        group=group,
        kind=kind,
        outcome=outcome,
        origin="paired",
        key_name=key_row.get("medicine_name"),
        model_name=model_row.get("name"),
        status=model_row.get("status", ""),
        key_timing=normalize_timing(key_row.get("timing_code")),
        model_timing=normalize_timing(model_row.get("timing_code")),
        name_correct=name_ok,
        timing_correct=timing_ok,
        pair_score=pair_score,
        note=note,
    )


def _timing_ok(model_row, key_row) -> bool:
    return normalize_timing(model_row.get("timing_code")) == normalize_timing(key_row.get("timing_code"))


def _is_flagged(row) -> bool:
    """A row is flagged unless its status is OK.

    The baseline has no status field, so baseline rows are never flagged. Section
    8 of the build prompt requires that: every wrong baseline item is dangerous.
    """
    status = row.get("status")
    if status is None or status == "":
        return False
    return status != STATUS_OK


def summarize(items: list[Item], seconds_per_image: dict | None = None, total_images: int = 0) -> dict:
    """Counts and rates for one run. Printed or handwritten reported separately."""
    total = len(items)
    counts = {CORRECT: 0, WRONG_FLAGGED: 0, DANGEROUS: 0}
    for item in items:
        counts[item.outcome] = counts.get(item.outcome, 0) + 1

    compared = [item for item in items if item.origin == "paired"]
    name_right = sum(1 for item in compared if item.name_correct)
    timing_right = sum(1 for item in compared if item.timing_correct)
    unclear_flags = sum(1 for item in items if item.status == STATUS_UNCLEAR)

    summary = {
        "items": total,
        "paired": len(compared),
        "missed": sum(1 for item in items if item.origin == "missed"),
        "extra": sum(1 for item in items if item.origin == "extra"),
        "correct": counts[CORRECT],
        "wrong_but_flagged": counts[WRONG_FLAGGED],
        "wrong_and_not_flagged": counts[DANGEROUS],
        "name_accuracy": _rate(name_right, len(compared)),
        "timing_accuracy": _rate(timing_right, len(compared)),
        "unclear_rate": _rate(unclear_flags, total),
        "by_kind": {},
        "images": total_images,
        "seconds_per_image": _mean(list((seconds_per_image or {}).values())),
    }
    for kind in sorted({item.kind for item in items}):
        subset = [item for item in items if item.kind == kind]
        summary["by_kind"][kind] = {
            "items": len(subset),
            "correct": sum(1 for item in subset if item.outcome == CORRECT),
            "wrong_but_flagged": sum(1 for item in subset if item.outcome == WRONG_FLAGGED),
            "wrong_and_not_flagged": sum(1 for item in subset if item.outcome == DANGEROUS),
            "missed": sum(1 for item in subset if item.origin == "missed"),
            "name_accuracy": _rate(
                sum(1 for item in subset if item.name_correct), len([i for i in subset if i.origin == "paired"])
            ),
        }
    return summary


def _rate(numerator: int, denominator: int):
    if not denominator:
        return None  # no items: a rate would be meaningless, so it is reported as blank
    return round(numerator / denominator, 3)


def _mean(values: list[float]):
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def markdown_table(summary: dict) -> str:
    """The results table. Every cell comes from the counts, never from a template."""
    lines = [
        "| Metric | Value |",
        "|---|---|",
        f"| Images | {summary['images']} |",
        f"| Items scored | {summary['items']} |",
        f"| Correct | {summary['correct']} |",
        f"| Wrong but flagged | {summary['wrong_but_flagged']} |",
        f"| Wrong and NOT flagged (dangerous) | {summary['wrong_and_not_flagged']} |",
        f"| Missed medicines | {summary['missed']} |",
        f"| Extra medicines | {summary['extra']} |",
        f"| Name accuracy | {_cell(summary['name_accuracy'])} |",
        f"| Timing accuracy | {_cell(summary['timing_accuracy'])} |",
        f"| Unclear rate | {_cell(summary['unclear_rate'])} |",
        f"| Seconds per image | {_cell(summary['seconds_per_image'])} |",
    ]
    if summary["by_kind"]:
        lines += ["", "| Kind | Items | Correct | Wrong but flagged | Dangerous | Missed | Name accuracy |", "|---|---|---|---|---|---|---|"]
        for kind, block in summary["by_kind"].items():
            lines.append(
                f"| {kind} | {block['items']} | {block['correct']} | {block['wrong_but_flagged']} | "
                f"{block['wrong_and_not_flagged']} | {block['missed']} | {_cell(block['name_accuracy'])} |"
            )
    return "\n".join(lines)


def _cell(value) -> str:
    return "n/a" if value is None else str(value)