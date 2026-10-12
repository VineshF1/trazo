"""API tests. A synthetic page image and a stubbed model call; no network, no real data."""

import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

import main
from app.config import SAFETY_BANNER

client = TestClient(main.app)


def _page(width=900, height=1200) -> bytes:
    """A sharp page-like image, so it passes the photo quality check."""
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    step = max(30, height // 40)
    line = max(3, height // 300)
    y = step
    while y < height - step:
        draw.line([(step, y), (width - step, y)], fill="black", width=line)
        draw.line([(step, y + line * 4), (width - step * 3, y + line * 4)], fill="black", width=max(2, line - 1))
        y += step
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def _upload(payload: bytes, name="rx.jpg", mime="image/jpeg"):
    return client.post("/read", files={"image": (name, payload, mime)})


def _stub_model(monkeypatch, payload, raw="raw", error=None):
    monkeypatch.setattr(main, "get_api_key", lambda: "key")
    monkeypatch.setattr(main, "load_prompt", lambda path: "prompt")
    monkeypatch.setattr(main, "build_client", lambda key: object())
    monkeypatch.setattr(main, "read_all", lambda: [])
    monkeypatch.setattr(main, "process", lambda *a, **k: (payload, raw, error))


OK_PAYLOAD = {
    "medicines": [
        {
            "name": "Dolo 650",
            "strength": "650",
            "duration": "5 days",
            "timing_code": "1-0-1",
            "timing_text": "Morning and night",
            "timing_known": True,
            "status": "OK",
            "reason": "every check passed.",
            "unclear": False,
            "candidates": [],
        }
    ],
    "notes": "",
    "banner": SAFETY_BANNER,
}


def test_health_is_unchanged():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_a_reading_returns_rows_and_the_banner(monkeypatch):
    _stub_model(monkeypatch, OK_PAYLOAD)
    response = _upload(_page())
    assert response.status_code == 200
    body = response.json()
    assert body["medicines"][0]["status"] == "OK"
    assert body["banner"] == SAFETY_BANNER


def test_a_file_that_is_not_an_image_is_rejected(monkeypatch):
    _stub_model(monkeypatch, OK_PAYLOAD)
    response = _upload(b"this is not an image", name="notes.jpg")
    assert response.status_code == 400
    assert response.json()["error"] == "that file is not an image"


def test_an_empty_upload_is_rejected(monkeypatch):
    _stub_model(monkeypatch, OK_PAYLOAD)
    response = _upload(b"")
    assert response.status_code == 400
    assert "no photo" in response.json()["error"]


def test_a_photo_over_the_size_limit_is_rejected(monkeypatch):
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 1024)
    response = _upload(_page(3000, 3000))
    assert response.status_code == 413
    assert "larger than" in response.json()["error"]


def test_a_missing_key_reports_the_service_as_not_configured(monkeypatch):
    def _no_key():
        raise RuntimeError("NVIDIA_API_KEY is not set.")

    monkeypatch.setattr(main, "get_api_key", _no_key)
    response = _upload(_page(700, 900))
    assert response.status_code == 503
    assert response.json()["error"] == "the reading service is not configured"


def test_a_missing_prompt_reports_the_service_as_not_configured(monkeypatch):
    monkeypatch.setattr(main, "get_api_key", lambda: "key")
    monkeypatch.setattr(main, "load_prompt", lambda path: (_ for _ in ()).throw(OSError("gone")))
    response = _upload(_page(700, 900))
    assert response.status_code == 503


def test_a_model_failure_is_reported_without_rows(monkeypatch):
    _stub_model(monkeypatch, None, raw="", error="the API returned HTTP 503.")
    response = _upload(_page(700, 900))
    assert response.status_code == 502
    body = response.json()
    assert body["medicines"] == []
    assert body["error"] == "the API returned HTTP 503."


def test_a_timeout_is_reported_as_a_gateway_timeout(monkeypatch):
    _stub_model(monkeypatch, None, raw="", error="The model did not answer within 120 seconds.")
    response = _upload(_page(700, 900))
    assert response.status_code == 504


def test_an_unexpected_failure_is_caught_and_reported(monkeypatch):
    def _boom(*args, **kwargs):
        raise ValueError("something broke")

    monkeypatch.setattr(main, "get_api_key", lambda: "key")
    monkeypatch.setattr(main, "load_prompt", lambda path: "prompt")
    monkeypatch.setattr(main, "build_client", lambda key: object())
    monkeypatch.setattr(main, "read_all", lambda: [])
    monkeypatch.setattr(main, "process", _boom)
    response = _upload(_page(700, 900))
    assert response.status_code == 502
    assert response.json()["medicines"] == []


def test_every_error_response_carries_the_banner_and_no_rows(monkeypatch):
    monkeypatch.setattr(main, "get_api_key", lambda: "key")
    responses = [
        _upload(b""),
        _upload(b"not an image"),
    ]
    for response in responses:
        body = response.json()
        assert body["medicines"] == []
        assert body["banner"] == SAFETY_BANNER
        assert body["error"]


def test_the_upload_is_read_into_memory_and_no_photo_is_written(monkeypatch, tmp_path):
    _stub_model(monkeypatch, OK_PAYLOAD)
    before = {path.name for path in tmp_path.iterdir()}
    _upload(_page(700, 900))
    after = {path.name for path in tmp_path.iterdir()}
    assert before == after  # nothing was written for this request


def test_no_request_creates_a_database_in_the_repo_data_dir(monkeypatch, tmp_path):
    """Endpoints must not leave a database behind. Reading the list is not writing."""
    from app.config import DATA_DIR

    monkeypatch.setattr(main, "get_api_key", lambda: "key")
    monkeypatch.setattr(main, "load_prompt", lambda path: "prompt")
    monkeypatch.setattr(main, "build_client", lambda key: object())
    monkeypatch.setattr(main, "process", lambda *a, **k: (OK_PAYLOAD, "raw", None))
    monkeypatch.setattr(main, "CORRECTIONS_DB", tmp_path / "c.db")

    before = {p.name for p in DATA_DIR.iterdir()} if DATA_DIR.is_dir() else set()
    _upload(_page(700, 900))
    client.post("/correct", json={"raw_text": "Dolo 65O", "corrected_name": "   "})
    after = {p.name for p in DATA_DIR.iterdir()} if DATA_DIR.is_dir() else set()
    assert before == after


def test_a_correction_is_saved_and_verified_against_the_medicine_list(monkeypatch, tmp_path):
    db = tmp_path / "c.db"
    monkeypatch.setattr(main, "CORRECTIONS_DB", db)
    monkeypatch.setattr(main, "read_all", lambda: [{"brand_name": "Dolo 650", "generic_name": "Paracetamol"}])
    response = client.post("/correct", json={"raw_text": "Dolo 65O", "corrected_name": "Dolo 650"})
    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is True
    assert body["verified"] is True
    assert body["times_confirmed"] == 1
    assert body["banner"] == SAFETY_BANNER


def test_a_correction_of_an_unknown_name_is_saved_but_not_verified(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "CORRECTIONS_DB", tmp_path / "c.db")
    monkeypatch.setattr(main, "read_all", lambda: [])
    response = client.post("/correct", json={"raw_text": "Xyzzy", "corrected_name": "Nothing"})
    assert response.status_code == 200
    assert response.json()["verified"] is False


def test_an_empty_correction_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "CORRECTIONS_DB", tmp_path / "c.db")
    response = client.post("/correct", json={"raw_text": "Dolo 65O", "corrected_name": "   "})
    assert response.status_code == 400
    assert response.json()["medicines"] == []


