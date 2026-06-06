"""CLI entrypoint: score unscored returns using the trained artifact."""

from __future__ import annotations

from src.config import configure_logging
from src.models import predict


def main() -> None:
    configure_logging()
    n = predict.predict()
    print(f"Scored {n} returns")


if __name__ == "__main__":
    main()
