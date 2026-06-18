"""
SprintCycle CLI - 命令行入口

提供项目的命令行交互接口
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

import uvicorn


def run_server(args):
    """启动HTTP服务器"""
    uvicorn.run(
        "sprintcycle.interfaces.http.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


def run_governance_check(args):
    """运行治理检查"""
    from sprintcycle.domain.core.governance.arch_guard.cli import main as governance_main
    return governance_main(args.governance_args)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="sprintcycle",
        description="意图驱动的自我进化敏捷开发框架"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    server_parser = subparsers.add_parser("server", help="启动HTTP服务器")
    server_parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    server_parser.add_argument("--port", type=int, default=8000, help="端口号")
    server_parser.add_argument("--reload", action="store_true", help="自动重载")
    
    governance_parser = subparsers.add_parser("governance", help="治理检查")
    governance_parser.add_argument("governance_args", nargs=argparse.REMAINDER)
    
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI主入口"""
    parser = build_parser()
    args = parser.parse_args(argv)
    
    if args.command == "server":
        run_server(args)
        return 0
    elif args.command == "governance":
        return run_governance_check(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())