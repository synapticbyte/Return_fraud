"""Convenience runner for `python -m scripts <command>`.

Example:
  python -m scripts generate_dummy_data
  python -m scripts run_etl

This repo stores all packages under `python/`, so this runner also adjusts
sys.path to include that folder when executed from the repo root.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def _ensure_python_on_syspath() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    python_dir = repo_root / "python"
    sys.path.insert(0, str(python_dir))


def main() -> None:
    _ensure_python_on_syspath()
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m scripts [generate_dummy_data|run_etl]")

    mod = sys.argv[1]
    runpy.run_module(f"scripts.{mod}", run_name="__main__")


if __name__ == "__main__":
    main()

