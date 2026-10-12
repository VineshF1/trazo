"""Load a medicine CSV into SQLite.

The CSV is supplied by the human and is never committed. It must have the columns
brand_name, generic_name, strength, use.

    python scripts/load_medicines.py path/to/medicines.csv
    python scripts/load_medicines.py path/to/medicines.csv --db data/medicines.db
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import MEDICINES_DB_PATH  # noqa: E402
from app.medicines import MedicineListError, load_csv_into_db  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Load a medicine CSV into SQLite.")
    parser.add_argument("csv", help="path to the medicine CSV")
    parser.add_argument("--db", default=None, help=f"database path (default {MEDICINES_DB_PATH})")
    args = parser.parse_args(argv)

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        print(f"error: no such file: {csv_path}")
        return 2

    try:
        count, _ = load_csv_into_db(csv_path, args.db)
    except MedicineListError as exc:
        print(f"error: {exc}")
        return 2
    except OSError as exc:
        print(f"error: could not read the CSV: {exc}")
        return 2

    print(f"loaded {count} medicine(s) into {args.db or MEDICINES_DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())