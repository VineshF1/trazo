"""Send one prescription image to GLM 5.3 Flash and get the extraction JSON back.

Failure is reported as an error object with a readable message. Nothing is
invented and no fallback model is used.
"""

import base64
import io
import os

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
)

from app.config import (
    API_BASE_URL,
    API_KEY_ENV_VAR,
    MODEL_ID,
    MODEL_MAX_TOKENS,
    MODEL_TEMPERATURE,
    MODEL_TIMEOUT_SECONDS,
)
from app.image_utils import prepare_image
from app.parse_utils import parse_payload
from app.schema import ExtractionResult

RETRY_NOTE = "first reply was not valid JSON, retried once"


def load_prompt(path) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def get_api_key() -> str:
    """Read the key from the environment. It is never logged and never returned."""
    key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not key:
        raise RuntimeError(
            f"{API_KEY_ENV_VAR} is not set. Set it in the environment and run again. "
            "The key is used server side only and never appears in the page."
        )
    return key


def build_client(api_key: str | None = None) -> OpenAI:
    return OpenAI(
        api_key=api_key or get_api_key(),
        base_url=API_BASE_URL,
        timeout=MODEL_TIMEOUT_SECONDS,
    )


def build_messages(prompt: str, jpeg_bytes: bytes) -> list[dict]:
    """OpenAI-style image request from section 8 of the build prompt."""
    encoded = base64.b64encode(jpeg_bytes).decode("ascii")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                },
            ],
        }
    ]


def call_model(client: OpenAI, prompt: str, jpeg_bytes: bytes) -> tuple[str, str | None]:
    """One model call. Returns (raw_text, error)."""
    messages = build_messages(prompt, jpeg_bytes)
    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            temperature=MODEL_TEMPERATURE,
            max_tokens=MODEL_MAX_TOKENS,
        )
    except AuthenticationError:
        return "", f"Authentication failed (401). Check {API_KEY_ENV_VAR}."
    except APITimeoutError:
        return "", f"The model did not answer within {MODEL_TIMEOUT_SECONDS} seconds."
    except APIConnectionError as exc:
        return "", f"Could not reach {API_BASE_URL}: {type(exc).__name__}."
    except APIStatusError as exc:
        if exc.status_code in (401, 403):
            return "", (
                f"The API refused the key (HTTP {exc.status_code}). "
                f"Check {API_KEY_ENV_VAR}."
            )
        return "", f"The API returned HTTP {exc.status_code}."
    except Exception as exc:  # unknown client-side failure: report, do not guess
        return "", f"{type(exc).__name__}: {exc}"

    text, error = extract_text(response)
    if error:
        return "", error
    return text, None


def extract_text(response) -> tuple[str, str | None]:
    """Pull the reply text out of a chat completion. Handles both content shapes."""
    choices = getattr(response, "choices", None)
    if not choices:
        return "", "the API returned no choices"
    message = getattr(choices[0], "message", None)
    if message is None:
        return "", "the API returned a choice with no message"
    content = getattr(message, "content", None)
    if isinstance(content, str):
        if not content.strip():
            return "", "empty response"
        return content, None
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
            elif isinstance(part, str):
                chunks.append(part)
        joined = "".join(chunks)
        if not joined.strip():
            return "", "empty response"
        return joined, None
    return "", "the reply contained no text"


def run_extraction(
    image_bytes: bytes,
    prompt: str,
    client: OpenAI | None = None,
) -> tuple[ExtractionResult | None, str, str | None]:
    """Full Phase 1 path: prepare the image, call the model, parse, validate.

    Returns (result, raw_text, error). Exactly one of result and error is set. The
    raw text is returned even when parsing fails, so it can be inspected.
    """
    try:
        jpeg = prepare_image(image_bytes)
    except Exception as exc:  # unreadable upload is a client error, not a model error
        return None, "", f"could not read the image: {type(exc).__name__}"

    active_client = client or build_client()
    raw_text, error = call_model(active_client, prompt, jpeg)
    if error:
        return None, raw_text, error

    payload, error = parse_payload(raw_text)
    if error:
        retry_text, retry_error = call_model(active_client, prompt, jpeg)
        if retry_error:
            return None, retry_text or raw_text, retry_error
        payload, error = parse_payload(retry_text)
        raw_text = retry_text
        if error:
            return None, raw_text, f"{error}; {RETRY_NOTE}"

    try:
        return ExtractionResult.model_validate(payload), raw_text, None
    except Exception as exc:
        return None, raw_text, f"the reply did not match the schema: {type(exc).__name__}"


def result_to_dict(result: ExtractionResult) -> dict:
    """Plain JSON-ready form, for the API response and the eval results files."""
    return result.model_dump(mode="json")


def write_raw_output(path, image_path, raw_text: str, seconds: float) -> None:
    """Optional raw-output file for the evaluation harness. Text only, no image."""
    import json
    from datetime import datetime, timezone

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "image_file": os.path.basename(str(image_path)),
        "model": MODEL_ID,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seconds": round(seconds, 2),
        "raw_text": raw_text,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")