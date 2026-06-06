"""CLI entrypoint: train the fraud classifier and write the artifact."""

from __future__ import annotations

from src.config import configure_logging
from src.models import train


def main() -> None:
    configure_logging()
    path = train.train()
    print(f"Model trained and saved to {path}")


if __name__ == "__main__":
    main()
