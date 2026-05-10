"""人机卡点（HITL）与 Docker Compose ``product`` 子命令。"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from sprintcycle.api import SprintCycle
from sprintcycle.entrypoints.cli._common import console, err_console


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


def register(cli: click.Group) -> None:
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
