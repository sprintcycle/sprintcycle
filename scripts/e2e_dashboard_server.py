#!/usr/bin/env python3
"""Run the Dashboard FastAPI app for Playwright E2E (see frontend/playwright.config.ts)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--project", default=str(ROOT))
    args = ap.parse_args()

    import uvicorn
    from sprintcycle.dashboard.server import create_app

    app = create_app(project_path=args.project)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
