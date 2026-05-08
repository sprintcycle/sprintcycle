from __future__ import annotations

import argparse
import asyncio

from .config import ArchGuardConfig
from .engine import ArchGuardEngine
from .reporter import GovernanceReportAdapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sprintcycle governance")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--gate", choices=["planning", "review"], default="review")
    check.add_argument("--project-root", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = ArchGuardConfig(project_root=args.project_root)
    engine = ArchGuardEngine(cfg)

    if args.command == "check":
        if args.gate == "planning":
            raise SystemExit("planning gate 需要 release_plan，上层 API/Hook 调用更合适")
        report = asyncio.run(engine.run_review_gate(args.project_root, context={}))
        gov = GovernanceReportAdapter.to_governance_report(report)
        print(gov.to_dict())
        return 1 if gov.has_error_severity() else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
