"""
SprintCycle CLI — 子命令式入口

命令结构:
  sprintcycle "意图"          → 快捷执行 (= run)
  sprintcycle plan "意图"     → 生成计划
  sprintcycle run "意图"      → 执行
  sprintcycle diagnose        → 体检
  sprintcycle status [id]     → 查状态
  sprintcycle rollback <id>   → 回滚
  sprintcycle stop <id>       → 停止
  sprintcycle serve           → 启动 MCP Server
  sprintcycle dashboard       → 启动 Dashboard (P2)
  sprintcycle init [path]     → 初始化项目
"""

import json
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import click

from sprintcycle.api import SprintCycle
from sprintcycle.results import (
    PlanResult, RunResult, DiagnoseResult,
    StatusResult, RollbackResult, StopResult,
)


def setup_logging(
    log_file: str = ".sprintcycle/logs/sprintcycle.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        root_logger.addHandler(console)

        file_h = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_h.setLevel(level)
        file_h.setFormatter(formatter)
        root_logger.addHandler(file_h)

    return logging.getLogger(__name__)


logger = setup_logging()


def _print_result(result: Any, fmt: str) -> None:
    """统一输出：text 格式人类友好，json 格式机器友好"""
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    # text 格式
    if isinstance(result, PlanResult):
        _print_plan(result)
    elif isinstance(result, RunResult):
        _print_run(result)
    elif isinstance(result, DiagnoseResult):
        _print_diagnose(result)
    elif isinstance(result, StatusResult):
        _print_status(result)
    elif isinstance(result, RollbackResult):
        _print_rollback(result)
    elif isinstance(result, StopResult):
        _print_stop(result)
    else:
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    if not result.success and result.error:
        click.echo(f"\n❌ 错误: {result.error}")
        sys.exit(1)


def _print_plan(r: PlanResult) -> None:
    click.echo(f"📋 Sprint 计划 (mode={r.mode})")
    click.echo(f"   项目: {r.prd_name}")
    click.echo(f"   Sprint 数: {len(r.sprints)}")
    for i, s in enumerate(r.sprints, 1):
        click.echo(f"\n   Sprint {i}: {s.get('name', '')}")
        for t in s.get("tasks", []):
            click.echo(f"     · {t}")
    click.echo(f"\n💡 使用 run(prd_yaml=...) 可直接执行此计划")


def _print_run(r: RunResult) -> None:
    status_icon = "✅" if r.success else "❌"
    click.echo(f"\n{status_icon} 执行{'成功' if r.success else '失败'}")
    click.echo(f"   项目: {r.prd_name}")
    click.echo(f"   Sprint: {r.completed_sprints}/{r.total_sprints}")
    click.echo(f"   任务: {r.completed_tasks}/{r.total_tasks}")
    if r.execution_id:
        click.echo(f"   执行ID: {r.execution_id}")
    click.echo(f"   耗时: {r.duration:.1f}s")

    for sr in r.sprint_results:
        sprint_status = "✅" if sr.get("status") in ("success", "skipped") else "❌"
        click.echo(
            f"\n   📦 {sr.get('sprint_name', '?')} {sprint_status} "
            f"({sr.get('success_count', 0)}/{sr.get('task_count', 0)} 任务, {sr.get('duration', 0):.1f}s)"
        )


def _print_diagnose(r: DiagnoseResult) -> None:
    click.echo(f"🏥 项目体检")
    click.echo(f"   健康度: {r.health_score:.0f}/100")
    click.echo(f"   覆盖率: {r.coverage:.1%}")
    if r.issues:
        click.echo(f"   问题: {len(r.issues)}")
        for issue in r.issues[:5]:
            click.echo(f"     · [{issue.get('severity', '?')}] {issue.get('message', '')}")
    else:
        click.echo("   问题: 无")


def _print_status(r: StatusResult) -> None:
    if r.executions:
        click.echo(f"📜 执行历史 ({len(r.executions)} 条)")
        for e in r.executions[:10]:
            click.echo(
                f"   · {e.get('execution_id', '?')} [{e.get('status', '?')}] "
                f"{e.get('prd_name', '')} Sprint {e.get('current_sprint', 0)}/{e.get('total_sprints', 0)}"
            )
    else:
        click.echo(f"📜 执行状态: {r.execution_id}")
        click.echo(f"   状态: {r.status}")
        click.echo(f"   Sprint: {r.current_sprint}/{r.total_sprints}")
        if r.sprint_history:
            click.echo(f"   历史:")
            for h in r.sprint_history[-3:]:
                click.echo(f"     · {h.get('sprint_name', '?')} → {h.get('status', '?')}")


def _print_rollback(r: RollbackResult) -> None:
    icon = "✅" if r.success else "❌"
    click.echo(f"{icon} 回滚 (→ {r.rollback_point})")
    if r.files_restored:
        click.echo(f"   恢复文件: {len(r.files_restored)}")


def _print_stop(r: StopResult) -> None:
    icon = "✅" if r.cancelled else "❌"
    click.echo(f"{icon} 停止执行: {r.execution_id}")
    click.echo(f"   {r.message}")


# ─── CLI 入口 ───


@click.group(invoke_without_command=True)
@click.option("-p", "--project", default=".", help="项目路径")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.version_option(version="0.9.1", prog_name="sprintcycle")
@click.pass_context
def cli(ctx: click.Context, project: str, fmt: str, verbose: bool) -> None:
    """SprintCycle - PRD 驱动的自进化框架

    一切皆 PRD: 意图 → PRD 生成器 → 执行引擎

    \b
    快捷用法:
      sprintcycle "优化性能"              # 等同于 sprintcycle run
    """
    ctx.ensure_object(dict)
    ctx.obj["sc"] = SprintCycle(project_path=project)
    ctx.obj["fmt"] = fmt
    ctx.obj["verbose"] = verbose

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 无子命令时，将参数当作 run
    if ctx.invoked_subcommand is None:
        args = ctx.args
        if args:
            result = ctx.obj["sc"].run(intent=" ".join(args))
            _print_result(result, fmt)
        else:
            click.echo(ctx.get_help())


# ─── plan ───


@cli.command()
@click.argument("intent")
@click.option("-m", "--mode", default="auto", type=click.Choice(["auto", "evolution", "normal", "fix", "test"]))
@click.option("-t", "--target", default=None, help="目标文件/模块")
@click.option("--prd", "prd_path", default=None, help="已有 PRD 文件路径")
@click.pass_context
def plan(ctx: click.Context, intent: str, mode: str, target: Optional[str], prd_path: Optional[str]) -> None:
    """生成 Sprint 执行计划（不执行）"""
    result = ctx.obj["sc"].plan(intent=intent, mode=mode, target=target, prd_path=prd_path)
    _print_result(result, ctx.obj["fmt"])


# ─── run ───


@cli.command()
@click.argument("intent", required=False)
@click.option("-m", "--mode", default="auto", type=click.Choice(["auto", "evolution", "normal", "fix", "test"]))
@click.option("-t", "--target", default=None, help="目标文件/模块")
@click.option("--prd", "prd_path", default=None, help="PRD 文件路径")
@click.option("--prd-yaml", "prd_yaml", default=None, help="PRD YAML 内容")
@click.option("--resume", is_flag=True, help="断点续跑")
@click.option("--execution-id", default=None, help="执行 ID（resume 时使用）")
@click.pass_context
def run(
    ctx: click.Context,
    intent: Optional[str],
    mode: str,
    target: Optional[str],
    prd_path: Optional[str],
    prd_yaml: Optional[str],
    resume: bool,
    execution_id: Optional[str],
) -> None:
    """执行 Sprint"""
    result = ctx.obj["sc"].run(
        intent=intent, mode=mode, target=target,
        prd_path=prd_path, prd_yaml=prd_yaml,
        resume=resume, execution_id=execution_id,
    )
    _print_result(result, ctx.obj["fmt"])


# ─── diagnose ───


@cli.command()
@click.pass_context
def diagnose(ctx: click.Context) -> None:
    """诊断项目健康状态"""
    result = ctx.obj["sc"].diagnose()
    _print_result(result, ctx.obj["fmt"])


# ─── status ───


@cli.command()
@click.argument("execution_id", required=False)
@click.pass_context
def status(ctx: click.Context, execution_id: Optional[str]) -> None:
    """查询执行状态（不传 ID 则列出所有记录）"""
    result = ctx.obj["sc"].status(execution_id=execution_id)
    _print_result(result, ctx.obj["fmt"])


# ─── rollback ───


@cli.command()
@click.argument("execution_id")
@click.pass_context
def rollback(ctx: click.Context, execution_id: str) -> None:
    """回滚到执行前的状态"""
    result = ctx.obj["sc"].rollback(execution_id=execution_id)
    _print_result(result, ctx.obj["fmt"])


# ─── stop ───


@cli.command()
@click.argument("execution_id")
@click.pass_context
def stop(ctx: click.Context, execution_id: str) -> None:
    """停止正在执行的 Sprint"""
    result = ctx.obj["sc"].stop(execution_id=execution_id)
    _print_result(result, ctx.obj["fmt"])


# ─── serve (MCP Server) ───


@cli.command()
@click.option("--host", default="0.0.0.0", help="MCP Server host")
@click.option("--port", default=8080, type=int, help="MCP Server port")
@click.option("--transport", type=click.Choice(["stdio", "sse"]), default="stdio", help="传输方式")
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, transport: str) -> None:
    """启动 MCP Server"""
    try:
        from sprintcycle.mcp.server import SprintCycleMCPServer, MCP_AVAILABLE

        if not MCP_AVAILABLE:
            click.echo("❌ MCP SDK 未安装，请执行: pip install mcp")
            sys.exit(1)

        server = SprintCycleMCPServer(project_path=ctx.obj["sc"].project_path)
        if transport == "stdio":
            click.echo("🚀 MCP Server 启动 (stdio)", err=True)
            asyncio.run(server.run())
        else:
            click.echo(f"🚀 MCP Server 启动 (SSE {host}:{port})", err=True)
            # SSE 模式将在后续实现
            click.echo("❌ SSE 模式尚未实现")
            sys.exit(1)
    except ImportError:
        click.echo("❌ MCP 模块未找到")
        sys.exit(1)


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8080, type=int, help="监听端口")
@click.pass_context
def dashboard(ctx: click.Context, host: str, port: int) -> None:
    """启动 Dashboard (Web UI)"""
    try:
        import uvicorn
        from sprintcycle.dashboard.app import create_app

        app = create_app(project_path=ctx.obj["sc"].project_path)
        click.echo(f"🚀 Dashboard 启动: http://{host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")
    except ImportError as e:
        click.echo(f"❌ 依赖缺失: {e}")
        click.echo("   安装命令: pip install fastapi uvicorn")
        sys.exit(1)


# ─── init ───


@cli.command()
@click.argument("path", default=".")
@click.pass_context
def init(ctx: click.Context, path: str) -> None:
    """初始化项目"""
    project_path = Path(path)
    project_path.mkdir(parents=True, exist_ok=True)

    state_dir = project_path / ".sprintcycle" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    log_dir = project_path / ".sprintcycle" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"✅ 项目初始化完成: {project_path}")
    click.echo(f"   状态目录: {state_dir}")
    click.echo(f"   日志目录: {log_dir}")


if __name__ == "__main__":
    cli()
