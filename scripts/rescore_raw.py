"""Re-run the pipeline matching on saved raw model replies (no API calls).

Shows, for every row the model read in the last eval run, what status the
fixed matcher now gives. This is what the app would display.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.match import match_name  # noqa: F401  (import checks wiring)
from app.medicines import read_all
from app.parse_utils import parse_payload
from app.pipeline import build_rows
from app.schema import ExtractionResult

RAW_DIR = Path(__file__).resolve().parent.parent / "eval" / "results" / "raw"
RUN_PREFIX = "20261112T015348Z"  # latest completed pipeline run

medicines = read_all()
for path in sorted(RAW_DIR.glob(f"{RUN_PREFIX}__pipeline__*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("raw_text") or ""
    image = data.get("image_file", path.name)
    payload, error = parse_payload(raw)
    if error or payload is None:
        print(f"\n== {image}: parse error: {error}")
        continue
    result = ExtractionResult.model_validate(payload)
    rows = build_rows(result, medicines)
    print(f"\n== {image}")
    for row in rows:
        name = row["name"] or "(unreadable)"
        print(f"   {name:24} {row['status']:10} {row['reason'][:70]}")
