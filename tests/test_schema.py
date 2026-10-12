"""Schema and normalization tests. Synthetic values only."""

import pytest
from pydantic import ValidationError

from app.extract import result_to_dict
from app.schema import ExtractionResult


def test_setting_field_to_null_is_allowed():
    result = ExtractionResult.model_validate(
        {"medicines": [{"name": None, "strength": None, "timing_code": None, "duration": None}]}
    )
    item = result.medicines[0]
    assert item.name is None
    assert item.strength is None
    assert item.timing_code is None
    assert item.duration is None


def test_missing_fields_stay_null_rather_than_being_filled_in():
    result = ExtractionResult.model_validate({"medicines": [{"name": "Dolo"}]})
    item = result.medicines[0]
    assert item.name == "Dolo"
    assert item.strength is None
    assert item.timing_code is None
    assert item.duration is None
    assert item.confidence == 0.0


def test_confidence_is_clamped_to_the_unit_interval():
    assert ExtractionResult.model_validate(
        {"medicines": [{"confidence": 1.5}]}
    ).medicines[0].confidence == 1.0
    assert ExtractionResult.model_validate(
        {"medicines": [{"confidence": -0.3}]}
    ).medicines[0].confidence == 0.0
    assert ExtractionResult.model_validate(
        {"medicines": [{"confidence": "0.62"}]}
    ).medicines[0].confidence == pytest.approx(0.62)


def test_unparseable_confidence_becomes_zero_not_a_guess():
    for value in ("high", None, "", {"a": 1}):
        result = ExtractionResult.model_validate({"medicines": [{"confidence": value}]})
        assert result.medicines[0].confidence == 0.0


def test_unclear_missing_counts_as_unreadable():
    item = ExtractionResult.model_validate({"medicines": [{"name": "Dolo"}]}).medicines[0]
    assert item.unclear is None
    assert item.is_flagged_unclear is True


def test_unclear_false_is_kept_only_when_stated():
    item = ExtractionResult.model_validate(
        {"medicines": [{"name": "Dolo", "unclear": False}]}
    ).medicines[0]
    assert item.is_flagged_unclear is False


def test_unclear_true_is_flagged():
    item = ExtractionResult.model_validate(
        {"medicines": [{"name": None, "unclear": True}]}
    ).medicines[0]
    assert item.is_flagged_unclear is True


def test_unclear_accepts_string_and_number_forms():
    for value in ("true", "True", "yes", "1", 1):
        item = ExtractionResult.model_validate({"medicines": [{"unclear": value}]}).medicines[0]
        assert item.unclear is True


def test_an_empty_medicine_object_carries_no_invented_name():
    item = ExtractionResult.model_validate({"medicines": [{}]}).medicines[0]
    assert item.name is None
    assert item.is_flagged_unclear is True


def test_a_number_where_text_was_written_keeps_the_written_value():
    item = ExtractionResult.model_validate({"medicines": [{"strength": 650}]}).medicines[0]
    assert item.strength == "650"


def test_whitespace_only_text_is_treated_as_missing():
    item = ExtractionResult.model_validate({"medicines": [{"name": "   "}]}).medicines[0]
    assert item.name is None


def test_text_is_stripped():
    item = ExtractionResult.model_validate({"medicines": [{"name": "  Dolo 650  "}]}).medicines[0]
    assert item.name == "Dolo 650"


def test_missing_medicines_key_yields_an_empty_list():
    assert ExtractionResult.model_validate({}).medicines == []


def test_missing_notes_becomes_an_empty_string():
    assert ExtractionResult.model_validate({"medicines": []}).notes == ""
    assert ExtractionResult.model_validate({"medicines": [], "notes": None}).notes == ""


def test_unknown_keys_are_ignored_not_rejected():
    result = ExtractionResult.model_validate(
        {"medicines": [{"name": "Dolo", "colour": "white"}], "page": 1}
    )
    assert result.medicines[0].name == "Dolo"
    assert not hasattr(result.medicines[0], "colour")


def test_medicines_of_the_wrong_type_is_a_schema_error():
    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"medicines": 5})


def test_result_to_dict_is_json_ready():
    result = ExtractionResult.model_validate({"medicines": [{"name": "Dolo 650"}]})
    payload = result_to_dict(result)
    assert payload["medicines"][0]["name"] == "Dolo 650"
    assert payload["medicines"][0]["unclear"] is None
    assert payload["notes"] == ""