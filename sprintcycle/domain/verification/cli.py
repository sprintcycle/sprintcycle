from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import click

from ...infrastructure.config import RuntimeConfig
from .config import VerificationConfig
from .engine import VerificationEngine
from .reporter import VerificationReportAdapter


@click.group()
def verification() -> None:
    """多源验证入口。"""


@verification.command("check")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.option("--gate", type=click.Choice(["test", "verify", "arch", "security", "all"], case_sensitive=False), default="all", show_default=True)
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
@click.option("--pytest-command", default=None, help="覆盖 pytest 命令")
@click.option("--cli-command", default=None, help="覆盖 CLI 验证命令")
def verification_check(project: Path, gate: str, json_output: bool, pytest_command: Optional[str], cli_command: Optional[str]) -> None:
    runtime_config = RuntimeConfig.from_project(str(project))
    cfg = VerificationConfig.from_runtime_config(runtime_config, str(project))
    engine = VerificationEngine(cfg)
    context = {"project_path": str(project)}
    if pytest_command:
        context["pytest_command"] = pytest_command
    if cli_command:
        context["cli_command"] = cli_command

    report = asyncio.run(engine.run(gate, str(project), context=context))
    gov = VerificationReportAdapter.to_governance_report(report)
    payload = gov.to_dict()
    payload["success"] = not gov.has_error_severity()
    payload["gate"] = gate

    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"gate={gate} success={payload['success']} violations={len(payload.get('violations', []))}")
        for v in payload.get("violations", []):
            click.echo(f"- [{v['severity']}] {v['rule_id']}: {v['message']}")
    raise SystemExit(0 if payload["success"] else 1)
