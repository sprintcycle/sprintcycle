"""
SprintCycle MCP Server

通过 Model Context Protocol 暴露 SprintCycle 的 6 大核心操作，
让 AI 工具（Claude Desktop, Cursor, 扣子, OpenClaw）能直接调用。

所有逻辑委托给 SprintCycle API，本文件只做参数适配和 JSON 输出。

工具列表:
- sprintcycle_plan:     生成计划（不执行）
- sprintcycle_run:      执行（一键到底）
- sprintcycle_diagnose: 项目体检
- sprintcycle_status:   查状态/历史
- sprintcycle_rollback: 回滚
- sprintcycle_stop:     停止执行

传输模式:
- stdio: 标准输入输出（默认，本地使用）
- sse:   Server-Sent Events（远程 Agent 接入）
"""

from __future__ import annotations

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# MCP SDK imports - graceful fallback if not installed
MCP_AVAILABLE = False
stdio_server: Any = None

# SSE imports - graceful fallback if dependencies not installed
SSE_AVAILABLE = False
SseServerTransport: Any = None

if TYPE_CHECKING:
    from mcp.server import Server
    from mcp.types import Tool, TextContent

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent

    MCP_AVAILABLE = True
    SSE_AVAILABLE = True
except ImportError:
    Server = Any  # type: ignore[misc,assignment]
    Tool = Any  # type: ignore[misc,assignment]
    TextContent = Any  # type: ignore[misc,assignment]

# Optional HTTP server for SSE mode
try:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    HTTP_AVAILABLE = True
except ImportError:
    uvicorn = None  # type: ignore[assignment]
    Starlette = None  # type: ignore[misc,assignment]
    Route = None  # type: ignore[misc,assignment]
    Mount = None  # type: ignore[misc,assignment]
    Middleware = None  # type: ignore[misc,assignment]
    CORSMiddleware = None  # type: ignore[misc,assignment]
    HTTP_AVAILABLE = False

from sprintcycle.api import SprintCycle

logger = logging.getLogger(__name__)



def _text_response(text: str) -> List[Any]:
    """Create a TextContent response list - consolidates type: ignore to one place."""
    return [TextContent(type="text", text=text)]  # type: ignore[call-arg]

