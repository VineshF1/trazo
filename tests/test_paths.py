"""Path wiring tests.

These exist because moving the modules into app/ silently broke PROJECT_ROOT once:
every path hung off app/ instead of the project, and only a live request caught it.
"""

from pathlib import Path

from app.config import (
    CORRECTIONS_DB_PATH,
    DATA_DIR,
    MEDICINES_DB_PATH,
    PROJECT_ROOT,
)
from app.extract import load_prompt
from main import EXTRACT_PROMPT_PATH, STATIC_DIR


def test_project_root_is_the_repository_root():
    assert (PROJECT_ROOT / "main.py").is_file()
    assert (PROJECT_ROOT / "requirements.txt").is_file()
    assert PROJECT_ROOT.name != "app"


def test_the_extract_prompt_is_found_and_readable():
    assert EXTRACT_PROMPT_PATH.is_file()
    text = load_prompt(EXTRACT_PROMPT_PATH)
    assert "medicines" in text


def test_the_baseline_prompt_is_found_and_readable():
    path = PROJECT_ROOT / "prompts" / "baseline_prompt.txt"
    assert path.is_file()
    assert "medicines" in load_prompt(path)


def test_static_dir_is_the_project_static_dir():
    assert STATIC_DIR == PROJECT_ROOT / "static"
    assert STATIC_DIR.is_dir()


def test_the_databases_live_under_the_project_data_dir():
    assert DATA_DIR == PROJECT_ROOT / "data"
    assert MEDICINES_DB_PATH.parent == DATA_DIR
    assert CORRECTIONS_DB_PATH.parent == DATA_DIR


def test_the_referenced_folders_exist():
    for folder in ("prompts", "scripts", "data", "eval", "tests", "static", "tests_local"):
        assert (PROJECT_ROOT / folder).is_dir(), f"{folder}/ is missing"