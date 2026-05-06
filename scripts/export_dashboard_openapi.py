#!/usr/bin/env python3
"""Write Dashboard FastAPI OpenAPI schema for openapi-typescript (see frontend/package.json)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ROOT / "frontend" / "openapi-dashboard.json",
        help="Output JSON path",
    )
    ap.add_argument("--project", default=str(ROOT), help="SprintCycle project path passed to create_app")
    args = ap.parse_args()

    from sprintcycle.dashboard.server import create_app

    app = create_app(project_path=args.project)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
