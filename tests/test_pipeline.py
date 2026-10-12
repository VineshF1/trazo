"""Pipeline tests: build_rows joins the Phase 2 pieces. Synthetic data only."""

from app import pipeline
from app.pipeline import build_rows, process
from app.schema import STATUS_CHECK, STATUS_OK, STATUS_UNCLEAR, ExtractionResult

MEDS = [
    {"brand_name": "Dolo 650", "generic_name": "Paracetamol", "strength": "650 mg", "use": "fever"},
    {"brand_name": "Monocef", "generic_name": "Ceftriaxone", "strength": "1 g", "use": "infection"},
]


def _result(medicines, notes=""):
    return ExtractionResult.model_validate({"medicines": medicines, "notes": notes})


def test_a_clean_row_is_ok():
    result = _result([{"name": "Dolo 650", "strength": "650", "timing_code": "1-0-1", "duration": "5 days", "unclear": False}])
    rows = build_rows(result, MEDS, use_corrections=False)
    assert len(rows) == 1
    assert rows[0]["status"] == STATUS_OK
    assert rows[0]["timing_text"] == "Morning and night"
    assert rows[0]["timing_known"] is True
    assert rows[0]["candidates"][0]["brand_name"] == "Dolo 650"


def test_an_unreadable_row_keeps_a_null_name_and_is_unclear():
    result = _result([{"name": None, "unclear": True, "timing_code": None}])
    rows = build_rows(result, MEDS, use_corrections=False)
    assert rows[0]["name"] is None
    assert rows[0]["status"] == STATUS_UNCLEAR
    assert rows[0]["unclear"] is True
    assert rows[0]["reason"]


def test_a_review_match_is_check_this_with_a_suggestion():
    result = _result([{"name": "Dolo 65O", "timing_code": "1-0-1", "unclear": False}])
    rows = build_rows(result, MEDS, use_corrections=False)
    assert rows[0]["status"] == STATUS_CHECK
    assert "did you mean" in rows[0]["reason"].lower()


def test_an_unknown_timing_code_shows_the_raw_code():
    result = _result([{"name": "Dolo 650", "timing_code": "1-2-3", "unclear": False}])
    rows = build_rows(result, MEDS, use_corrections=False)
    assert rows[0]["timing_text"] == "1-2-3"
    assert rows[0]["timing_known"] is False
    assert rows[0]["status"] == STATUS_UNCLEAR


def test_an_empty_medicine_list_flags_every_row_but_does_not_invent_a_name():
    result = _result([{"name": "Dolo 650", "timing_code": "1-0-1", "unclear": False}])
    rows = build_rows(result, [], use_corrections=False)
    assert rows[0]["name"] == "Dolo 650"  # the reading is kept
    assert rows[0]["candidates"] == []
    assert rows[0]["status"] == STATUS_UNCLEAR


def test_no_rows_when_the_page_has_no_medicines():
    assert build_rows(_result([]), MEDS, use_corrections=False) == []


def test_every_row_carries_a_status_and_a_reason():
    result = _result(
        [
            {"name": "Dolo 650", "timing_code": "1-0-1", "unclear": False},
            {"name": None, "timing_code": None, "unclear": True},
            {"name": "Zzzz", "timing_code": "BD", "unclear": False},
        ]
    )
    for row in build_rows(result, MEDS, use_corrections=False):
        assert row["status"] in (STATUS_OK, STATUS_CHECK, STATUS_UNCLEAR)
        assert row["reason"]


def test_a_saved_correction_is_shown_but_the_row_does_not_stay_ok(tmp_path):
    from app.corrections import save_correction

    db = tmp_path / "c.db"
    save_correction("Dolo 650", "Dolo 650", db, MEDS)  # verified: the name is in the list
    result = _result([{"name": "Dolo 650", "timing_code": "1-0-1", "unclear": False}])
    rows = build_rows(result, MEDS, corrections_db=db)
    assert rows[0]["suggestion"] == "Dolo 650"
    assert rows[0]["status"] == STATUS_CHECK
    assert "saved correction suggests" in rows[0]["reason"]


def test_no_suggestion_when_corrections_are_switched_off(tmp_path):
    from app.corrections import save_correction

    db = tmp_path / "c.db"
    save_correction("Dolo 650", "Dolo 650", db, MEDS)
    result = _result([{"name": "Dolo 650", "timing_code": "1-0-1", "unclear": False}])
    rows = build_rows(result, MEDS, corrections_db=db, use_corrections=False)
    assert rows[0]["suggestion"] is None
    assert rows[0]["status"] == STATUS_OK


def test_an_unverified_correction_is_not_suggested(tmp_path):
    from app.corrections import save_correction

    db = tmp_path / "c.db"
    save_correction("Dolo 650", "Not A Medicine", db, MEDS)
    result = _result([{"name": "Dolo 650", "timing_code": "1-0-1", "unclear": False}])
    rows = build_rows(result, MEDS, corrections_db=db)
    assert rows[0]["suggestion"] is None
    assert rows[0]["status"] == STATUS_OK


def test_a_suggestion_never_turns_a_flagged_row_into_ok(tmp_path):
    from app.corrections import save_correction

    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    result = _result([{"name": "Dolo 65O", "timing_code": "1-0-1", "unclear": False}])
    rows = build_rows(result, MEDS, corrections_db=db)
    assert rows[0]["status"] == STATUS_CHECK  # already flagged by the review match
    assert rows[0]["status"] != STATUS_OK


def test_process_returns_rows_notes_and_the_safety_banner(monkeypatch):
    from app.config import SAFETY_BANNER

    monkeypatch.setattr(
        pipeline,
        "run_extraction",
        lambda image_bytes, prompt, client=None: (
            _result([{"name": "Dolo 650", "timing_code": "1-0-1", "unclear": False}]),
            "raw",
            None,
        ),
    )
    payload, raw, error = pipeline.process(b"image", "prompt", MEDS, use_corrections=False)
    assert error is None
    assert raw == "raw"
    assert payload["banner"] == SAFETY_BANNER
    assert payload["medicines"][0]["status"] == STATUS_OK


def test_process_passes_the_error_through_without_rows(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "run_extraction",
        lambda image_bytes, prompt, client=None: (None, "", "the API returned HTTP 503."),
    )
    payload, raw, error = pipeline.process(b"image", "prompt", MEDS)
    assert payload is None
    assert error == "the API returned HTTP 503."
