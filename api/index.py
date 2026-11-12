"""Vercel serverless entry point.

Vercel's Python runtime looks for an ASGI app named `app` in this file.
The real FastAPI app lives in main.py at the project root, so we re-export it.
Project root files (data/, static/, prompts/) are part of the function bundle.
"""

from main import app  # noqa: F401  (Vercel reads `app` from this module)
