"""Status rule tests. Synthetic rows only."""

from app.match import MatchKind, MatchResult
from app.schema import MedicineItem, STATUS_CHECK, STATUS_OK, STATUS_UNCLEAR
from app.status import decide_status
from app.timing import decode


def _match(kind=MatchKind.ACCEPT, brand="Dolo 650", close=None, reason="matched"):
    best = None
    if kind is not MatchKind.NOT_FOUND:
        from app.match import Candidate

        best = Candidate(
            brand_name=brand,
            generic_name="Paracetamol",
            strength="650 mg",
            matched_field="brand_name",
            score=100.0,
        )
    return MatchResult(
        query=brand,
        kind=kind,
        best=best,
        close=close or [],
        reason=reason,
    )


def _item(name="Dolo 650", unclear=False):
    return MedicineItem(name=name, strength="650", timing_code="1-0-1", unclear=unclear)


def test_a_row_passes_only_when_every_check_passes():
    result = decide_status(_match(), decode("1-0-1"), _item())
    assert result.status == STATUS_OK
    assert result.is_ok is True
    assert result.reasons == ["every check passed."]


def test_the_model_flagging_unclear_makes_the_row_unclear():
    result = decide_status(_match(), decode("1-0-1"), _item(unclear=True))
    assert result.status == STATUS_UNCLEAR
    assert "not confident" in result.reason


def test_an_unread_name_is_unclear():
    result = decide_status(_match(), decode("1-0-1"), _item(name=None, unclear=True))
    assert result.status == STATUS_UNCLEAR
    assert "could not be read" in result.reason


def test_a_missing_unclear_flag_counts_as_unclear_because_it_was_never_confirmed():
    item = MedicineItem(name="Dolo 650")  # no unclear key at all
    result = decide_status(_match(), decode("1-0-1"), item)
    assert result.status == STATUS_UNCLEAR


def test_a_review_match_is_flagged_and_suggests_a_name():
    result = decide_status(_match(kind=MatchKind.REVIEW, reason="scored 87"), decode("1-0-1"), _item())
    assert result.status == STATUS_CHECK
    assert "did you mean Dolo 650?" in result.reason


def test_a_name_not_found_makes_the_row_unclear():
    result = decide_status(_match(kind=MatchKind.NOT_FOUND, reason="nothing close"), decode("1-0-1"), _item())
    assert result.status == STATUS_UNCLEAR
    assert "nothing close" in result.reason


def test_an_unknown_timing_code_is_flagged_and_shown_as_written():
    result = decide_status(_match(), decode("1-2-3"), _item())
    assert result.status == STATUS_UNCLEAR
    assert "'1-2-3'" in result.reason


def test_a_missing_timing_code_is_flagged():
    result = decide_status(_match(), decode(None), _item())
    assert result.status == STATUS_UNCLEAR
    assert "no timing was written" in result.reason


def test_an_ambiguous_name_makes_the_row_unclear():
    from app.match import Candidate

    other = Candidate(
        brand_name="Azithral 250",
        generic_name="Azithromycin",
        strength="250 mg",
        matched_field="brand_name",
        score=95.0,
    )
    result = decide_status(_match(close=[other]), decode("1-0-1"), _item())
    assert result.status == STATUS_UNCLEAR
    assert "Azithral 250" in result.reason


def test_all_three_status_words_are_reachable():
    seen = {
        decide_status(_match(), decode("1-0-1"), _item()).status,
        decide_status(_match(kind=MatchKind.REVIEW), decode("1-0-1"), _item()).status,
        decide_status(_match(), decode("ZZZ"), _item()).status,
    }
    assert seen == {STATUS_OK, STATUS_CHECK, STATUS_UNCLEAR}


def test_every_flagged_row_carries_a_reason():
    for match_result, timing, item in (
        (_match(), decode("1-2-3"), _item()),
        (_match(kind=MatchKind.REVIEW), decode("BD"), _item()),
        (_match(), decode("BD"), _item(unclear=True)),
        (_match(kind=MatchKind.NOT_FOUND), decode(None), _item(name=None)),
    ):
        result = decide_status(match_result, timing, item)
        assert result.status != STATUS_OK
        assert result.reasons and result.reason.strip()


def test_a_flagged_row_that_is_correct_is_still_flagged():
    """A right name that failed a check must not report OK: flags are not optional."""
    result = decide_status(_match(), decode("BD"), _item(unclear=True))
    assert result.status != STATUS_OK