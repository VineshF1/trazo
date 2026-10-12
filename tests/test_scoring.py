"""Scoring and pairing tests. Synthetic rows only.

Expected RapidFuzz scores were read off real output before being written here.
"""

from scoring import (
    CORRECT,
    DANGEROUS,
    WRONG_FLAGGED,
    Item,
    markdown_table,
    names_equal,
    normalize_timing,
    pair_and_score,
    summarize,
)


def _model(name, timing=None, status="OK", unclear=False):
    return {"name": name, "timing_code": timing, "status": status, "unclear": unclear}


def _key(name, timing=None):
    return {"medicine_name": name, "timing_code": timing, "group": "A", "kind": "printed"}


def test_names_equal_ignores_case_space_and_punctuation():
    assert names_equal("Dolo 650", "dolo650") is True
    assert names_equal("Zerodol-P", "zerodol p") is True


def test_names_equal_does_not_treat_a_brand_and_a_generic_as_the_same():
    # TODO placeholder: the human decides equivalence in eval/scoring_rules.md.
    assert names_equal("Dolo 650", "Paracetamol 650 mg") is False


def test_normalize_timing_strips_and_uppercases():
    assert normalize_timing(" bd ") == "BD"
    assert normalize_timing(None) == ""
    assert normalize_timing("1 - 0 - 1") == "1 - 0 - 1"


def test_a_correct_row_is_correct():
    items = pair_and_score("a.jpg", "A", "printed", [_model("Dolo 650", "1-0-1")], [_key("Dolo 650", "1-0-1")])
    assert len(items) == 1
    assert items[0].outcome == CORRECT
    assert items[0].origin == "paired"
    assert items[0].name_correct is True
    assert items[0].timing_correct is True


def test_a_right_name_with_the_wrong_timing_is_wrong_but_flagged_when_flagged():
    items = pair_and_score(
        "a.jpg", "A", "printed", [_model("Dolo 650", "BD", status="Unclear")], [_key("Dolo 650", "1-0-1")]
    )
    assert items[0].outcome == WRONG_FLAGGED
    assert items[0].name_correct is True
    assert items[0].timing_correct is False


def test_a_wrong_row_that_is_not_flagged_is_dangerous():
    items = pair_and_score("a.jpg", "A", "printed", [_model("Dolo 650", "BD")], [_key("Dolo 650", "1-0-1")])
    assert items[0].outcome == DANGEROUS


def test_a_baseline_row_has_no_status_so_it_is_never_flagged():
    baseline_row = {"name": "Dolo 650", "timing_code": "BD", "status": ""}
    items = pair_and_score("a.jpg", "A", "printed", [baseline_row], [_key("Dolo 650", "1-0-1")])
    assert items[0].outcome == DANGEROUS


def test_a_key_medicine_with_no_model_row_is_missed_and_dangerous():
    items = pair_and_score("a.jpg", "A", "printed", [], [_key("Dolo 650", "1-0-1")])
    assert items[0].origin == "missed"
    assert items[0].outcome == DANGEROUS


def test_a_model_row_not_in_the_key_is_extra():
    items = pair_and_score("a.jpg", "A", "printed", [_model("Zzzz", "BD")], [_key("Dolo 650", "1-0-1")])
    origins = {item.origin for item in items}
    assert origins == {"extra", "missed"}
    assert len(items) == 2


def test_an_extra_row_that_is_flagged_is_not_dangerous():
    items = pair_and_score(
        "a.jpg", "A", "printed", [_model("Zzzz", "BD", status="Unclear")], [_key("Dolo 650", "1-0-1")]
    )
    extra = next(item for item in items if item.origin == "extra")
    assert extra.outcome == WRONG_FLAGGED


def test_two_model_rows_pair_with_two_key_rows_not_crosswise():
    model = [_model("Dolo 650", "1-0-1"), _model("Monocef", "BD")]
    key = [_key("Monocef", "BD"), _key("Dolo 650", "1-0-1")]
    items = pair_and_score("a.jpg", "A", "printed", model, key)
    assert len(items) == 2
    assert all(item.outcome == CORRECT for item in items)
    # Each model row paired with the key row of the same medicine, not just any.
    for item in items:
        assert item.name_correct is True


