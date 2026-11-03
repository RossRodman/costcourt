"""Entry point: `python -m app` or the `costcourt` script."""

from __future__ import annotations

import argparse

import uvicorn

from app.core.config import Environment, get_settings


def main(argv: list[str] | None = None) -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(prog="costcourt", description=__doc__)
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=settings.env is Environment.DEV,
        help="auto-reload on code changes (default: on in dev)",
    )
    args = parser.parse_args(argv)

    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.value.lower(),
    )


if __name__ == "__main__":
    main()
