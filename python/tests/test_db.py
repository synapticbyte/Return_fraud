"""Smoke test: the engine factory wires up and reuses the same engine."""

from __future__ import annotations

import os

import pytest

# Set a dummy URL before importing modules that read DATABASE_URL.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from src import db  # noqa: E402


def test_get_engine_returns_cached_instance() -> None:
    db.dispose_engine()
    a = db.get_engine()
    b = db.get_engine()
    assert a is b


def test_dispose_engine_drops_reference() -> None:
    db.dispose_engine()
    a = db.get_engine()
    db.dispose_engine()
    b = db.get_engine()
    assert a is not b


@pytest.mark.skip(reason="Live DB connection test — run manually with a real DATABASE_URL.")
def test_engine_connects() -> None:
    engine = db.get_engine()
    with engine.connect() as conn:
        from sqlalchemy import text

        assert conn.execute(text("SELECT 1")).scalar() == 1
