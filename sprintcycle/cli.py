"""SprintCycle CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import click

from .config import RuntimeConfig
from .execution.project_write import ProjectWriteStrategy
from .governance.arch_guard.config import ArchGuardConfig
from .governance.arch_guard.engine import ArchGuardEngine
from .governance.arch_guard.reporter import GovernanceReportAdapter
from .release_plan.parser import ReleasePlanParser


@click.group()
def cli() -> None:
    """SprintCycle 命令行入口。"""


@cli.command()
@click.argument("intent")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.option("--reference", "references", multiple=True, type=click.Path(path_type=Path), help="参考项目路径，可重复")
@click.option("--write-policy", type=click.Choice(["create", "incremental", "safe"], case_sensitive=False), default="incremental", show_default=True)
def run(intent: str, project: Path, references: List[Path], write_policy: str) -> None:
    """统一运行入口：新建、增量修改、参考生成。"""
    config = RuntimeConfig(project_path=str(project), reference_projects=[str(p) for p in references], write_policy=write_policy)
    strategy = ProjectWriteStrategy(str(project), [str(p) for p in references], write_policy=config.write_policy)
    plan = strategy.build_plan(intent)
    applied = strategy.apply_template(plan)
    summary = strategy.write_summary(applied)
    click.echo(json.dumps({"project": str(project), "references": [str(p) for p in references], "write_policy": write_policy, "target_exists": applied.target_exists, "created_files": applied.created_files, "modified_files": applied.modified_files, "skipped_files": applied.skipped_files, "backups": [b.__dict__ for b in applied.backups], "git": applied.git.__dict__ if applied.git else None, "summary": str(summary)}, ensure_ascii=False, indent=2))


@cli.group()
def governance() -> None:
    """架构治理相关命令。"""


@governance.command("check")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.option("--gate", type=click.Choice(["planning", "review"], case_sensitive=False), default="review", show_default=True)
@click.option("--release-plan", type=click.Path(path_type=Path), default=None, help="Planning gate 用的 ReleasePlan YAML 文件")
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_check(project: Path, gate: str, release_plan: Optional[Path], json_output: bool) -> None:
    """执行架构治理检查。"""
    runtime_config = RuntimeConfig.from_project(str(project))
    cfg = ArchGuardConfig.from_runtime_config(runtime_config, str(project))
    engine = ArchGuardEngine(cfg)
    context = {"project_path": str(project)}

    if gate == "planning":
        if release_plan is None:
            raise click.UsageError("planning gate 需要提供 --release-plan")
        plan = ReleasePlanParser().parse_file(str(release_plan))
        import asyncio

        report = asyncio.run(engine.run_planning_gate(str(project), release_plan=plan, context=context))
    else:
        import asyncio

        report = asyncio.run(engine.run_review_gate(str(project), context=context))

    gov = GovernanceReportAdapter.to_governance_report(report)
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


if __name__ == "__main__":
    cli()