class SprintCycleMCPServer:
    """
    SprintCycle MCP Server 实现

    通过 MCP 协议暴露 SprintCycle API 的 6 大操作。
    所有逻辑委托给 SprintCycle API，本类只做参数映射 + JSON 序列化。
    """

    def __init__(self, project_path: str = "."):
        self.sc = SprintCycle(project_path=project_path)
        self._server: Optional[Server] = None

        if MCP_AVAILABLE:
            self._server = Server("sprintcycle")  # type: ignore[arg-type]
            self._register_tools()
        else:
            logger.warning(
                "MCP SDK not installed. Install with: pip install mcp"
            )

    def _register_tools(self) -> None:
        """注册 6 个 MCP 工具"""
        if self._server is None:
            return

        @self._server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="sprintcycle_plan",
                    description="根据用户意图生成 Sprint 执行计划（不执行）。返回 prd_yaml，用户确认后可传给 sprintcycle_run 执行。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string", "description": "用户意图描述"},
                            "mode": {"type": "string", "enum": ["auto", "evolution", "normal", "fix", "test"], "description": "执行模式"},
                            "target": {"type": "string", "description": "目标文件/模块"},
                            "prd_path": {"type": "string", "description": "已有 PRD 文件路径"},
                        },
                        "required": ["intent"],
                    },
                ),
                Tool(
                    name="sprintcycle_run",
                    description="执行 Sprint。支持自然语言意图、PRD YAML、PRD 文件路径三种输入。支持断点续跑。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string", "description": "用户意图描述"},
                            "prd_yaml": {"type": "string", "description": "PRD YAML 内容（来自 plan 结果）"},
                            "prd_path": {"type": "string", "description": "PRD 文件路径"},
                            "mode": {"type": "string", "enum": ["auto", "evolution", "normal", "fix", "test"], "description": "执行模式"},
                            "target": {"type": "string", "description": "目标文件/模块"},
                            "execution_id": {"type": "string", "description": "断点续跑的执渡 ID"},
                            "resume": {"type": "boolean", "description": "是否断点续跑", "default": False},
                        },
                    },
                ),
                Tool(
                    name="sprintcycle_diagnose",
                    description="诊断项目健康状态：覆盖率、复杂度、代码气味、类型安全等。",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="sprintcycle_status",
                    description="查询执行状态。传 execution_id 查单条，不传查所有记录。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {"type": "string", "description": "执行 ID（可选，不传则返回列表）"},
                        },
                    },
                ),
                Tool(
                    name="sprintcycle_rollback",
                    description="回滚到指定执行前的状态。代码和配置恢复原样。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {"type": "string", "description": "要回滚的执行 ID"},
                        },
                        "required": ["execution_id"],
                    },
                ),
                Tool(
                    name="sprintcycle_stop",
                    description="停止正在执行的 Sprint。在下一个任务边界安全终止。",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {"type": "string", "description": "要停止的执行 ID"},
                        },
                        "required": ["execution_id"],
                    },
                ),
            ]

        @self._server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            handler = {
                "sprintcycle_plan": self._handle_plan,
                "sprintcycle_run": self._handle_run,
                "sprintcycle_diagnose": self._handle_diagnose,
                "sprintcycle_status": self._handle_status,
                "sprintcycle_rollback": self._handle_rollback,
                "sprintcycle_stop": self._handle_stop,
            }.get(name)

            if handler is None:
                return _text_response(f"未知工具: {name}")

            try:
                return await handler(arguments)
            except Exception as e:
                return _text_response(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))

    # ─── 6 个 handler ───

    async def _handle_plan(self, args: Dict[str, Any]) -> List[TextContent]:
        result = self.sc.plan(
            intent=args["intent"],
            mode=args.get("mode", "auto"),
            target=args.get("target"),
            prd_path=args.get("prd_path"),
        )
        return _text_response(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    async def _handle_run(self, args: Dict[str, Any]) -> List[TextContent]:
        result = self.sc.run(
            intent=args.get("intent"),
            mode=args.get("mode", "auto"),
            target=args.get("target"),
            prd_yaml=args.get("prd_yaml"),
            prd_path=args.get("prd_path"),
            execution_id=args.get("execution_id"),
            resume=args.get("resume", False),
        )
        return _text_response(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    async def _handle_diagnose(self, args: Dict[str, Any]) -> List[TextContent]:
        result = self.sc.diagnose()
        return _text_response(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    async def _handle_status(self, args: Dict[str, Any]) -> List[TextContent]:
        result = self.sc.status(execution_id=args.get("execution_id"))
        return _text_response(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    async def _handle_rollback(self, args: Dict[str, Any]) -> List[TextContent]:
        result = self.sc.rollback(execution_id=args["execution_id"])
        return _text_response(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    async def _handle_stop(self, args: Dict[str, Any]) -> List[TextContent]:
        result = self.sc.stop(execution_id=args["execution_id"])
        return _text_response(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    # ─── Server 生命周期 ───

    async def run(self) -> None:
        """启动 MCP Server（stdio 模式）"""
        if not MCP_AVAILABLE or self._server is None:
            raise RuntimeError(
                "MCP SDK is not installed. Cannot start MCP Server. "
                "Install with: pip install mcp"
            )

        async with stdio_server() as (read_stream, write_stream):
            await self._server.run(
                read_stream,
                write_stream,
                self._server.create_initialization_options(),
            )

    async def run_sse(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """
        启动 MCP Server（SSE 模式）

        通过 HTTP SSE 端点暴露 MCP 协议，支持远程 Agent 接入。
        端点:
        - GET /sse  - 建立 SSE 连接，接收服务端消息
        - POST /messages - 发送客户端消息

        Args:
            host: 监听地址
            port: 监听端口
        """
        if not MCP_AVAILABLE or not SSE_AVAILABLE:
            raise RuntimeError(
                "MCP SDK with SSE support is not installed. "
                "Install with: pip install mcp[dev]"
            )

        if not HTTP_AVAILABLE:
            raise RuntimeError(
                "HTTP dependencies are not installed. "
                "Install with: pip install uvicorn starlette"
            )

        if self._server is None:
            raise RuntimeError("MCP Server not initialized")

        # Create SSE transport
        sse_transport = SseServerTransport("/messages/")

        # Reference to server for type checking
        server = self._server

        async def sse_handler(scope: Any, receive: Any, send: Any) -> None:
            """Handle incoming SSE connections"""
            async with sse_transport.connect_sse(scope, receive, send) as streams:
                await server.run(  # type: ignore[union-attr]
                    streams[0],
                    streams[1],
                    server.create_initialization_options(),  # type: ignore[union-attr]
                )

        # Create Starlette application with CORS
        app = Starlette(
            debug=True,
            routes=[
                Route("/sse", sse_handler),
                Route("/messages/", sse_transport.handle_post_message),
            ],
            middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_methods=["*"],
                    allow_headers=["*"],
                ),
            ],
        )

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
        )
        server_instance = uvicorn.Server(config)

        logger.info(f"MCP SSE Server starting on {host}:{port}")
        logger.info(f"SSE endpoint: http://{host}:{port}/sse")
        logger.info(f"Messages endpoint: http://{host}:{port}/messages/")

        await server_instance.serve()

    def is_available(self) -> bool:
        """检查 MCP Server 是否可用"""
        return MCP_AVAILABLE

    def is_sse_available(self) -> bool:
        """检查 SSE 模式是否可用"""
        return MCP_AVAILABLE and SSE_AVAILABLE and HTTP_AVAILABLE


def main() -> None:
    """MCP Server 入口点"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    transport = sys.argv[2] if len(sys.argv) > 2 else "stdio"

    if not MCP_AVAILABLE:
        print("Error: MCP SDK is not installed.", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = SprintCycleMCPServer(project_path=project_path)

    if transport == "sse":
        host = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
        port = int(sys.argv[4]) if len(sys.argv) > 4 else 8080
        asyncio.run(server.run_sse(host=host, port=port))
    else:
        asyncio.run(server.run())


if __name__ == "__main__":
    main()
