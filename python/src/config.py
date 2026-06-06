"""Centralized config: env vars, paths, constants.

All other modules import from here so behavior is consistent and testable.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", REPO_ROOT / "data")).resolve()
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"
MODEL_ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "models" / "artifacts"

DEFAULT_MODEL_PATH = os.getenv(
    "FRAUD_MODEL_PATH",
    str(MODEL_ARTIFACT_DIR / "fraud_v1.joblib"),
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://returns:returns@localhost:5432/returns_db")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging() -> None:
    """Idempotent root-logger setup. Call once at script startup."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
