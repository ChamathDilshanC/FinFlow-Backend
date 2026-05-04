"""
Vercel legacy ``@vercel/python`` build entry.

The real application is built in :mod:`app.main`; this file only exposes ``app``
so ``vercel.json`` can point to ``main.py`` at the project root.
"""

from app.main import app

__all__ = ["app"]
