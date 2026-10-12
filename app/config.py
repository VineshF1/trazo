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
# Model ID and base URL copied from the NVIDIA build model card for GLM-5.3-Flash
# (build.nvidia.com/z-ai/glm-5-3-flash, checked 2026-10-11). The model is natively
# multimodal and accepts png, jpg, jpeg and webp input.
MODEL_ID = "z-ai/glm-5.3-flash"
API_BASE_URL = "https://integrate.api.nvidia.com/v1"
API_KEY_ENV_VAR = "NVIDIA_API_KEY"
MODEL_TEMPERATURE = 0.0
# Cap on the reply length. Not in the plan; added because a vision call with no cap can
# spend minutes on reasoning. Starting guess.
MODEL_MAX_TOKENS = 1024
# The model card documents a thinking budget via `reasoning_effort` (low/high/max,
# default max) and says chat scenarios should pass `clear_thinking=true` explicitly.
# Neither is sent yet: Phase 1 tests the plain request format from the plan first.
MODEL_TIMEOUT_SECONDS = 120  # starting guess

# --- Image handling ---
MAX_IMAGE_SIDE = 1600  # starting guess: longest side after resize, pixels
JPEG_QUALITY = 0.8  # starting guess

# --- Medicine name matching ---
MATCH_ACCEPT = 90  # starting guess: score at or above this is an accepted match
MATCH_REVIEW = 70  # starting guess: between review and accept -> "Check this"
MATCH_CLOSE_MARGIN = 5  # starting guess: a second candidate this close is shown too
PAIRING_THRESHOLD = 60  # starting guess: eval pairing threshold

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