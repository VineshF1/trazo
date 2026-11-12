"""Configuration for Trazo.

Every numeric value in this file is a starting guess taken from the project plan.
Each one must be tuned on the development set (Group A) on the real data. Nothing
here is a measured result.
"""

from pathlib import Path

# --- Application identity ---
APP_NAME = "Trazo"
APP_VERSION = "0.1.0"

# --- Model ---
# Nemotron 3.5 Super VL 120B on NVIDIA Build (same endpoint and key as the earlier
# GLM 5.3 Flash setup). Switched 2026-11-12 after GLM's endpoint hung repeatedly:
# Nemotron answered the test sheet in 26 s with a correct full JSON read.
# It is a reasoning model: max_tokens must cover the thinking budget (4096),
# and the GLM-only reasoning_effort param is not sent (see app/extract.py).
MODEL_ID = "nvidia/nemotron-3.5-super-vl-120b-a12b"
API_BASE_URL = "https://integrate.api.nvidia.com/v1"
API_KEY_ENV_VAR = "NVIDIA_API_KEY"
MODEL_TEMPERATURE = 0.0
# Cap on the reply length. Nemotron's thinking pass improves its handwriting
# reads materially (tested 2026-11-12: thinking off = 3 dangerous errors), and
# one dense sheet thought past 8192 tokens; 16384 gives it room to finish.
MODEL_MAX_TOKENS = 16384
# The model card documents a thinking budget via `reasoning_effort` (low/high/max,
# default max) and says chat scenarios should pass `clear_thinking=true` explicitly.
# Neither is sent yet: Phase 1 tests the plain request format from the plan first.
MODEL_TIMEOUT_SECONDS = 600  # starting guess
# Model-card tuning (checked 2026-11-11): the card documents a thinking budget via
# reasoning_effort (low/high/max, default max). The default burned past the timeout
# on real handwriting, so the eval sends low-effort reasoning. The card also mentions
# clear_thinking=true, but the live endpoint rejects it (HTTP 400: unsupported
# parameter) — verified 2026-11-12, so it is NOT sent.
MODEL_REASONING_EFFORT = "low"

# --- Image handling ---
MAX_IMAGE_SIDE = 1600  # starting guess: longest side after resize, pixels
JPEG_QUALITY = 0.8  # starting guess

# --- Medicine name matching ---
MATCH_ACCEPT = 90  # starting guess: score at or above this is an accepted match
MATCH_REVIEW = 70  # starting guess: between review and accept -> "Check this"
# Close-margin raised 5 -> 8 after Group A tuning (2026-11-12): the model read
# "ELOOPAR" as "ELDOPAR"; Elopar (a different, real brand) accepted at 92.9 with
# the true Eloopar at 85.7 — just past the old margin, producing a confident
# wrong match. A margin of 8 turns that into an ambiguity flag instead.
MATCH_CLOSE_MARGIN = 8
# Pairing threshold lowered 60 -> 55 after Group A tuning (2026-11-12): the
# model misread "HCQ" as "HCG"; against key "HCQS" that scores 57 — just under
# 60, so the row went unpaired (counted missed+extra) instead of paired and
# flagged. Pairing only lines rows up for comparison; names_equal and the
# status checks still decide correctness, so a slightly lower threshold is safe.
PAIRING_THRESHOLD = 55  # eval pairing threshold

# --- Upload limits ---
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # starting guess: largest accepted photo

# --- Photo quality check ---
# All starting guesses. Tune these on your own photos before trusting them.
BLUR_MIN_VARIANCE = 100.0  # variance of the Laplacian; below this the photo is blurry
BRIGHTNESS_MIN = 60.0  # mean grey value; below this the photo is too dark
BRIGHTNESS_MAX = 245.0  # above this the frame is blown out. A clean white page
# photographed at mean ~218 must pass, so this ceiling is set near the top of the
# range rather than in the middle of it. Measured on a generated page, see tests.
MIN_IMAGE_SIDE = 400  # shortest side in pixels; smaller is too low-resolution to read

# --- Fixed text ---
# Shown on every result. Wording is fixed by the project plan.
SAFETY_BANNER = "This is a reading aid, not medical advice. Confirm with your pharmacist."

# --- Storage ---
# This file lives in app/, so the project root is one level up. Everything the
# app opens by path hangs off it.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Local key file ---
# A .env file in the project root (see .env.example) can hold NVIDIA_API_KEY so
# nobody has to export it in every shell. Real environment variables win over
# the file, so CI and production can still inject the key. A missing .env is
# not an error; the key check happens later, where it can produce a readable
# 503 instead of a crash at import time.
from dotenv import load_dotenv  # noqa: E402  (must run after PROJECT_ROOT)

load_dotenv(PROJECT_ROOT / ".env", override=False)

DATA_DIR = PROJECT_ROOT / "data"
MEDICINES_DB_PATH = DATA_DIR / "medicines.db"
CORRECTIONS_DB_PATH = DATA_DIR / "corrections.db"

# --- Serverless (Vercel) adjustments ---
# On Vercel the filesystem is read-only except /tmp, so the corrections
# database (the only file the app writes) moves to /tmp there. The medicines
# database is read-only and ships inside the bundle. The model timeout is
# clamped under the 60-second function limit (Hobby plan maximum).
import os  # noqa: E402

if os.environ.get("VERCEL"):
    CORRECTIONS_DB_PATH = Path("/tmp/corrections.db")
    if MODEL_TIMEOUT_SECONDS > 55:
        MODEL_TIMEOUT_SECONDS = 55