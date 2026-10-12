"""Matching tests. Synthetic medicine lists and strings only.

Expected scores were read off real RapidFuzz output, then written down here. They
are properties of the matcher, not accuracy results of the app.
"""

from app import match
from app.match import MatchKind, match_name

MEDS = [
    {"brand_name": "Dolo 650", "generic_name": "Paracetamol", "strength": "650 mg", "use": "fever"},
    {"brand_name": "Amoxycillin 500", "generic_name": "Amoxicillin", "strength": "500 mg", "use": "infection"},
    {"brand_name": "Azithral 500", "generic_name": "Azithromycin", "strength": "500 mg", "use": "infection"},
    {"brand_name": "Azithral 250", "generic_name": "Azithromycin", "strength": "250 mg", "use": "infection"},
    {"brand_name": "Pantocid 40", "generic_name": "Pantoprazole", "strength": "40 mg", "use": "acidity"},
    {"brand_name": "Monocef", "generic_name": "Ceftriaxone", "strength": "1 g", "use": "infection"},
]


def test_an_exact_brand_name_is_accepted_with_no_ambiguity():
    result = match_name("Dolo 650", MEDS)
    assert result.kind is MatchKind.ACCEPT
    assert result.best.brand_name == "Dolo 650"
    assert result.best.score == 100.0
    assert result.close == []
    assert result.is_ok is True


def test_a_read_name_is_matched_against_the_generic_name_too():
    result = match_name("Amoxicillin", MEDS)
    assert result.kind is MatchKind.ACCEPT
    assert result.best.brand_name == "Amoxycillin 500"
    assert result.best.matched_field == "generic_name"


def test_a_misspelling_inside_the_review_band_is_suggested_not_accepted():
    result = match_name("Dolo 65O", MEDS)
    assert result.kind is MatchKind.REVIEW
    assert result.best.brand_name == "Dolo 650"
    assert 70 <= result.best.score < 90
    assert "below the accept threshold" in result.reason
    assert result.is_ok is False


def test_a_misspelling_of_a_generic_name_is_corrected_and_accepted():
    """Paracetmol vs Paracetamol scores 95.2: inside the accept band, so it is fixed."""
    result = match_name("Paracetmol", MEDS)
    assert result.kind is MatchKind.ACCEPT
    assert result.best.generic_name == "Paracetamol"
    assert result.best.matched_field == "generic_name"
    assert result.suggestion == "Dolo 650"


def test_a_worse_misspelling_lands_in_the_review_band():
    result = match_name("Dolo 65O", MEDS)
    assert result.kind is MatchKind.REVIEW


def test_a_name_below_the_review_threshold_is_not_found():
    result = match_name("Zzzz", MEDS)
    assert result.kind is MatchKind.NOT_FOUND
    assert result.best is not None
    assert result.best.score < 70
    assert "below the review threshold" in result.reason


def test_a_name_between_the_thresholds_is_review_not_not_found():
    result = match_name("Azithral", MEDS)
    assert result.kind is MatchKind.REVIEW
    assert result.best.brand_name == "Azithral 500"


def test_a_missing_name_is_not_found_with_a_reason():
    result = match_name(None, MEDS)
    assert result.kind is MatchKind.NOT_FOUND
    assert result.best is None
    assert result.reason == "no medicine name to match"


def test_an_empty_medicine_list_reports_the_list_as_the_reason():
    result = match_name("Dolo 650", [])
    assert result.kind is MatchKind.NOT_FOUND
    assert "not loaded" in result.reason


def test_matching_uses_the_database_when_no_list_is_passed(monkeypatch):
    monkeypatch.setattr(match, "read_all", lambda: MEDS)
    result = match_name("Monocef")
    assert result.kind is MatchKind.ACCEPT
    assert result.best.brand_name == "Monocef"


def test_a_second_near_match_outside_the_margin_is_not_ambiguous():
    """Two strengths of one drug are 100 and 91.7: 8.3 points apart, margin is 5."""
    result = match_name("Azithral 500", MEDS)
    assert result.kind is MatchKind.ACCEPT
    assert result.close == []
    assert result.is_ok is True


def test_a_second_near_match_inside_the_margin_is_ambiguous(monkeypatch):
    monkeypatch.setattr(match, "MATCH_CLOSE_MARGIN", 10)
    result = match_name("Azithral 500", MEDS)
    assert result.kind is MatchKind.ACCEPT
    assert [candidate.brand_name for candidate in result.close] == ["Azithral 250"]
    assert result.is_ok is False


def test_a_zero_margin_flags_only_an_exact_tie(monkeypatch):
    monkeypatch.setattr(match, "MATCH_CLOSE_MARGIN", 0)
    assert match_name("Azithral 500", MEDS).close == []


def test_the_accept_threshold_can_be_raised(monkeypatch):
    result = match_name("Dolo 65O", MEDS, threshold=95)
    assert result.kind is MatchKind.REVIEW


def test_normalize_folds_case_and_whitespace():
    assert match.normalize("  Dolo   650 ") == "dolo 650"


def test_case_and_whitespace_do_not_change_the_result():
    assert match_name("dolo 650", MEDS).kind is MatchKind.ACCEPT
    assert match_name("  DOLO   650  ", MEDS).kind is MatchKind.ACCEPT


def test_a_medicine_with_no_generic_name_is_still_matchable():
    medicines = [{"brand_name": "Shelcal 500", "generic_name": None, "strength": None, "use": None}]
    result = match_name("Shelcal 500", medicines)
    assert result.kind is MatchKind.ACCEPT
    assert result.best.matched_field == "brand_name"