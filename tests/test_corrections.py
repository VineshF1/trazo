"""Correction table tests. A temporary database only; no photos, no user data."""

import pytest

from app.corrections import (
    find_suggestion,
    is_verified,
    normalize_raw,
    read_all_rows,
    save_correction,
)

MEDS = [
    {"brand_name": "Dolo 650", "generic_name": "Paracetamol", "strength": "650 mg", "use": "fever"},
    {"brand_name": "Monocef", "generic_name": "Ceftriaxone", "strength": "1 g", "use": "infection"},
]


def test_a_verified_correction_is_stored_and_marked_verified(tmp_path):
    db = tmp_path / "c.db"
    correction = save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    assert correction.verified is True
    assert correction.times_confirmed == 1
    assert correction.raw_text == "Dolo 65O"
    assert correction.corrected_name == "Dolo 650"


def test_a_correction_not_in_the_medicine_list_is_stored_but_not_verified(tmp_path):
    db = tmp_path / "c.db"
    correction = save_correction("Xyzzy", "Not A Medicine", db, MEDS)
    assert correction.verified is False


def test_the_same_correction_twice_confirms_rather_than_duplicates(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    second = save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    assert second.times_confirmed == 2
    assert len(read_all_rows(db)) == 1


def test_two_different_corrections_of_the_same_reading_are_kept_separately(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo S50", "Dolo 650", db, MEDS)
    save_correction("Dolo S50", "Dolo 500", db, MEDS)
    assert len(read_all_rows(db)) == 2


def test_a_verified_correction_is_offered_as_a_suggestion(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    assert find_suggestion("Dolo 65O", db, MEDS) == "Dolo 650"


def test_an_unverified_correction_is_never_suggested(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Xyzzy", "Not A Medicine", db, MEDS)
    assert find_suggestion("Xyzzy", db, MEDS) is None


def test_no_suggestion_when_nothing_matches(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    assert find_suggestion("Monocef", db, MEDS) is None


def test_the_suggestion_match_ignores_case_and_extra_spaces(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo  65O", "Dolo 650", db, MEDS)
    assert find_suggestion("  dolo 65o ", db, MEDS) == "Dolo 650"


def test_no_suggestion_without_a_reading(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    assert find_suggestion("", db, MEDS) is None
    assert find_suggestion(None, db, MEDS) is None


def test_an_empty_reading_is_refused(tmp_path):
    with pytest.raises(ValueError):
        save_correction("   ", "Dolo 650", tmp_path / "c.db", MEDS)


def test_an_empty_correction_is_refused(tmp_path):
    with pytest.raises(ValueError):
        save_correction("Dolo 65O", "  ", tmp_path / "c.db", MEDS)


def test_is_verified_matches_brand_and_generic(tmp_path):
    assert is_verified("Dolo 650", MEDS) is True
    assert is_verified("Paracetamol", MEDS) is True
    assert is_verified("Nope", MEDS) is False
    assert is_verified("", MEDS) is False


def test_normalize_raw_collapses_whitespace_and_case():
    assert normalize_raw("  Dolo   65O ") == "dolo 65o"


def test_a_new_correction_does_not_touch_an_existing_one(tmp_path):
    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    save_correction("Monocef", "Monocef", db, MEDS)
    assert len(read_all_rows(db)) == 2


def test_reading_a_missing_database_returns_nothing_rather_than_raising(tmp_path):
    assert read_all_rows(tmp_path / "nothing.db") == []


def test_only_text_columns_are_stored(tmp_path):
    """The schema must not grow a photo or a user column without a decision."""
    import sqlite3

    db = tmp_path / "c.db"
    save_correction("Dolo 65O", "Dolo 650", db, MEDS)
    connection = sqlite3.connect(db)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(corrections)")}
    connection.close()
    assert columns == {"id", "raw_text", "corrected_name", "times_confirmed", "verified", "created_at"}