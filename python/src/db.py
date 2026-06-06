"""SQLAlchemy engine factory.

All warehouse access in this project goes through `get_engine()`. Don't open
`psycopg2` connections directly — keep connection pooling and config in one place.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .config import DATABASE_URL

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return a process-wide SQLAlchemy engine, creating it on first call."""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    return _engine


def dispose_engine() -> None:
    """Close the pooled engine. Call from tests so connections don't leak."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
