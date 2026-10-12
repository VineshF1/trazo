"""Evaluation harness: score the pipeline against a verified answer key.

    python eval/run_eval.py --mode baseline
    python eval/run_eval.py --mode pipeline
    python eval/run_eval.py --mode pipeline --final

Reads images from tests_local/prescriptions/ and answers from eval/expected.csv.
Runs the same model on the same images in both modes. Writes a results CSV and a
markdown table under eval/results/.

Group B only runs with --final, and it is meant to be used once.
"""

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import MODEL_ID, PAIRING_THRESHOLD  # noqa: E402
from app.extract import (  # noqa: E402
    build_client,
    call_model,
    get_api_key,
    load_prompt,
    write_raw_output,
)
from app.image_utils import prepare_image  # noqa: E402
from app.medicines import read_all  # noqa: E402
from app.parse_utils import parse_payload  # noqa: E402
from app.schema import STATUS_UNCLEAR, ExtractionResult  # noqa: E402
from scoring import markdown_table, pair_and_score, summarize  # noqa: E402

MODES = ("baseline", "pipeline")
PROMPTS = {
    "baseline": PROJECT_ROOT / "prompts" / "baseline_prompt.txt",
    "pipeline": PROJECT_ROOT / "prompts" / "extract_prompt.txt",
}
PRESCRIPTIONS_DIR = PROJECT_ROOT / "tests_local" / "prescriptions"
EXPECTED_CSV = PROJECT_ROOT / "eval" / "expected.csv"
RESULTS_DIR = PROJECT_ROOT / "eval" / "results"
RAW_DIR = RESULTS_DIR / "raw"

EXTRA_KEY_COLUMNS = {"group", "kind", "image_file", "medicine_name", "strength", "timing_code", "duration"}


def load_expected(path) -> dict[str, list[dict]]:
    """Read the answer key, grouped by image file."""
    if not Path(path).is_file():
        raise SystemExit(
            f"error: no answer key at {path}.\n"
            "Create it with these columns: image_file, group, kind, medicine_name, "
            "strength, timing_code, duration"
        )
    by_image: dict[str, list[dict]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = set(reader.fieldnames or [])
        missing = EXTRA_KEY_COLUMNS - header
        if missing:
            raise SystemExit("error: the answer key is missing columns: " + ", ".join(sorted(missing)))
        for row in reader:
            image = (row.get("image_file") or "").strip()
            if not image:
                continue
            by_image.setdefault(image, []).append(row)
    return by_image


def run_one(mode: str, image_path: Path, prompt: str, medicines: list[dict], client):
    """One image through one mode. Returns (rows, raw_text, seconds, error)."""
    started = time.perf_counter()
    try:
        jpeg = prepare_image(image_path.read_bytes())
    except Exception as exc:
        return [], "", 0.0, f"could not read the image: {type(exc).__name__}"
    try:
        raw_text, error = call_model(client, prompt, jpeg)
    except Exception as exc:
        return [], "", time.perf_counter() - started, f"{type(exc).__name__}: {exc}"
    seconds = time.perf_counter() - started
    if error:
        return [], raw_text, seconds, error

    payload, parse_error = parse_payload(raw_text)
    if parse_error:
        return [], raw_text, seconds, parse_error

    result = ExtractionResult.model_validate(payload)
    if mode == "pipeline":
        from app.pipeline import build_rows

        return build_rows(result, medicines), raw_text, seconds, None

    # Baseline: same JSON fields, no matching, no decoder, no flags. Never flagged.
    rows = [
        {
            "name": item.name,
            "strength": item.strength,
            "timing_code": item.timing_code,
            "duration": item.duration,
            "unclear": False,
            "status": "",  # no status in baseline, so the row can never be flagged
        }
        for item in result.medicines
    ]
    return rows, raw_text, seconds, None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Score the pipeline against the answer key.")
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument(
        "--final",
        action="store_true",
        help="include group B. It is meant to be used once, for the reported numbers.",
    )
    args = parser.parse_args(argv)
    mode = args.mode

    if args.final:
        print(
            "WARNING: --final includes group B. Group B is meant to be used once, for the "
            "reported numbers. Do not tune on it."
        )

    prompt_path = PROMPTS[mode]
    if not prompt_path.is_file():
        raise SystemExit(f"error: no prompt at {prompt_path}")
    prompt = load_prompt(prompt_path)

    key = load_expected(EXPECTED_CSV)
    medicines = read_all()
    if mode == "pipeline" and not medicines:
        print(
            "WARNING: the medicine list is empty. Every row will be flagged as unmatched. "
            "Load it first with scripts/load_medicines.py."
        )

    groups = {"A"} if not args.final else {"A", "B"}
    selected = {image: rows for image, rows in key.items() if (rows[0].get("group") or "A").strip() in groups}
    if not selected:
        raise SystemExit(
            "error: no images selected. Check the group column in the answer key, and that the "
            "images are in tests_local/prescriptions/."
        )

    client = build_client(get_api_key())

    items = []
    seconds_per_image: dict[str, float] = {}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for image in sorted(selected):
        image_path = PRESCRIPTIONS_DIR / image
        key_rows = selected[image]
        group = (key_rows[0].get("group") or "A").strip()
        kind = (key_rows[0].get("kind") or "printed").strip().lower()
        if not image_path.is_file():
            print(f"  skip {image}: not in {PRESCRIPTIONS_DIR}")
            continue

        rows, raw_text, seconds, error = run_one(mode, image_path, prompt, medicines, client)
        seconds_per_image[image] = seconds
        write_raw_output(RAW_DIR / f"{run_id}__{mode}__{image}.json", image_path, raw_text, seconds)
        if error:
            print(f"  {image}: FAILED - {error}")
            continue

        image_items = pair_and_score(image, group, kind, rows, key_rows, pairing_threshold=PAIRING_THRESHOLD)
        items.extend(image_items)
        print(f"  {image}: {len(rows)} row(s) read, {len(image_items)} scored, {seconds:.1f} s")

    if not items:
        raise SystemExit("error: nothing was scored. No results were written.")

    summary = summarize(items, seconds_per_image, total_images=len(seconds_per_image))

    csv_path = RESULTS_DIR / f"{run_id}__{mode}__items.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(items[0].as_dict()))
        writer.writeheader()
        for item in items:
            writer.writerow(item.as_dict())

    table = markdown_table(summary)
    table_path = RESULTS_DIR / f"{run_id}__{mode}__summary.md"
    table_path.write_text(
        f"# Trazo evaluation: {mode}\n\n"
        f"- run: {run_id}\n- model: {MODEL_ID}\n- groups: {', '.join(sorted(groups))}\n"
        f"- mode: {mode}\n\n{table}\n",
        encoding="utf-8",
    )

    print()
    print(table)
    print()
    print(f"raw replies : {RAW_DIR}")
    print(f"per item    : {csv_path.name}")
    print(f"summary     : {table_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())