"""Verified-correction table.

The app improves from corrections a user makes, never from its own readings. It
does not retrain the model; it stores text around it.

What is stored: the text the model read, and what the user typed. No photo, no user
id, no timestamp of a person. A suggestion from this table always keeps the row
flagged "Check this": a learned correction never replaces a reading silently.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import CORRECTIONS_DB_PATH
from app.medicines import read_all

CREATE_CORRECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY,
    raw_text TEXT NOT NULL,
    corrected_name TEXT NOT NULL,
    times_confirmed INTEGER DEFAULT 1,
    verified INTEGER DEFAULT 0,
    created_at TEXT
)
"""


@dataclass(frozen=True)
class Correction:
    """One stored correction."""

    id: int
    raw_text: str
    corrected_name: str
    times_confirmed: int
    verified: bool
    created_at: str


def connect(db_path=None) -> sqlite3.Connection:
    path = CORRECTIONS_DB_PATH if db_path is None else db_path
    path = str(path)
    if path != ":memory:":
        from pathlib import Path

        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(CREATE_CORRECTIONS_TABLE)
    return connection


def normalize_raw(text) -> str:
    """How a stored reading is matched against a new reading."""
    return " ".join(str(text or "").split()).casefold()


def is_verified(corrected_name: str, medicines: list[dict] | None = None) -> bool:
    """A correction is verified only if the corrected name is in the medicine list.

    TODO: add the second rule the human chooses (for example, confirmed more than
    once) before this table is used to influence anything.
    """
    if not corrected_name or not str(corrected_name).strip():
        return False
    medicines = read_all() if medicines is None else medicines
    target = normalize_raw(corrected_name)
    for medicine in medicines:
        for field in ("brand_name", "generic_name"):
            if normalize_raw(medicine.get(field)) == target:
                return True
    return False


def save_correction(
    raw_text: str,
    corrected_name: str,
    db_path=None,
    medicines: list[dict] | None = None,
) -> Correction:
    """Store one correction, or confirm it again if the same pair is already stored.

    Only text is written. The same raw_text with a different corrected_name adds a
    separate row rather than overwriting: two users disagreeing is information.
    """
    raw_text = (raw_text or "").strip()
    corrected_name = (corrected_name or "").strip()
    if not raw_text:
        raise ValueError("raw_text is empty: there is no reading to correct")
    if not corrected_name:
        raise ValueError("corrected_name is empty: nothing was entered")

    verified = is_verified(corrected_name, medicines)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    connection = connect(db_path)
    try:
        existing = connection.execute(
            "SELECT id, times_confirmed FROM corrections WHERE raw_text = ? AND corrected_name = ?",
            (raw_text, corrected_name),
        ).fetchone()
        if existing is not None:
            connection.execute(
                "UPDATE corrections SET times_confirmed = times_confirmed + 1, verified = ? WHERE id = ?",
                (1 if verified else 0, existing["id"]),
            )
            connection.commit()
            row = connection.execute("SELECT * FROM corrections WHERE id = ?", (existing["id"],)).fetchone()
        else:
            cursor = connection.execute(
                "INSERT INTO corrections (raw_text, corrected_name, times_confirmed, verified, created_at) "
                "VALUES (?, ?, 1, ?, ?)",
                (raw_text, corrected_name, 1 if verified else 0, now),
            )
            connection.commit()
            row = connection.execute("SELECT * FROM corrections WHERE id = ?", (cursor.lastrowid,)).fetchone()
    finally:
        connection.close()
    return _row_to_correction(row)


def find_suggestion(raw_text, db_path=None, medicines: list[dict] | None = None) -> str | None:
    """The corrected name stored for this reading, if there is one and it is verified.

    Only verified corrections are suggested. The caller must keep the row flagged:
    a suggestion is never applied silently.
    """
    key = normalize_raw(raw_text)
    if not key:
        return None
    try:
        connection = connect(db_path)
    except sqlite3.Error:
        return None
    try:
        rows = connection.execute(
            "SELECT * FROM corrections WHERE verified = 1 ORDER BY times_confirmed DESC, id"
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        connection.close()

    medicines = read_all() if medicines is None else medicines
    for row in rows:
        if normalize_raw(row["raw_text"]) == key and is_verified(row["corrected_name"], medicines):
            return row["corrected_name"]
    return None


def read_all_rows(db_path=None) -> list[Correction]:
    """Every stored correction, for tests and for the report."""
    try:
        connection = connect(db_path)
    except sqlite3.Error:
        return []
    try:
        rows = connection.execute("SELECT * FROM corrections ORDER BY id").fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    return [_row_to_correction(row) for row in rows]


def _row_to_correction(row) -> Correction:
    return Correction(
        id=row["id"],
        raw_text=row["raw_text"],
        corrected_name=row["corrected_name"],
        times_confirmed=row["times_confirmed"],
        verified=bool(row["verified"]),
        created_at=row["created_at"],
    )