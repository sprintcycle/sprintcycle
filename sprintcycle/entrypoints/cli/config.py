"""项目初始化等配置向子命令。"""

from __future__ import annotations

from pathlib import Path

import click
import questionary
from rich.markup import escape
from rich.panel import Panel

from sprintcycle.entrypoints.cli._common import _require_tty_for_interactive, console


def register(cli: click.Group) -> None:
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
