"""Trazo API.

POST /read reads a prescription photo and returns the rows, the status word for
each one, and the safety banner. The page itself is Phase 5.

Nothing is written to disk, and no medicine name is logged with any identity. The
only log line is the route, the method and the status.
"""

import io
import logging

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from app.clean import check_quality
from app.corrections import save_correction
from app.config import (
    APP_NAME,
    APP_VERSION,
    MAX_UPLOAD_BYTES,
    PROJECT_ROOT,
    SAFETY_BANNER,
)
from app.extract import build_client, get_api_key, load_prompt
from app.medicines import read_all
from app.pipeline import process

logger = logging.getLogger("trazo")

EXTRACT_PROMPT_PATH = PROJECT_ROOT / "prompts" / "extract_prompt.txt"
STATIC_DIR = PROJECT_ROOT / "static"
CORRECTIONS_DB = None  # set to a path to enable learned suggestions

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.middleware("http")
async def log_request(request: Request, call_next):
    """Log the route and its status. Never the body, never a medicine name."""
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/health")
def health() -> dict:
    """Liveness check. Returns no user or medicine data."""
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.post("/read")
async def read(image: UploadFile = File(...)):
    """Read one prescription photo and return the rows.

    Errors are reported with a status code and a plain sentence. No error path
    returns rows, so a failure can never look like a reading.
    """
    payload = await image.read()

    if not payload:
        return JSONResponse(status_code=400, content=_error("no photo was received"))
    if len(payload) > MAX_UPLOAD_BYTES:
        return JSONResponse(
            status_code=413,
            content=_error(f"that photo is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB"),
        )
    if not _is_image(payload):
        return JSONResponse(status_code=400, content=_error("that file is not an image"))

    quality = check_quality(payload)
    if not quality.ok:
        # A photo that cannot be read is not sent to the model.
        return JSONResponse(
            status_code=422,
            content={
                "error": quality.retake_message,
                "retake": True,
                "medicines": [],
                "banner": SAFETY_BANNER,
            },
        )

    try:
        api_key = get_api_key()
        prompt = load_prompt(EXTRACT_PROMPT_PATH)
    except (RuntimeError, OSError):
        return JSONResponse(status_code=503, content=_error("the reading service is not configured"))

    try:
        result, _raw, error = process(
            payload,
            prompt,
            medicines=read_all(),
            client=build_client(api_key),
            corrections_db=CORRECTIONS_DB,
        )
    except Exception as exc:
        # The exception type only: a validation error's message can quote the
        # reading, and medicine names must not reach the log.
        logger.error("model call failed: %s", type(exc).__name__)
        return JSONResponse(
            status_code=502,
            content=_error("the reading service could not be reached"),
        )

    if error:
        status_code = 504 if "did not answer within" in error else 502
        return JSONResponse(status_code=status_code, content=_error(error))

    return JSONResponse(status_code=200, content=result)


def _is_image(payload: bytes) -> bool:
    """Whether the upload is an image Pillow can open. The file name is not trusted."""
    try:
        with Image.open(io.BytesIO(payload)) as opened:
            opened.verify()
    except Exception:
        return False
    return True


def _error(message: str) -> dict:
    """One error shape for every failure. No rows, so nothing can look like a reading."""
    return {"error": message, "medicines": [], "banner": SAFETY_BANNER}


class CorrectionRequest(BaseModel):
    """A user's fix for one reading. Text only: no photo, no user id."""

    raw_text: str
    corrected_name: str


@app.post("/correct")
def correct(request: CorrectionRequest):
    """Save one correction so it can be suggested later, always flagged.

    A correction is verified only if the corrected name is in the medicine list.
    Nothing here replaces a reading: suggestions are shown with "Check this".
    """
    try:
        correction = save_correction(
            request.raw_text,
            request.corrected_name,
            CORRECTIONS_DB,
            medicines=read_all(),
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content=_error(str(exc)))

    return {
        "saved": True,
        "verified": correction.verified,
        "times_confirmed": correction.times_confirmed,
        "banner": SAFETY_BANNER,
    }


STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
