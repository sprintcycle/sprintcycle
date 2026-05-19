#!/usr/bin/env python3
"""Run the Frontend dev server for Playwright E2E."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=5173)
    args = ap.parse_args()

    cmd = ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(args.port)]
    subprocess.run(cmd, cwd=ROOT / "frontend", check=True)


if __name__ == "__main__":
    main()
