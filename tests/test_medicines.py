"""Medicine list tests. Temporary CSVs and a temporary database only."""

import sqlite3

import pytest

from app.medicines import (
    MedicineListError,
    connect,
    load_csv_into_db,
    read_all,
    read_csv,
    replace_all,
)

HEADER = "brand_name,generic_name,strength,use\n"


def _write(tmp_path, body, name="meds.csv", header=HEADER):
    path = tmp_path / name
    path.write_text(header + body, encoding="utf-8")
    return path


def test_a_valid_csv_loads_into_sqlite(tmp_path):
    path = _write(tmp_path, "Dolo 650,Paracetamol,650 mg,fever\n")
    db = tmp_path / "meds.db"
    count, rows = load_csv_into_db(path, db)
    assert count == 1
    assert rows[0]["brand_name"] == "Dolo 650"
    stored = read_all(db)
    assert stored == [
        {"brand_name": "Dolo 650", "generic_name": "Paracetamol", "strength": "650 mg", "use": "fever"}
    ]


def test_a_missing_column_is_reported_by_name(tmp_path):
    path = _write(tmp_path, "Dolo 650,Paracetamol\n", header="brand_name,generic_name\n")
    with pytest.raises(MedicineListError) as excinfo:
        read_csv(path)
    message = str(excinfo.value)
    assert "strength" in message and "use" in message


def test_a_csv_with_no_header_is_reported(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(MedicineListError):
        read_csv(path)


def test_a_csv_with_no_medicine_rows_is_reported(tmp_path):
    path = _write(tmp_path, "")
    with pytest.raises(MedicineListError) as excinfo:
        read_csv(path)
    assert "no medicine rows" in str(excinfo.value)


def test_a_row_with_no_brand_name_is_skipped_not_invented(tmp_path):
    path = _write(tmp_path, ",Paracetamol,650 mg,fever\nDolo 650,Paracetamol,650 mg,fever\n")
    rows = read_csv(path)
    assert len(rows) == 1
    assert rows[0]["brand_name"] == "Dolo 650"


def test_blank_optional_fields_become_null(tmp_path):
    path = _write(tmp_path, "Monocef,,,\n")
    rows = read_csv(path)
    assert rows[0]["generic_name"] is None
    assert rows[0]["strength"] is None
    assert rows[0]["use"] is None


def test_values_are_stripped(tmp_path):
    path = _write(tmp_path, "  Dolo 650 , Paracetamol , 650 mg , fever \n")
    rows = read_csv(path)
    assert rows[0]["brand_name"] == "Dolo 650"
    assert rows[0]["generic_name"] == "Paracetamol"


def test_a_utf8_bom_header_is_tolerated(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_text("\ufeff" + HEADER + "Dolo 650,Paracetamol,650 mg,fever\n", encoding="utf-8")
    rows = read_csv(path)
    assert rows[0]["brand_name"] == "Dolo 650"


def test_loading_twice_replaces_rather_than_appends(tmp_path):
    db = tmp_path / "meds.db"
    load_csv_into_db(_write(tmp_path, "Dolo 650,Paracetamol,650 mg,fever\n", name="a.csv"), db)
    load_csv_into_db(_write(tmp_path, "Monocef,Ceftriaxone,1 g,infection\n", name="b.csv"), db)
    stored = read_all(db)
    assert [row["brand_name"] for row in stored] == ["Monocef"]


def test_replace_all_returns_the_row_count(tmp_path):
    connection = connect(tmp_path / "meds.db")
    count = replace_all(
        connection,
        [
            {"brand_name": "A", "generic_name": None, "strength": None, "use": None},
            {"brand_name": "B", "generic_name": None, "strength": None, "use": None},
        ],
    )
    connection.close()
    assert count == 2


def test_read_all_on_an_unloaded_database_returns_an_empty_list(tmp_path):
    assert read_all(tmp_path / "nothing.db") == []


def test_read_all_does_not_raise_when_the_table_is_missing(tmp_path):
    db = tmp_path / "bare.db"
    sqlite3.connect(db).close()  # a real database file with no medicines table
    assert read_all(db) == []


def test_connect_creates_the_table(tmp_path):
    db = tmp_path / "fresh.db"
    connection = connect(db)
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()
    assert "medicines" in tables


def test_reading_the_list_never_creates_a_database(tmp_path):
    """A read must not leave a file behind: an absent list is a normal state."""
    missing = tmp_path / "not_created.db"
    assert read_all(missing) == []
    assert not missing.exists()
    assert list(tmp_path.iterdir()) == []
