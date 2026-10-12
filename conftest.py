"""Make the project root and eval/ importable from the tests, however pytest is run."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT, ROOT / "eval"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))