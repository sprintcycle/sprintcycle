"""CLI 共享：控制台、版本号、富文本 result 渲染。"""

from __future__ import annotations

import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import click
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install as install_rich_traceback

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


__all__ = [
    "console",
    "err_console",
    "_ensure_rich_traceback",
    "_package_version",
    "_print_result",
    "_require_tty_for_interactive",
]
