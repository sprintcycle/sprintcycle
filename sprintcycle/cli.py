"""
SprintCycle CLI — 子命令式入口

命令结构:
  sprintcycle "意图"          → 快捷执行 (= run)
  sprintcycle plan "意图"     → 生成计划
  sprintcycle run "意图"      → 执行
  sprintcycle wizard          → 交互式向导（questionary）
  sprintcycle diagnose        → 体检
  sprintcycle status [id]     → 查状态
  sprintcycle rollback <id>   → 回滚
  sprintcycle stop <id>       → 停止
  sprintcycle serve           → 启动 MCP Server
  sprintcycle dashboard [--dev] → 启动 Dashboard（`--dev` 同启 Vite）
  sprintcycle init [path]     → 初始化项目
  sprintcycle import-state    → JSON 状态目录导入 SQLite
  sprintcycle knowledge search → 检索知识卡片
  sprintcycle hitl pending|submit|history|show → 人机卡点（读库 show 不依赖 enabled）
  sprintcycle execution-events <id> → 只读 SQLite 执行事件回放
  sprintcycle governance check → 治理门禁（Review/Planning）
  sprintcycle governance model-compare [--quick] → 双跑 pytest 对比失败集合
  sprintcycle product … → Docker Compose 构建/启停日志
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Optional

import click
import questionary
from questionary import Choice
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as install_rich_traceback

from sprintcycle.api import SprintCycle
from sprintcycle.logging_setup import configure_sprintcycle_logging
from sprintcycle.release_plan.payload_keys import dict_plan_name
from sprintcycle.results import (
    DiagnoseResult,
    PlanResult,
    RollbackResult,
    RunResult,
    StatusResult,
    StopResult,
)

console = Console()
err_console = Console(stderr=True)
_rich_traceback_installed = False


def _package_version() -> str:
    try:
        return version("sprintcycle")
    except PackageNotFoundError:
        return "0.0.0"


def _ensure_rich_traceback() -> None:
    global _rich_traceback_installed
    if _rich_traceback_installed:
        return
    install_rich_traceback(show_locals=False, suppress=[click])
    _rich_traceback_installed = True


def _print_result(result: Any, fmt: str) -> None:
    """统一输出：text 格式人类友好，json 格式机器友好"""
    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        if isinstance(result, RunResult) and getattr(
            result, "pending_knowledge_confirmation", False
        ):
            sys.exit(3)
        return

    if isinstance(result, PlanResult):
        _print_plan(result)
    elif isinstance(result, RunResult):
        _print_run(result)
        if getattr(result, "pending_knowledge_confirmation", False):
            sys.exit(3)
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
        err_console.print(f"\n[bold red]错误:[/bold red] {escape(str(result.error))}")
        sys.exit(1)


def _print_plan(r: PlanResult) -> None:
    table = Table(title=f"Sprint 计划 [dim](mode={escape(r.mode)})[/dim]", show_lines=True)
    table.add_column("#", style="cyan", justify="right", width=3)
    table.add_column("Sprint", style="bold")
    table.add_column("任务", style="white")

    for i, s in enumerate(r.sprints, 1):
        tasks = s.get("tasks") or []
        task_lines = "\n".join(f"· {escape(str(t))}" for t in tasks) or "—"
        table.add_row(str(i), escape(str(s.get("name", ""))), task_lines)

    console.print(
        Panel(
            table,
            title="[bold magenta]📋 Release Plan[/bold magenta]",
            subtitle=f"项目: {escape(r.release_plan_name)}  ·  {len(r.sprints)} 个 Sprint",
        )
    )
    console.print(
        "[dim]使用[/dim] [bold]run[/bold][dim](release_plan_yaml=...) 可直接执行此计划[/dim]"
    )


def _print_run(r: RunResult) -> None:
    if getattr(r, "pending_knowledge_confirmation", False):
        body_lines = [
            f"项目: [bold]{escape(r.release_plan_name)}[/bold]",
        ]
        pv = r.knowledge_injection_preview or {}
        cu = pv.get("cards_used") or []
        if cu:
            body_lines.append(f"引用知识卡片: [yellow]{len(cu)}[/yellow] 条")
        if r.message:
            body_lines.append(escape(str(r.message)))
        body_lines.append(
            "[dim]再次执行时请加上[/dim] [bold]--yes[/bold] [dim]以确认并落盘 release_plan_overlay.yaml[/dim]"
        )
        console.print(
            Panel(
                "\n".join(body_lines),
                title="[bold yellow]⏸ 知识注入待确认[/bold yellow]",
                subtitle="尚未执行 Sprint",
                border_style="yellow",
            )
        )
        return

    ok = r.success
    status_style = "bold green" if ok else "bold red"
    status_text = "执行成功" if ok else "执行失败"
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="dim", justify="right")
    summary.add_column()
    summary.add_row("项目", escape(r.release_plan_name))
    summary.add_row("Sprint", f"{r.completed_sprints}/{r.total_sprints}")
    summary.add_row("任务", f"{r.completed_tasks}/{r.total_tasks}")
    if r.execution_id:
        summary.add_row("执行ID", escape(r.execution_id))
    summary.add_row("耗时", f"{r.duration:.1f}s")

    console.print(
        Panel.fit(
            summary,
            title=f"[{status_style}]{status_text}[/{status_style}]",
            border_style="green" if ok else "red",
        )
    )

    if r.sprint_results:
        st = Table(title="Sprint 明细", show_header=True, header_style="bold")
        st.add_column("Sprint")
        st.add_column("状态", justify="center")
        st.add_column("任务", justify="right")
        st.add_column("耗时", justify="right")
        for sr in r.sprint_results:
            sprint_status = "✅" if sr.get("status") in ("success", "skipped") else "❌"
            st.add_row(
                escape(str(sr.get("sprint_name", "?"))),
                sprint_status,
                f"{sr.get('success_count', 0)}/{sr.get('task_count', 0)}",
                f"{float(sr.get('duration', 0)):.1f}s",
            )
        console.print(st)


def _print_diagnose(r: DiagnoseResult) -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim", justify="right")
    grid.add_column()
    grid.add_row("健康度", f"[bold]{r.health_score:.0f}[/bold]/100")
    grid.add_row("覆盖率", f"{r.coverage:.1%}")
    issues_n = len(r.issues)
    grid.add_row("问题数", str(issues_n) if issues_n else "[green]0[/green]")

    console.print(
        Panel.fit(grid, title="[bold blue]🏥 项目体检[/bold blue]", border_style="blue")
    )

    if r.issues:
        it = Table(title="问题（最多 5 条）", show_lines=False)
        it.add_column("级别", style="yellow", width=10)
        it.add_column("说明")
        for issue in r.issues[:5]:
            it.add_row(
                escape(str(issue.get("severity", "?"))),
                escape(str(issue.get("message", ""))),
            )
        console.print(it)


def _print_status(r: StatusResult) -> None:
    if r.executions:
        t = Table(title=f"执行历史 [dim]({len(r.executions)} 条，展示前 10 条)[/dim]")
        t.add_column("执行ID", style="cyan")
        t.add_column("状态")
        t.add_column("项目")
        t.add_column("Sprint", justify="right")
        for e in r.executions[:10]:
            t.add_row(
                escape(str(e.get("execution_id", "?"))),
                escape(str(e.get("status", "?"))),
                escape(dict_plan_name(e)),
                f"{e.get('current_sprint', 0)}/{e.get('total_sprints', 0)}",
            )
        console.print(t)
    else:
        lines = [
            f"执行ID: [bold]{escape(r.execution_id)}[/bold]",
            f"状态: {escape(r.status)}",
            f"Sprint: {r.current_sprint}/{r.total_sprints}",
        ]
        if r.sprint_history:
            hist = "\n".join(
                f"  · {escape(str(h.get('sprint_name', '?')))} → {escape(str(h.get('status', '?')))}"
                for h in r.sprint_history[-3:]
            )
            lines.append("历史:\n" + hist)
        console.print(Panel("\n".join(lines), title="[bold]📜 执行状态[/bold]", border_style="magenta"))


def _print_rollback(r: RollbackResult) -> None:
    ok = r.success
    title = "[bold green]✅ 回滚成功[/bold green]" if ok else "[bold red]❌ 回滚失败[/bold red]"
    msg = f"回滚点: [bold]{escape(r.rollback_point)}[/bold]"
    if r.files_restored:
        msg += f"\n恢复文件: {len(r.files_restored)} 个"
    console.print(Panel(msg, title=title, border_style="green" if ok else "red"))


def _print_stop(r: StopResult) -> None:
    ok = r.cancelled
    title = "[bold green]✅ 已停止[/bold green]" if ok else "[bold red]❌ 停止失败[/bold red]"
    console.print(
        Panel(
            f"{escape(r.execution_id)}\n{escape(r.message)}",
            title=title,
            border_style="green" if ok else "red",
        )
    )


def _require_tty_for_interactive(cmd: str) -> None:
    if not sys.stdin.isatty():
        err_console.print(
            f"[red]{cmd} 需要在交互式终端（TTY）中运行；"
            f"或在脚本中直接使用子命令与参数。[/red]"
        )
        raise SystemExit(1)


# ─── CLI 入口 ───


@click.group(invoke_without_command=True)
@click.option("-p", "--project", default=".", help="项目路径")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("-v", "--verbose", is_flag=True, help="详细输出")
@click.version_option(version=_package_version(), prog_name="sprintcycle")
@click.pass_context
def cli(ctx: click.Context, project: str, fmt: str, verbose: bool) -> None:
    """SprintCycle — 意图驱动 + 敏捷 Sprint 闭环（执行计划 YAML，Scrum 对齐见文档）

    意图 → Release Plan（YAML）→ 编排执行

    \b
    快捷用法:
      sprintcycle "优化性能"              # 等同于 sprintcycle run
    """
    _ensure_rich_traceback()
    configure_sprintcycle_logging(
        stderr_level="DEBUG" if verbose else "INFO",
    )
    ctx.ensure_object(dict)
    ctx.obj["sc"] = SprintCycle(project_path=project)
    ctx.obj["fmt"] = fmt
    ctx.obj["verbose"] = verbose

    if ctx.invoked_subcommand is None:
        args = ctx.args
        if args:
            result = ctx.obj["sc"].run(intent=" ".join(args))
            _print_result(result, fmt)
        else:
            console.print(ctx.get_help())


# ─── wizard ───


@cli.command("wizard")
@click.pass_context
def wizard(ctx: click.Context) -> None:
    """交互式向导：多步选择后执行 plan / run / diagnose / status"""
    if ctx.obj["fmt"] == "json":
        raise click.UsageError("wizard 不支持 --format json（交互仅面向人类可读终端）")
    _require_tty_for_interactive("wizard")

    questionary.print("SprintCycle — 交互式向导\n", style="bold")

    action = questionary.select(
        "要执行的操作？",
        choices=[
            Choice("生成执行计划（不执行）", value="plan"),
            Choice("执行 Sprint（run）", value="run"),
            Choice("项目体检（diagnose）", value="diagnose"),
            Choice("查看执行状态 / 历史（status）", value="status"),
        ],
    ).ask()

    if action is None:
        raise SystemExit(1)

    sc: SprintCycle = ctx.obj["sc"]
    fmt = ctx.obj["fmt"]

    if action == "diagnose":
        _print_result(sc.diagnose(), fmt)
        return

    if action == "status":
        eid = questionary.text(
            "执行 ID（留空列出全部历史）:",
            default="",
        ).ask()
        if eid is None:
            raise SystemExit(1)
        eid = (eid or "").strip() or None
        _print_result(sc.status(execution_id=eid), fmt)
        return

    intent = questionary.text(
        "意图描述（自然语言）:",
        validate=lambda t: bool(str(t).strip()) or "请输入非空意图",
    ).ask()
    if intent is None:
        raise SystemExit(1)

    mode = questionary.select(
        "模式:",
        choices=["auto", "evolution", "normal", "fix", "test"],
        default="auto",
    ).ask()
    if mode is None:
        raise SystemExit(1)

    target = questionary.text("目标文件或模块（可选，直接回车跳过）:", default="").ask()
    if target is None:
        raise SystemExit(1)
    target = (target or "").strip() or None

    product = questionary.text(
        "进化模式产品英文名 -P（可选，直接回车跳过）:",
        default="",
    ).ask()
    if product is None:
        raise SystemExit(1)
    product = (product or "").strip() or None

    if not questionary.confirm("确认执行？", default=True).ask():
        console.print("[dim]已取消。[/dim]")
        return

    if action == "plan":
        _print_result(
            sc.plan(
                intent=intent.strip(),
                mode=mode,
                target=target,
                product=product,
                release_plan_path=None,
            ),
            fmt,
        )
    else:
        _print_result(
            sc.run(
                intent=intent.strip(),
                mode=mode,
                target=target,
                product=product,
                release_plan_path=None,
                release_plan_yaml=None,
                resume=False,
                execution_id=None,
                confirm_knowledge=False,
            ),
            fmt,
        )


# ─── plan ───


@cli.command()
@click.argument("intent")
@click.option("-m", "--mode", default="auto", type=click.Choice(["auto", "evolution", "normal", "fix", "test"]))
@click.option("-t", "--target", default=None, help="目标文件/模块")
@click.option(
    "-P",
    "--product",
    default=None,
    help="进化模式下的英文产品名（与意图中 product: Name 等价）；代码写入 products/<name>/",
)
@click.option(
    "--release-plan",
    "release_plan_path",
    default=None,
    help="已有执行计划 YAML 文件路径（.yaml/.yml）",
)
@click.pass_context
def plan(
    ctx: click.Context,
    intent: str,
    mode: str,
    target: Optional[str],
    product: Optional[str],
    release_plan_path: Optional[str],
) -> None:
    """生成 Sprint 执行计划（不执行）"""
    result = ctx.obj["sc"].plan(
        intent=intent,
        mode=mode,
        target=target,
        release_plan_path=release_plan_path,
        product=product,
    )
    _print_result(result, ctx.obj["fmt"])


# ─── run ───


@cli.command()
@click.argument("intent", required=False)
@click.option("-m", "--mode", default="auto", type=click.Choice(["auto", "evolution", "normal", "fix", "test"]))
@click.option("-t", "--target", default=None, help="目标文件/模块")
@click.option(
    "-P",
    "--product",
    default=None,
    help="进化模式下的英文产品名（与意图中 product: Name 等价）",
)
@click.option(
    "--release-plan",
    "release_plan_path",
    default=None,
    help="执行计划 YAML 文件路径",
)
@click.option(
    "--release-plan-yaml",
    "release_plan_yaml",
    default=None,
    help="执行计划 YAML 文本（与 plan 返回的 release_plan_yaml 同形）",
)
@click.option("--resume", is_flag=True, help="断点续跑")
@click.option("--execution-id", default=None, help="执行 ID（resume 时使用）")
@click.option(
    "--yes",
    "confirm_knowledge",
    is_flag=True,
    help="在 require_knowledge_injection_confirm 开启时确认知识注入并继续执行",
)
@click.pass_context
def run(
    ctx: click.Context,
    intent: Optional[str],
    mode: str,
    target: Optional[str],
    product: Optional[str],
    release_plan_path: Optional[str],
    release_plan_yaml: Optional[str],
    resume: bool,
    execution_id: Optional[str],
    confirm_knowledge: bool,
) -> None:
    """执行 Sprint"""
    result = ctx.obj["sc"].run(
        intent=intent,
        mode=mode,
        target=target,
        release_plan_path=release_plan_path,
        release_plan_yaml=release_plan_yaml,
        resume=resume,
        execution_id=execution_id,
        confirm_knowledge=confirm_knowledge,
        product=product,
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


# ─── execution-events（SQLite MQ 回放）───


@cli.command("execution-events")
@click.argument("execution_id")
@click.option("--limit", default=200, type=int, help="最多返回条数（上限由实现裁剪）")
@click.pass_context
def execution_events_cmd(ctx: click.Context, execution_id: str, limit: int) -> None:
    """只读：列出已持久化到 SQLite MQ 的执行事件（execution_event_backend=sqlite 时才有数据）"""
    sc: SprintCycle = ctx.obj["sc"]
    data = sc.execution_events(execution_id, limit=limit)
    if ctx.obj["fmt"] == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if not data.get("success"):
        err_console.print(f"[red]失败[/red] {escape(str(data.get('error', '')))}")
        raise SystemExit(1)
    msg = data.get("message")
    if msg:
        console.print(Panel.fit(escape(str(msg)), title="execution-events"))
    rows = data.get("data") or []
    if not rows:
        console.print("暂无事件记录（检查 execution_event_backend 与 .sprintcycle/data/exec_events.sqlite）")
        return
    t = Table(title="执行事件（时间正序）")
    t.add_column("时间", max_width=22)
    t.add_column("类型", max_width=28)
    t.add_column("摘要", max_width=48)
    for r in rows:
        if not isinstance(r, dict):
            continue
        d = r.get("data") if isinstance(r.get("data"), dict) else {}
        hint = ""
        for k in ("description", "sprint_index", "status", "message"):
            v = d.get(k)
            if v is not None and str(v):
                hint = f"{k}={str(v)[:40]}"
                break
        t.add_row(
            str(r.get("timestamp") or r.get("created_at") or "")[:20],
            str(r.get("event_type", "")),
            escape(hint or "(no data)"),
        )
    console.print(t)


# ─── import-state（JSON → SQLite）───


@cli.command("import-state")
@click.option(
    "--json-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="原 JSON StateStore 目录（含 *.json）",
)
@click.option(
    "--sqlite",
    "sqlite_db",
    type=click.Path(path_type=Path),
    required=True,
    help="目标 SQLite 数据库文件路径",
)
@click.pass_context
def import_state(ctx: click.Context, json_dir: Path, sqlite_db: Path) -> None:
    """将 JSON 执行状态导入 SQLite（与 storage.backend=sqlite 共用库）"""
    from sprintcycle.persistence.import_json_state import import_json_executions_to_sqlite

    n = import_json_executions_to_sqlite(json_dir, sqlite_db)
    console.print(
        Panel.fit(
            f"已导入 [bold green]{n}[/bold green] 条执行记录\n→ {escape(str(sqlite_db))}",
            title="[bold green]✅ import-state[/bold green]",
        )
    )


# ─── knowledge ───


@cli.group("knowledge")
def knowledge_group() -> None:
    """知识卡片检索（P1）"""


@knowledge_group.command("search")
@click.option("-q", "--query", default="", help="关键词（匹配 domain/body/outcome）")
@click.option("--tag", multiple=True, help="标签（可重复，全部匹配）")
@click.option("--limit", default=50, type=int)
@click.pass_context
def knowledge_search(ctx: click.Context, query: str, tag: tuple[str, ...], limit: int) -> None:
    """检索知识卡片"""
    data = ctx.obj["sc"].knowledge_search(query=query, tags=list(tag), limit=limit)
    if ctx.obj["fmt"] == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    cards = data.get("cards", [])[:20]
    t = Table(title=f"知识卡片 [dim]({data.get('count', 0)} 条，展示前 {len(cards)} 条)[/dim]")
    t.add_column("ID", style="dim", max_width=12)
    t.add_column("领域")
    t.add_column("摘要", max_width=72)
    for c in cards:
        cid = str(c.get("id", ""))
        cid_show = (cid[:8] + "…") if len(cid) > 9 else cid
        body = (c.get("body") or "")[:80]
        t.add_row(escape(cid_show), escape(str(c.get("domain", ""))), escape(body))
    console.print(t)


# ─── hitl（人机卡点）───


@cli.group("hitl")
def hitl_group() -> None:
    """人机卡点：待决策列表与提交决策（需 [hitl] enabled）"""


@hitl_group.command("pending")
@click.option("--execution-id", default=None, help="仅列出该执行 ID 下的待办")
@click.pass_context
def hitl_pending(ctx: click.Context, execution_id: Optional[str]) -> None:
    """列出待处理的人机卡点"""
    sc: SprintCycle = ctx.obj["sc"]
    data = asyncio.run(sc.hitl_pending(execution_id=execution_id))
    if ctx.obj["fmt"] == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    rows = data.get("data") or []
    if not rows:
        console.print(Panel.fit("暂无待处理的人机卡点", title="HITL"))
        return
    t = Table(title="待处理人机卡点")
    t.add_column("request_id", max_width=14)
    t.add_column("execution", max_width=12)
    t.add_column("gate")
    t.add_column("title", max_width=48)
    for r in rows:
        if not isinstance(r, dict):
            continue
        rid = str(r.get("request_id", ""))
        t.add_row(
            (rid[:10] + "…") if len(rid) > 11 else rid,
            str(r.get("execution_id", ""))[:10],
            str(r.get("gate", "")),
            escape(str(r.get("title", ""))[:46]),
        )
    console.print(t)


@hitl_group.command("submit")
@click.argument("request_id")
@click.option(
    "--decision",
    required=True,
    type=str,
    help="决策：approve / skip_sprint / abort_execution（或 reject→abort、skip→skip_sprint 等别名）",
)
@click.option("--note", default=None, help="备注")
@click.pass_context
def hitl_submit(ctx: click.Context, request_id: str, decision: str, note: Optional[str]) -> None:
    """提交人机卡点决策"""
    sc: SprintCycle = ctx.obj["sc"]
    data = asyncio.run(sc.hitl_submit(request_id, decision, note))
    if ctx.obj["fmt"] == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if not data.get("success"):
        err_console.print(f"[red]失败[/red] {escape(str(data.get('error', '')))}")
        raise SystemExit(1)
    console.print(Panel.fit("[green]已提交决策[/green]", title="HITL"))


@hitl_group.command("show")
@click.argument("request_id")
@click.pass_context
def hitl_show_cmd(ctx: click.Context, request_id: str) -> None:
    """按 ID 查看单条人机卡点记录（读 SQLite，不依赖 [hitl] enabled）"""
    sc: SprintCycle = ctx.obj["sc"]
    data = asyncio.run(sc.hitl_show(request_id))
    if ctx.obj["fmt"] == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if not data.get("success"):
        err_console.print(f"[red]失败[/red] {escape(str(data.get('error', '')))}")
        raise SystemExit(1)
    row = data.get("data") or {}
    if not isinstance(row, dict):
        row = {}
    lines = [
        f"[bold]request_id[/bold] {escape(str(row.get('request_id', '')))}",
        f"[bold]execution_id[/bold] {escape(str(row.get('execution_id', '')))}",
        f"[bold]gate[/bold] {escape(str(row.get('gate', '')))}",
        f"[bold]status[/bold] {escape(str(row.get('status', '')))}",
        f"[bold]decision[/bold] {escape(str(row.get('decision') or '-'))}",
        f"[bold]title[/bold] {escape(str(row.get('title', '')))}",
    ]
    console.print(Panel.fit("\n".join(lines), title="HITL 记录"))


@hitl_group.command("history")
@click.option("--execution-id", default=None)
@click.option("--limit", default=50, type=int)
@click.pass_context
def hitl_history(ctx: click.Context, execution_id: Optional[str], limit: int) -> None:
    """人机卡点历史"""
    sc: SprintCycle = ctx.obj["sc"]
    data = asyncio.run(sc.hitl_history(execution_id=execution_id, limit=limit))
    if ctx.obj["fmt"] == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    rows = data.get("data") or []
    if not rows:
        console.print("暂无记录")
        return
    t = Table(title="HITL 历史")
    t.add_column("时间", max_width=20)
    t.add_column("gate")
    t.add_column("决策")
    t.add_column("标题", max_width=40)
    for r in rows:
        if not isinstance(r, dict):
            continue
        t.add_row(
            str(r.get("created_at", ""))[:19],
            str(r.get("gate", "")),
            str(r.get("decision") or "-"),
            escape(str(r.get("title", ""))[:38]),
        )
    console.print(t)


# ─── governance（治理与质量门禁）───


@cli.group("governance")
def governance_group() -> None:
    """代码治理与质量门禁（见 docs/GOVERNANCE_ENGINEERING.md）"""


@governance_group.command("check")
@click.option(
    "--gate",
    type=click.Choice(["review", "planning", "both"]),
    default="review",
    help="执行的检查包",
)
@click.pass_context
def governance_check(ctx: click.Context, gate: str) -> None:
    """对项目根执行 Review / Planning 治理（不跑完整 Sprint）"""
    from sprintcycle.config.runtime_config import RuntimeConfig
    from sprintcycle.governance.runner import run_planning_gate_sync, run_review_gate_sync

    sc: SprintCycle = ctx.obj["sc"]
    cfg = RuntimeConfig.from_project(sc.project_path)
    planning_report = None
    review_report = None
    if gate in ("planning", "both"):
        planning_report = run_planning_gate_sync(sc.project_path, cfg)
    if gate in ("review", "both"):
        review_report = run_review_gate_sync(sc.project_path, cfg)

    block_on = (cfg.governance_block_on or "none").strip().lower()
    fail = False
    if gate in ("planning", "both") and planning_report is not None:
        if block_on == "planning_and_review" and planning_report.has_error_severity():
            fail = True
    if gate in ("review", "both") and review_report is not None:
        if block_on in ("review_only", "planning_and_review") and review_report.has_error_severity():
            fail = True

    if ctx.obj["fmt"] == "json":
        out: dict[str, Any] = {}
        if planning_report is not None:
            out["planning"] = planning_report.to_dict()
        if review_report is not None:
            out["review"] = review_report.to_dict()
        out["should_fail_ci"] = fail
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if planning_report is not None:
            console.print(Panel.fit(f"[bold]Planning[/bold] violations={len(planning_report.violations)}", title="治理"))
            for v in planning_report.violations[:15]:
                console.print(f"  [{v.severity}] {escape(v.rule_id)}: {escape(v.message[:200])}")
        if review_report is not None:
            console.print(Panel.fit(f"[bold]Review[/bold] violations={len(review_report.violations)}", title="治理"))
            for v in review_report.violations[:15]:
                console.print(f"  [{v.severity}] {escape(v.rule_id)}: {escape(v.message[:200])}")
        if fail:
            err_console.print("[red]根据 governance_block_on 配置，本次检查视为失败。[/red]")

    if fail:
        raise SystemExit(1)


@governance_group.command("model-compare")
@click.option(
    "--env1",
    multiple=True,
    default=(),
    help="第一遍 pytest 前附加的环境变量 KEY=VALUE（可重复）",
)
@click.option(
    "--env2",
    multiple=True,
    default=(),
    help="第二遍 pytest 前附加的环境变量 KEY=VALUE（可重复）",
)
@click.option(
    "--output",
    "out_path",
    type=click.Path(path_type=Path),
    default=None,
    help="写入 JSON 报告路径；默认 <report_dir>/model_compare_last.json",
)
@click.option(
    "--quick",
    is_flag=True,
    default=False,
    help="未传 pytest 参数时使用 tests/ -q --tb=no -m golden（大仓库模型对比更快）",
)
@click.argument("pytest_args", nargs=-1)
@click.pass_context
def governance_model_compare(
    ctx: click.Context,
    env1: tuple[str, ...],
    env2: tuple[str, ...],
    out_path: Optional[Path],
    quick: bool,
    pytest_args: tuple[str, ...],
) -> None:
    """同一仓库连续跑两遍 pytest（junitxml），对比失败用例集合与退出码。

    用于切换 ``LLM_MODEL`` 等环境后的回归基线对比。未传 pytest 参数时默认 ``tests/ -q --tb=no``；
    使用 ``--quick`` 时默认追加 ``-m golden``（见 ``docs/GOVERNANCE_GOLDEN.md``）。
    """
    from sprintcycle.config.runtime_config import RuntimeConfig
    from sprintcycle.governance.model_compare import run_model_compare

    sc: SprintCycle = ctx.obj["sc"]
    cfg = RuntimeConfig.from_project(sc.project_path)
    if pytest_args:
        args = list(pytest_args)
    elif quick:
        args = ["tests/", "-q", "--tb=no", "-m", "golden"]
    else:
        args = ["tests/", "-q", "--tb=no"]
    rep = run_model_compare(Path(sc.project_path), args, env1, env2)

    rel = getattr(cfg, "governance_report_dir", None) or ".sprintcycle"
    root = Path(sc.project_path).resolve()
    out_dir = root / rel if not Path(rel).is_absolute() else Path(rel)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_path or (out_dir / "model_compare_last.json")
    dest.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    diff_failures = not rep.get("failure_sets_equal", True)
    diff_exit = rep.get("exit_code_run1") != rep.get("exit_code_run2")
    fail = diff_failures or diff_exit

    if ctx.obj["fmt"] == "json":
        out = dict(rep)
        out["report_path"] = str(dest)
        out["should_fail_ci"] = fail
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        console.print(
            Panel.fit(
                f"run1 exit={rep.get('exit_code_run1')} failures={rep.get('failed_count_run1')}\n"
                f"run2 exit={rep.get('exit_code_run2')} failures={rep.get('failed_count_run2')}\n"
                f"failure_sets_equal={rep.get('failure_sets_equal')}\n"
                f"报告 → {escape(str(dest))}",
                title="[bold]model-compare[/bold]",
            )
        )
        if rep.get("failed_only_run1"):
            console.print("[yellow]仅在 run1 失败:[/yellow]", escape(str(rep["failed_only_run1"][:10])))
        if rep.get("failed_only_run2"):
            console.print("[yellow]仅在 run2 失败:[/yellow]", escape(str(rep["failed_only_run2"][:10])))

    if fail:
        err_console.print("[red]两次运行结果不一致（退出码或失败用例集合）。[/red]")
        raise SystemExit(1)


def _docker_compose_cmd(compose_file: Optional[str]) -> list[str]:
    cmd = ["docker", "compose"]
    if compose_file:
        cmd.extend(["-f", compose_file])
    return cmd


def _run_docker_compose(
    cwd: Path,
    compose_file: Optional[str],
    args: list[str],
) -> int:
    cmd = _docker_compose_cmd(compose_file) + args
    p = subprocess.run(cmd, cwd=str(cwd))
    return int(p.returncode)


# ─── product（Docker Compose 一键）───


@cli.group("product")
def product_group() -> None:
    """用户产品仓库 Docker Compose（需已安装 docker compose v2）"""


@product_group.command("docker-build")
@click.option(
    "--project-directory",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="含 compose 文件的目录；默认使用当前 -p 项目路径",
)
@click.option("--compose-file", default=None, help="compose 文件名（默认 docker compose 在目录内解析）")
@click.pass_context
def product_docker_build(ctx: click.Context, project_directory: Optional[Path], compose_file: Optional[str]) -> None:
    """在项目目录执行 docker compose build"""
    sc: SprintCycle = ctx.obj["sc"]
    cwd = Path(project_directory).resolve() if project_directory else Path(sc.project_path).resolve()
    code = _run_docker_compose(cwd, compose_file, ["build"])
    if code != 0:
        err_console.print(f"[red]docker compose build 退出码 {code}[/red]")
        raise SystemExit(code)


@product_group.command("up")
@click.option("--project-directory", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--compose-file", default=None)
@click.pass_context
def product_up(ctx: click.Context, project_directory: Optional[Path], compose_file: Optional[str]) -> None:
    """docker compose up -d"""
    sc: SprintCycle = ctx.obj["sc"]
    cwd = Path(project_directory).resolve() if project_directory else Path(sc.project_path).resolve()
    code = _run_docker_compose(cwd, compose_file, ["up", "-d"])
    if code != 0:
        err_console.print(f"[red]docker compose up 退出码 {code}[/red]")
        raise SystemExit(code)


@product_group.command("down")
@click.option("--project-directory", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--compose-file", default=None)
@click.pass_context
def product_down(ctx: click.Context, project_directory: Optional[Path], compose_file: Optional[str]) -> None:
    """docker compose down"""
    sc: SprintCycle = ctx.obj["sc"]
    cwd = Path(project_directory).resolve() if project_directory else Path(sc.project_path).resolve()
    code = _run_docker_compose(cwd, compose_file, ["down"])
    if code != 0:
        err_console.print(f"[red]docker compose down 退出码 {code}[/red]")
        raise SystemExit(code)


@product_group.command("logs")
@click.option("--project-directory", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--compose-file", default=None)
@click.option("--tail", default="100", help="docker compose logs --tail")
@click.pass_context
def product_logs(
    ctx: click.Context,
    project_directory: Optional[Path],
    compose_file: Optional[str],
    tail: str,
) -> None:
    """docker compose logs（默认 tail=100）"""
    sc: SprintCycle = ctx.obj["sc"]
    cwd = Path(project_directory).resolve() if project_directory else Path(sc.project_path).resolve()
    code = _run_docker_compose(cwd, compose_file, ["logs", "--tail", tail])
    if code != 0:
        raise SystemExit(code)


# ─── serve (MCP Server) ───


@cli.command()
@click.option("--host", default="0.0.0.0", help="MCP Server host")
@click.option("--port", default=8080, type=int, help="MCP Server port")
@click.option("--transport", "transport", type=click.Choice(["stdio", "sse"]), default="stdio", help="传输方式")
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, transport: str) -> None:
    """启动 MCP Server

    支持两种传输模式:

    \b
    stdio 模式（默认）:
        本地进程通信，适合 Claude Desktop、Cursor 等本地工具
        $ sprintcycle serve

    \b
    SSE 模式（远程 Agent 接入）:
        HTTP SSE 传输，适合扣子、OpenClaw 等远程 Agent
        $ sprintcycle serve --transport sse --host 0.0.0.0 --port 8080

        端点说明:
        - GET  /sse       → 建立 SSE 连接，接收服务端消息
        - POST /messages/ → 发送客户端消息
    """
    try:
        from sprintcycle.mcp.server import HTTP_AVAILABLE, MCP_AVAILABLE, SSE_AVAILABLE, SprintCycleMCPServer

        if not MCP_AVAILABLE:
            err_console.print("[red]MCP SDK 未安装，请执行:[/red] pip install mcp")
            sys.exit(1)

        server = SprintCycleMCPServer(project_path=ctx.obj["sc"].project_path)

        if transport == "stdio":
            err_console.print("[bold]MCP Server[/bold] 启动 [dim](stdio)[/dim]")
            asyncio.run(server.run())
        else:
            if not SSE_AVAILABLE:
                err_console.print("[red]MCP SSE 支持未安装，请执行:[/red] pip install mcp[dev]")
                sys.exit(1)
            if not HTTP_AVAILABLE:
                err_console.print("[red]HTTP 服务器未安装，请执行:[/red] pip install uvicorn starlette")
                sys.exit(1)

            err_console.print(f"[bold]MCP Server[/bold] 启动 [dim](SSE {host}:{port})[/dim]")
            err_console.print(f"   SSE 端点: [link]http://{host}:{port}/sse[/link]")
            err_console.print(f"   消息端点: [link]http://{host}:{port}/messages/[/link]")
            asyncio.run(server.run_sse(host=host, port=port))

    except ImportError as e:
        err_console.print(f"[red]MCP 模块导入失败:[/red] {escape(str(e))}")
        sys.exit(1)


def _dashboard_frontend_dir() -> Path:
    """仓库根目录下的 frontend/（可编辑安装）；wheel 安装时通常不存在。"""
    return Path(__file__).resolve().parent.parent / "frontend"


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8080, type=int, help="监听端口")
@click.option(
    "--dev",
    is_flag=True,
    help="开发模式：同启 Vite（需仓库内 frontend/ 且已 npm install），后端启用 CORS",
)
@click.pass_context
def dashboard(ctx: click.Context, host: str, port: int, dev: bool) -> None:
    """启动 Dashboard (Web UI)；`--dev` 时同时启动 Vite，浏览器打开 http://localhost:5173"""
    try:
        import uvicorn

        from sprintcycle.dashboard.server import create_app
    except ImportError as e:
        err_console.print(f"[red]依赖缺失:[/red] {escape(str(e))}")
        err_console.print("[dim]安装命令:[/dim] pip install fastapi uvicorn")
        sys.exit(1)

    frontend_dir = _dashboard_frontend_dir()
    vite_proc: Optional[subprocess.Popen] = None

    if dev:
        pkg_json = frontend_dir / "package.json"
        if not pkg_json.is_file():
            err_console.print(
                "[red]未找到 frontend/ 工程：--dev 仅适用于源码克隆目录[/red] "
                "（需包含 frontend/package.json）。"
            )
            err_console.print(
                "[dim]或用手动双终端：[/dim] `SPRINTCYCLE_ENV=development sprintcycle dashboard` + `cd frontend && npm run dev`"
            )
            sys.exit(1)
        if not (frontend_dir / "node_modules").is_dir():
            err_console.print(
                "[red]缺少 node_modules：[/red] 请先执行 [bold]cd frontend && npm install[/bold]"
            )
            sys.exit(1)

        dev_env = os.environ.copy()
        dev_env["SPRINTCYCLE_ENV"] = "development"
        dev_env["VITE_PROXY_TARGET"] = f"http://127.0.0.1:{port}"

        try:
            vite_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(frontend_dir),
                env=dev_env,
            )
        except OSError as e:
            err_console.print(f"[red]无法启动 npm run dev:[/red] {escape(str(e))}")
            sys.exit(1)

        console.print(
            f"[bold]Dashboard dev[/bold] 后端 [link]http://127.0.0.1:{port}[/link] · "
            f"前端 [link]http://localhost:5173[/link]"
        )
    else:
        console.print(f"[bold]Dashboard[/bold] 启动: [link]http://{host}:{port}[/link]")

    app = create_app(project_path=ctx.obj["sc"].project_path)
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    finally:
        if vite_proc is not None and vite_proc.poll() is None:
            vite_proc.terminate()
            try:
                vite_proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                vite_proc.kill()


