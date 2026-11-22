"""Beejak application entry point.

    python3 run.py
    python3 run.py --host 0.0.0.0 --port 8080 --debug
"""
from __future__ import annotations

import argparse

from app import create_app
from config import DEV_GITHUB, DEV_NAME, DEV_TAGLINE

app = create_app()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Beejak billing studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    print(f"Beejak by {DEV_NAME} — {DEV_TAGLINE}")
    print(f"Open http://{args.host}:{args.port}  •  {DEV_GITHUB}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
