"""Robust parsing of the model's JSON reply.

The model is asked to return only JSON. In practice it can wrap the JSON in a
markdown fence, put text around it, or return something that is not JSON at all.
This module extracts the object if it can, and reports failure if it cannot. It
never invents fields, and it never returns a partially decoded guess.
"""

import json
import re

_ANY_FENCE = re.compile(r"```(.*?)```", re.DOTALL)
_KEEP_QUIET = ("", "json", "json5")


def strip_code_fences(text: str) -> str:
    """Unwrap a markdown fence. Returns the inner text if one is found."""
    match = _ANY_FENCE.search(text)
    if not match:
        return text
    inner = match.group(1).strip()
    first, _, rest = inner.partition("\n")
    if first.strip().lower() in _KEEP_QUIET:
        return rest.strip() if first.strip() else inner
    return inner


def iter_json_objects(text: str):
    """Yield every balanced top-level object in the text, left to right.

    Scanning rather than regex-matching means braces inside string values do not
    end the object early. Trying each opening brace means prose that contains an
    earlier, unrelated brace pair does not stop the real object from being found.
    """
    for start, char in enumerate(text):
        if char != "{":
            continue
        candidate = _balanced_object(text, start)
        if candidate is not None:
            yield candidate


def _balanced_object(text: str, start: int) -> str | None:
    depth_curly = 0
    depth_square = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth_curly += 1
        elif char == "}":
            depth_curly -= 1
            if depth_curly == 0:
                return text[start : index + 1]
        elif char == "[":
            depth_square += 1
        elif char == "]":
            depth_square -= 1
            if depth_square < 0:
                return None
    return None


def parse_payload(text):
    """Parse the model's reply into a dict.

    Returns (payload, error). Exactly one of the two is None. The text is tried
    as-is, then with markdown fences stripped, then by scanning for a balanced
    object inside it.
    """
    if text is None:
        return None, "empty response"
    raw = str(text).strip()
    if not raw:
        return None, "empty response"

    attempts = [raw]
    unfenced = strip_code_fences(raw).strip()
    if unfenced and unfenced != raw:
        attempts.append(unfenced)

    for attempt in attempts:
        value = _try_json(attempt)
        if isinstance(value, dict):
            return value, None
        if value is not None:
            return None, f"JSON was valid but not an object ({type(value).__name__})"
        for candidate in iter_json_objects(attempt):
            value = _try_json(candidate)
            if isinstance(value, dict):
                return value, None
    return None, "no JSON object found"


def _try_json(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None