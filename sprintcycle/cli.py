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
from .verification.cli import verification as verification_group
from .api import SprintCycle


@click.group()
def cli() -> None:
    """SprintCycle 命令行入口。"""


cli.add_command(verification_group)
cli.add_command(governance_hitl, name="hitl")


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


@governance.command("hitl")
@click.group()
def governance_hitl() -> None:
    """HITL 管理命令。"""


@governance_hitl.command("pending")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.option("--execution-id", default=None, help="可选，仅该执行 ID 下的记录")
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_hitl_pending(project: Path, execution_id: Optional[str], json_output: bool) -> None:
    """列出待决策 HITL 请求。"""
    sc = SprintCycle(str(project))
    import asyncio

    payload = asyncio.run(sc.hitl_pending(execution_id=execution_id))
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for row in payload.get("data", []):
            click.echo(f"- {row.get('request_id')} [{row.get('gate')}] {row.get('title')} ({row.get('status')})")


@governance_hitl.command("history")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.option("--execution-id", default=None, help="可选，仅该执行 ID 下的记录")
@click.option("--limit", default=50, show_default=True, type=int)
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_hitl_history(project: Path, execution_id: Optional[str], limit: int, json_output: bool) -> None:
    """列出 HITL 历史记录。"""
    sc = SprintCycle(str(project))
    import asyncio

    payload = asyncio.run(sc.hitl_history(execution_id=execution_id, limit=limit))
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for row in payload.get("data", []):
            click.echo(f"- {row.get('request_id')} [{row.get('gate')}] {row.get('decision') or 'pending'}")


@governance_hitl.command("show")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.argument("request_id")
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_hitl_show(project: Path, request_id: str, json_output: bool) -> None:
    """显示单条 HITL 记录。"""
    sc = SprintCycle(str(project))
    import asyncio

    payload = asyncio.run(sc.hitl_show(request_id))
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not payload.get("success"):
            click.echo(payload.get("error", "unknown error"))
            raise SystemExit(1)
        row = payload["data"]
        click.echo(f"{row.get('request_id')} [{row.get('gate')}] {row.get('title')}")
        click.echo(f"status={row.get('status')} decision={row.get('decision')} note={row.get('decision_note')}")


@governance_hitl.command("submit")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.argument("request_id")
@click.argument("decision")
@click.option("--note", default=None, help="附注")
@click.option("--correction-json", default=None, help="修正 JSON")
@click.option("--replay-json", default=None, help="重试指令 JSON")
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_hitl_submit(project: Path, request_id: str, decision: str, note: Optional[str], correction_json: Optional[str], replay_json: Optional[str], json_output: bool) -> None:
    """提交 HITL 决策、修正或重试。"""
    sc = SprintCycle(str(project))
    import asyncio

    correction = json.loads(correction_json) if correction_json else None
    replay = json.loads(replay_json) if replay_json else None
    payload = asyncio.run(sc.hitl_submit(request_id, decision, note=note, correction=correction, replay=replay))
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not payload.get("success"):
            click.echo(payload.get("error", "unknown error"))
            raise SystemExit(1)
        row = payload["data"]
        click.echo(f"submitted {row.get('request_id')} decision={row.get('decision')} status={row.get('status')}")


@governance_hitl.command("modify")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.argument("request_id")
@click.option("--note", default=None, help="修改建议或备注")
@click.option("--correction-json", required=True, help="结构化修正 JSON")
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_hitl_modify(project: Path, request_id: str, note: Optional[str], correction_json: str, json_output: bool) -> None:
    """提交 request_changes / modify。"""
    sc = SprintCycle(str(project))
    import asyncio

    payload = asyncio.run(sc.hitl_submit(request_id, "request_changes", note=note, correction=json.loads(correction_json)))
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not payload.get("success"):
            click.echo(payload.get("error", "unknown error"))
            raise SystemExit(1)
        row = payload["data"]
        click.echo(f"modified {row.get('request_id')} status={row.get('status')}")


@governance_hitl.command("retry")
@click.option("-p", "--project", required=True, type=click.Path(path_type=Path), help="目标项目路径")
@click.argument("request_id")
@click.option("--note", default=None, help="重试说明")
@click.option("--replay-json", required=True, help="重试指令 JSON")
@click.option("--json-output", is_flag=True, help="以 JSON 输出结果")
def governance_hitl_retry(project: Path, request_id: str, note: Optional[str], replay_json: str, json_output: bool) -> None:
    """提交 retry / replay。"""
    sc = SprintCycle(str(project))
    import asyncio

    payload = asyncio.run(sc.hitl_submit(request_id, "retry", note=note, replay=json.loads(replay_json)))
    if json_output:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not payload.get("success"):
            click.echo(payload.get("error", "unknown error"))
            raise SystemExit(1)
        row = payload["data"]
        click.echo(f"retry requested {row.get('request_id')} status={row.get('status')}")


if __name__ == "__main__":
    cli()
