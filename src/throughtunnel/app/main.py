"""Command-line entry point: ``uv run throughtunnel``."""

from __future__ import annotations

import argparse

from nicegui import ui


def run() -> None:
    parser = argparse.ArgumentParser(description="ThroughTunnel vehicle simulator UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser window")
    args = parser.parse_args()

    import throughtunnel.app.page  # noqa: F401  (registers the page routes)

    ui.run(
        title="ThroughTunnel",
        host=args.host,
        port=args.port,
        show=not args.no_browser,
        reload=False,
        favicon="🚗",
    )


if __name__ in {"__main__", "__mp_main__"}:
    run()
