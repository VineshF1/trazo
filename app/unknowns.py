"""Names the human verified online as not being any medicine.

Each entry in data/unknown_names.csv was searched on pharmacy sites; no
medicine exists under that name. A read name matching one of these is
flagged with wording that says so, instead of a generic Check this.
The status vocabulary stays OK / Check this / Unclear.
"""

import csv
from pathlib import Path

from app.config import MEDICINES_DB_PATH
from app.match import normalize

UNKNOWN_NAMES_PATH = Path(MEDICINES_DB_PATH).parent / "unknown_names.csv"


def read_unknown_names(path=None) -> dict[str, str]:
    """Normalized name -> note. A missing file means the feature is off."""
    csv_path = Path(path) if path else UNKNOWN_NAMES_PATH
    if not csv_path.exists():
        return {}
    out: dict[str, str] = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("name") or "").strip()
            if name:
                out[normalize(name)] = (row.get("note") or "").strip()
    return out
