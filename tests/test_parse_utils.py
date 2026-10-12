"""Parser tests: synthetic model text only. No API calls, no real prescriptions."""

from app.parse_utils import parse_payload, strip_code_fences

SAMPLE = '{"medicines":[{"name":"Paracetamol"}],"notes":""}'


def test_plain_json():
    payload, error = parse_payload(SAMPLE)
    assert error is None
    assert payload["medicines"][0]["name"] == "Paracetamol"


def test_json_with_surrounding_whitespace():
    payload, error = parse_payload(f"\n\n  {SAMPLE}  \n")
    assert error is None
    assert payload["medicines"][0]["name"] == "Paracetamol"


def test_fenced_json_with_language_tag():
    payload, error = parse_payload(f"```json\n{SAMPLE}\n```")
    assert error is None
    assert payload["notes"] == ""


def test_fenced_json_without_language_tag():
    payload, error = parse_payload(f"```\n{SAMPLE}\n```")
    assert error is None
    assert "medicines" in payload


def test_extra_text_before_and_after_json():
    text = f"Here is the reading.\n\n{SAMPLE}\n\nLet me know if you need more."
    payload, error = parse_payload(text)
    assert error is None
    assert payload["medicines"][0]["name"] == "Paracetamol"


def test_prose_with_stray_braces_before_the_object():
    text = f'Use the {{{{brace}}}} style then: {SAMPLE}'
    payload, error = parse_payload(text)
    assert error is None
    assert payload["medicines"][0]["name"] == "Paracetamol"


def test_braces_inside_a_string_value_do_not_end_the_object():
    text = '{"medicines":[],"notes":"the line read {unreadable} marker"}'
    payload, error = parse_payload(text)
    assert error is None
    assert payload["notes"] == "the line read {unreadable} marker"


def test_escaped_quote_inside_a_string_value():
    text = '{"medicines":[],"notes":"one \\"partial\\" word"}'
    payload, error = parse_payload(text)
    assert error is None
    assert payload["notes"] == 'one "partial" word'


def test_broken_json_is_reported_not_guessed():
    payload, error = parse_payload('{"medicines":[{"name":"Dolo"')
    assert payload is None
    assert error is not None


def test_completely_broken_json_is_reported():
    payload, error = parse_payload("I could not read this prescription.")
    assert payload is None
    assert error is not None


def test_empty_string_is_reported():
    payload, error = parse_payload("   ")
    assert payload is None
    assert error == "empty response"


def test_none_is_reported():
    payload, error = parse_payload(None)
    assert payload is None
    assert error == "empty response"


def test_empty_json_object_is_valid_and_carries_no_medicines():
    payload, error = parse_payload("{}")
    assert error is None
    assert payload == {}


def test_json_array_is_rejected_as_not_an_object():
    payload, error = parse_payload('[{"name":"Dolo"}]')
    assert payload is None
    assert "not an object" in error


def test_truncated_object_after_a_complete_one_keeps_the_complete_one():
    text = SAMPLE + '{"medicines":[{"name":"Incomplete"'
    payload, error = parse_payload(text)
    assert error is None
    assert payload["medicines"][0]["name"] == "Paracetamol"