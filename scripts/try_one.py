"""Run one real model call on one prescription image.

Phase 1 check. It resizes the image, makes one call to GLM 5.3 Flash, and prints
the raw reply and the seconds taken. Use --save to keep the raw text under
eval/results/ (text only, never the photo).

    python scripts/try_one.py path/to/prescription.jpg
    python scripts/try_one.py path/to/prescription.jpg --save
"""

import argparse
import sys
import time
from pathlib import Path

# Allow "python scripts/try_one.py" from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.extract import (  # noqa: E402
    build_client,
    call_model,
    get_api_key,
    load_prompt,
    write_raw_output,
)
from app.image_utils import image_info, prepare_image  # noqa: E402
from app.parse_utils import parse_payload  # noqa: E402
from app.schema import ExtractionResult  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACT_PROMPT = PROJECT_ROOT / "prompts" / "extract_prompt.txt"
RAW_OUTPUT = PROJECT_ROOT / "eval" / "results" / "try_one_raw.json"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One model call on one prescription image.")
    parser.add_argument("image", help="path to a prescription photo")
    parser.add_argument("--save", action="store_true", help="save the raw reply under eval/results/")
    args = parser.parse_args(argv)

    path = Path(args.image)
    if not path.is_file():
        print(f"error: no such file: {path}")
        return 2

    print(f"model      {config.MODEL_ID}")
    print(f"endpoint   {config.API_BASE_URL}")

    try:
        api_key = get_api_key()
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 2

    original = path.read_bytes()
    try:
        info = image_info(original)
    except Exception as exc:
        print(f"error: could not read the image: {type(exc).__name__}")
        return 2
    print(
        f"input      {info['width']}x{info['height']} {info['mode']} {info['format']} "
        f"({len(original) / 1024:.0f} KB)"
    )

    jpeg = prepare_image(original)
    print(f"prepared   {len(jpeg) / 1024:.0f} KB JPEG, longest side {config.MAX_IMAGE_SIDE} px cap")

    prompt = load_prompt(EXTRACT_PROMPT)
    client = build_client(api_key)

    print("calling the model ...")
    started = time.perf_counter()
    raw_text, error = call_model(client, prompt, jpeg)
    seconds = time.perf_counter() - started

    if error:
        print(f"\nFAILED after {seconds:.1f} s")
        print(f"  {error}")
        return 1

    print(f"\nmodel reply ({seconds:.1f} s, {len(raw_text)} chars)\n")
    print("-" * 68)
    print(raw_text)
    print("-" * 68)

    payload, parse_error = parse_payload(raw_text)
    if parse_error:
        print(f"\nJSON: FAILED to parse - {parse_error}")
    else:
        result = ExtractionResult.model_validate(payload)
        print(f"\nJSON: parsed, {len(result.medicines)} medicine row(s)")
        for item in result.medicines:
            print(
                f"  name={item.name!r} strength={item.strength!r} "
                f"timing={item.timing_code!r} duration={item.duration!r} "
                f"confidence={item.confidence} unclear={item.unclear}"
            )
        if result.notes:
            print(f"  notes: {result.notes}")

    if args.save:
        write_raw_output(RAW_OUTPUT, path, raw_text, seconds)
        print(f"\nsaved raw reply to {RAW_OUTPUT.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())