def test_a_blank_page_is_rejected_with_a_retake_and_no_model_call(monkeypatch):
    """A blank photo measures as blurry, so it must not reach the model."""
    calls = []
    _stub_model(monkeypatch, OK_PAYLOAD)
    monkeypatch.setattr(main, "process", lambda *a, **k: calls.append(1) or (OK_PAYLOAD, "raw", None))

    blank = io.BytesIO()
    Image.new("RGB", (1200, 1600), "white").save(blank, format="JPEG")
    response = _upload(blank.getvalue())

    assert response.status_code == 422
    assert response.json()["retake"] is True
    assert response.json()["medicines"] == []
    assert calls == []


def test_a_model_failure_is_not_logged_with_medicine_names(monkeypatch, caplog):
    """A validation error's message can quote the reading, so only the type is logged."""
    def _leaky(*args, **kwargs):
        raise ValueError("Dolo 650 is not a valid name")

    monkeypatch.setattr(main, "get_api_key", lambda: "key")
    monkeypatch.setattr(main, "load_prompt", lambda path: "prompt")
    monkeypatch.setattr(main, "build_client", lambda key: object())
    monkeypatch.setattr(main, "read_all", lambda: [])
    monkeypatch.setattr(main, "process", _leaky)
    with caplog.at_level("INFO", logger="trazo"):
        _upload(_page(700, 900))
    assert "Dolo 650" not in caplog.text


def test_a_large_but_allowed_photo_is_accepted(monkeypatch):
    _stub_model(monkeypatch, OK_PAYLOAD)
    response = _upload(_page(2400, 3200))
    assert response.status_code == 200