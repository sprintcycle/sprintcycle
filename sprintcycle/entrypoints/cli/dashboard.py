"""Dashboard Web UI 与 MCP ``serve``。"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.markup import escape

from sprintcycle.entrypoints.cli._common import console, err_console
from sprintcycle.config.runtime_config import DashboardPortDefaults


def _dashboard_frontend_dir() -> Path:
    """仓库根目录下的 frontend/（可编辑安装）；wheel 安装时通常不存在。"""
    return Path(__file__).resolve().parent.parent.parent / "frontend"


def register(cli: click.Group) -> None:
    @cli.command()
    @click.option("--host", default="0.0.0.0", help="MCP Server host")
    @click.option("--port", default=DashboardPortDefaults.default_port, type=int, help="MCP Server port")
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
            $ sprintcycle serve --transport sse --host 0.0.0.0 --port <port>

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

    @cli.command()
    @click.option("--host", default="0.0.0.0", help="监听地址")
    @click.option("--port", default=DashboardPortDefaults.default_port, type=int, help="监听端口")
    @click.option(
        "--dev",
        is_flag=True,
        help="开发模式：同启 Vite（需仓库内 frontend/ 且已 npm install），后端启用 CORS",
    )
    @click.pass_context
    def dashboard(ctx: click.Context, host: str, port: int, dev: bool) -> None:
        """启动 Dashboard (Web UI)；``--dev`` 时同启 Vite（默认前端口见 ``DashboardPortDefaults.dev_port``）。"""
        dp = DashboardPortDefaults
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
            dev_env["VITE_DEV_SERVER_PORT"] = str(dp.dev_port)

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
                f"前端 [link]http://localhost:{dp.dev_port}[/link]"
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