# ─── init ───


@cli.command()
@click.argument("path", default=".")
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="交互式确认路径与目录结构（需 TTY）",
)
@click.pass_context
def init(ctx: click.Context, path: str, interactive: bool) -> None:
    """初始化项目"""
    if interactive:
        if ctx.obj["fmt"] == "json":
            raise click.UsageError("init --interactive 不支持 --format json")
        _require_tty_for_interactive("init --interactive")
        answered = questionary.text(
            "项目根目录路径:",
            default=str(Path(path).resolve()),
        ).ask()
        if answered is None:
            raise SystemExit(1)
        path = answered.strip() or path

    project_path = Path(path).expanduser().resolve()
    if interactive:
        if not questionary.confirm(
            f"将在 {project_path} 下创建 .sprintcycle 目录，继续？",
            default=True,
        ).ask():
            console.print("[dim]已取消。[/dim]")
            return

    project_path.mkdir(parents=True, exist_ok=True)

    state_dir = project_path / ".sprintcycle" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    log_dir = project_path / ".sprintcycle" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel.fit(
            f"状态目录: {escape(str(state_dir))}\n日志目录: {escape(str(log_dir))}",
            title="[bold green]✅ 项目初始化完成[/bold green]",
        )
    )


if __name__ == "__main__":
    cli()
