"""Timing decoder tests. Synthetic strings only."""

from app.timing import TIMING, decode


def test_every_dictionary_code_decodes_to_its_meaning():
    for code, meaning in TIMING.items():
        result = decode(code)
        assert result.known is True
        assert result.meaning == meaning
        assert result.display == meaning


def test_lowercase_is_the_same_code():
    result = decode("bd")
    assert result.known is True
    assert result.meaning == "Twice a day"


def test_surrounding_whitespace_is_ignored():
    assert decode("  OD  ").known is True
    assert decode("  OD  ").meaning == "Once a day"


def test_a_hyphenated_code_keeps_its_hyphens():
    assert decode("1-0-1").meaning == "Morning and night"


def test_a_known_code_is_not_flagged():
    assert decode("SOS").known is True


def test_an_unknown_code_is_flagged_and_shown_as_written():
    result = decode("1-2-3")
    assert result.known is False
    assert result.meaning is None
    assert result.raw == "1-2-3"
    assert result.display == "1-2-3"


def test_an_unknown_code_is_never_guessed():
    result = decode("QWERTY")
    assert result.meaning is None
    assert result.known is False


def test_none_is_flagged_with_nothing_shown():
    result = decode(None)
    assert result.known is False
    assert result.raw is None
    assert result.meaning is None
    assert result.display == ""


def test_blank_text_is_treated_as_missing():
    result = decode("   ")
    assert result.known is False
    assert result.raw is None
    assert result.display == ""


def test_a_number_is_reported_as_written():
    result = decode(101)
    assert result.known is False
    assert result.raw == "101"