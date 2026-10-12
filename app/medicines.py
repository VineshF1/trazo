"""Medicine list storage.

The medicine list is a CSV the human supplies, with the columns
brand_name, generic_name, strength, use. It is loaded into SQLite. Nothing is
downloaded, and no dataset is committed to the repository.

Coverage is reported honestly: a medicine that is not in this list cannot be
matched, and that is a limit of the list, not a failure of the model.
"""

import csv
import sqlite3
from pathlib import Path

from app.config import MEDICINES_DB_PATH

REQUIRED_COLUMNS = ("brand_name", "generic_name", "strength", "use")

CREATE_MEDICINES_TABLE = """
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY,
    brand_name TEXT NOT NULL,
    generic_name TEXT,
    strength TEXT,
    use TEXT
)
"""


class MedicineListError(ValueError):
    """The CSV cannot be used as a medicine list."""


def resolve(db_path=None) -> str:
    """The database path as a string, from the argument or from config."""
    path = MEDICINES_DB_PATH if db_path is None else db_path
    return str(path)


def connect(db_path=None) -> sqlite3.Connection:
    """Open the medicine database, creating the folder and table.

    This is for writing. `read_all` deliberately does not use it, so that reading
    the list never creates an empty database.
    """
    path = resolve(db_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(CREATE_MEDICINES_TABLE)
    return connection


def read_csv(csv_path) -> list[dict]:
    """Read and validate the medicine CSV. Raises MedicineListError with a reason."""
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise MedicineListError("the CSV has no header row")

        header = [name.strip() for name in reader.fieldnames]
        missing = [name for name in REQUIRED_COLUMNS if name not in header]
        if missing:
            raise MedicineListError(
                "the CSV is missing these columns: " + ", ".join(missing)
            )

        rows = []
        for raw in reader:
            row = {key.strip(): (value or "").strip() for key, value in raw.items() if key}
            brand = row.get("brand_name", "")
            if not brand:
                continue  # a row with no brand name cannot be matched to anything
            rows.append(
                {
                    "brand_name": brand,
                    "generic_name": row.get("generic_name") or None,
                    "strength": row.get("strength") or None,
                    "use": row.get("use") or None,
                }
            )
    if not rows:
        raise MedicineListError("the CSV contains no medicine rows")
    return rows


def replace_all(connection: sqlite3.Connection, medicines: list[dict]) -> int:
    """Replace the table contents with these medicines. Returns the row count."""
    connection.execute("DELETE FROM medicines")
    connection.executemany(
        "INSERT INTO medicines (brand_name, generic_name, strength, use) VALUES (?, ?, ?, ?)",
        [
            (
                item["brand_name"],
                item.get("generic_name"),
                item.get("strength"),
                item.get("use"),
            )
            for item in medicines
        ],
    )
    connection.commit()
    return len(medicines)


def load_csv_into_db(csv_path, db_path=None) -> tuple[int, list[dict]]:
    """Read the CSV and replace the database contents. Returns (count, rows)."""
    medicines = read_csv(csv_path)
    connection = connect(db_path)
    try:
        count = replace_all(connection, medicines)
    finally:
        connection.close()
    return count, medicines


def read_all(db_path=None) -> list[dict]:
    """Every medicine, in insertion order.

    Returns an empty list when the list is not loaded. It never creates a database:
    reading must not leave a file behind, and a missing list is a normal state, not
    an error.
    """
    path = resolve(db_path)
    if path != ":memory:" and not Path(path).is_file():
        return []

    try:
        connection = sqlite3.connect(path)
    except sqlite3.Error:
        return []
    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT brand_name, generic_name, strength, use FROM medicines ORDER BY id"
        ).fetchall()
    except sqlite3.Error:
        return []  # the file exists but has no medicines table yet
    finally:
        connection.close()
    return [dict(row) for row in rows]