def test_a_model_row_below_the_pairing_threshold_is_extra_not_paired():
    # "Paracetamol" against "Dolo 650" scores far below the 60 threshold.
    items = pair_and_score(
        "a.jpg", "A", "printed", [_model("Paracetamol", "BD")], [_key("Dolo 650", "1-0-1")]
    )
    origins = {item.origin for item in items}
    assert origins == {"extra", "missed"}


def test_pairing_threshold_can_be_raised_to_force_a_miss():
    items = pair_and_score(
        "a.jpg", "A", "printed", [_model("Dolo 65O", "1-0-1")], [_key("Dolo 650", "1-0-1")], pairing_threshold=95
    )
    assert {item.origin for item in items} == {"extra", "missed"}


def test_an_unreadable_leftover_row_pairs_by_reading_order():
    model = [_model("Dolo 650", "1-0-1"), _model(None, None, status="Unclear", unclear=True)]
    key = [_key("Dolo 650", "1-0-1"), _key("Monocef", "BD")]
    items = pair_and_score("a.jpg", "A", "printed", model, key)
    assert len(items) == 2
    unreadable = next(item for item in items if item.model_name is None)
    assert unreadable.key_name == "Monocef"
    assert unreadable.note == "paired to an unreadable row in reading order"
    # The unreadable row is flagged, so it is wrong but flagged, never dangerous.
    assert unreadable.outcome == WRONG_FLAGGED


def test_no_key_rows_means_nothing_is_scored():
    assert pair_and_score("a.jpg", "A", "printed", [_model("Dolo 650")], []) == []


def test_summarize_counts_each_outcome():
    items = [
        Item(image_file="a", group="A", kind="printed", outcome=CORRECT, origin="paired", name_correct=True, timing_correct=True),
        Item(image_file="a", group="A", kind="printed", outcome=WRONG_FLAGGED, origin="paired", name_correct=True, timing_correct=False, status="Unclear"),
        Item(image_file="a", group="A", kind="printed", outcome=DANGEROUS, origin="extra", model_name="X", status="OK"),
        Item(image_file="a", group="A", kind="printed", outcome=DANGEROUS, origin="missed", key_name="Y"),
    ]
    summary = summarize(items, {"a.jpg": 2.0}, total_images=1)
    assert summary["items"] == 4
    assert summary["correct"] == 1
    assert summary["wrong_but_flagged"] == 1
    assert summary["wrong_and_not_flagged"] == 2
    assert summary["missed"] == 1
    assert summary["extra"] == 1
    assert summary["name_accuracy"] == 1.0  # both paired rows had the right name
    assert summary["timing_accuracy"] == 0.5
    assert summary["seconds_per_image"] == 2.0


def test_summarize_reports_none_rather_than_zero_when_there_is_nothing_to_rate():
    summary = summarize([], {}, total_images=0)
    assert summary["name_accuracy"] is None
    assert summary["timing_accuracy"] is None
    assert summary["unclear_rate"] is None


def test_summarize_reports_printed_and_handwritten_separately():
    items = [
        Item(image_file="p", group="A", kind="printed", outcome=CORRECT, origin="paired", name_correct=True, timing_correct=True),
        Item(image_file="h", group="A", kind="handwritten", outcome=DANGEROUS, origin="extra", model_name="X"),
    ]
    summary = summarize(items)
    assert summary["by_kind"]["printed"]["correct"] == 1
    assert summary["by_kind"]["handwritten"]["wrong_and_not_flagged"] == 1


def test_the_markdown_table_contains_every_metric():
    summary = summarize(
        [Item(image_file="a", group="A", kind="printed", outcome=CORRECT, origin="paired", name_correct=True, timing_correct=True)]
    )
    table = markdown_table(summary)
    for label in (
        "Correct",
        "Wrong but flagged",
        "Wrong and NOT flagged (dangerous)",
        "Name accuracy",
        "Timing accuracy",
        "Unclear rate",
        "Seconds per image",
    ):
        assert label in table


def test_item_as_dict_is_csv_friendly():
    item = Item(image_file="a.jpg", group="A", kind="printed", outcome=CORRECT, origin="paired", name_correct=True)
    row = item.as_dict()
    assert row["name_correct"] == "yes"
    assert row["pair_score"] == ""
    assert set(row) == {
        "image_file",
        "group",
        "kind",
        "origin",
        "outcome",
        "key_name",
        "model_name",
        "status",
        "key_timing",
        "model_timing",
        "name_correct",
        "timing_correct",
        "pair_score",
        "note",
    }