"""
SprintCycle MCP Server

通过 Model Context Protocol 暴露 SprintCycle 的核心能力，
让 AI 工具（Claude Desktop, Cursor 等）能直接调用。

工具列表:
- sprintcycle_plan: 从意图或PRD生成Sprint计划
- sprintcycle_execute: 执行Sprint
- sprintcycle_diagnose: 诊断项目状态
- sprintcycle_status: 查询执行状态
- sprintcycle_rollback: 回滚到之前状态
"""

from __future__ import annotations

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# MCP SDK imports - graceful fallback if not installed
MCP_AVAILABLE = False
stdio_server: Any = None

if TYPE_CHECKING:
    from mcp.server import Server
    from mcp.types import Tool, TextContent

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    MCP_AVAILABLE = True
except ImportError:
    # Stub for type checking
    Server = Any  # type: ignore[misc,assignment]
    Tool = Any  # type: ignore[misc,assignment]
    TextContent = Any  # type: ignore[misc,assignment]

from sprintcycle.intent.parser import IntentParser
from sprintcycle.prd.generator import IntentPRDGenerator
from sprintcycle.config.runtime_config import RuntimeConfig
from sprintcycle.diagnostic.provider import ProjectDiagnostic

logger = logging.getLogger(__name__)


class SprintCycleMCPServer:
    """
    SprintCycle MCP Server 实现

    通过 MCP 协议暴露 SprintCycle 的核心功能，
    支持 Claude Desktop、Cursor 等 AI 工具集成。
    """

    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.config = RuntimeConfig()
        self._server: Optional[Server] = None

        if MCP_AVAILABLE:
            self._server = Server("sprintcycle")  # type: ignore[arg-type]
            self._register_tools()
        else:
            logger.warning(
                "MCP SDK not installed. MCP Server functionality will be limited. "
                "Install with: pip install mcp"
            )

    def _register_tools(self) -> None:
        """注册所有 MCP 工具"""
        if self._server is None:
            return

        @self._server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="sprintcycle_plan",
                    description="从用户意图或PRD文件生成Sprint执行计划",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "intent": {
                                "type": "string",
                                "description": "用户意图描述"
                            },
                            "prd_path": {
                                "type": "string",
                                "description": "PRD YAML文件路径（可选）"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "项目路径"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["auto", "evolution", "normal", "fix"],
                                "description": "执行模式"
                            },
                        },
                        "required": ["intent"],
                    },
                ),
                Tool(
                    name="sprintcycle_execute",
                    description="执行Sprint计划",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "项目路径"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["auto", "evolution", "normal", "fix"],
                                "description": "执行模式"
                            },
                            "max_concurrent": {
                                "type": "integer",
                                "description": "最大并发数",
                                "default": 3
                            },
                        },
                    },
                ),
                Tool(
                    name="sprintcycle_diagnose",
                    description="诊断项目状态（覆盖率、复杂度、类型安全等）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "项目路径"
                            },
                        },
                    },
                ),
                Tool(
                    name="sprintcycle_status",
                    description="查询Sprint执行状态",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "项目路径"
                            },
                        },
                    },
                ),
                Tool(
                    name="sprintcycle_rollback",
                    description="回滚到之前的执行状态",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "项目路径"
                            },
                        },
                    },
                ),
            ]

        @self._server.call_tool()
        async def call_tool(
            name: str,
            arguments: Dict[str, Any]
        ) -> List[TextContent]:
            if name == "sprintcycle_plan":
                return await self._handle_plan(arguments)
            elif name == "sprintcycle_execute":
                return await self._handle_execute(arguments)
            elif name == "sprintcycle_diagnose":
                return await self._handle_diagnose(arguments)
            elif name == "sprintcycle_status":
                return await self._handle_status(arguments)
            elif name == "sprintcycle_rollback":
                return await self._handle_rollback(arguments)
            else:
                return [TextContent(type="text", text=f"未知工具: {name}")]  # type: ignore[call-arg]

    async def _handle_plan(self, args: Dict[str, Any]) -> List[TextContent]:
        """处理 sprintcycle_plan 请求"""
        intent = args.get("intent", "")
        project_path = args.get("project_path", self.project_path)
        mode = args.get("mode", "auto")

        if intent:
            parser = IntentParser()
            parsed = parser.parse(intent)
            generator = IntentPRDGenerator()
            prd = generator.generate(parsed)

            # 提取 sprints 信息
            sprints_data: List[Dict[str, Any]] = []
            if hasattr(prd, 'sprints') and prd.sprints:
                for s in prd.sprints:
                    tasks_list: List[str] = []
                    if hasattr(s, 'tasks') and s.tasks:
                        for t in s.tasks:
                            tasks_list.append(t.task if hasattr(t, 'task') else str(t))
                    sprints_data.append({
                        "name": s.name,
                        "tasks": tasks_list
                    })

            result = {
                "status": "success",
                "prd_name": prd.project.name if hasattr(prd, 'project') else "generated",
                "mode": mode,
                "sprints": sprints_data,
            }
        else:
            result = {
                "status": "error",
                "message": "请提供 intent 或 prd_path"
            }

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]  # type: ignore[call-arg]

    async def _handle_execute(self, args: Dict[str, Any]) -> List[TextContent]:
        """处理 sprintcycle_execute 请求"""
        project_path = args.get("project_path", self.project_path)
        mode = args.get("mode", "normal")
        max_concurrent = args.get("max_concurrent", 3)

        from sprintcycle.scheduler.dispatcher import TaskDispatcher

        dispatcher = TaskDispatcher(config=self.config)

        result = {
            "status": "success",
            "message": f"执行引擎已初始化 (mode={mode}, max_concurrent={max_concurrent})",
            "project_path": project_path,
        }

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]  # type: ignore[call-arg]

    async def _handle_diagnose(self, args: Dict[str, Any]) -> List[TextContent]:
        """处理 sprintcycle_diagnose 请求"""
        project_path = args.get("project_path", self.project_path)

        provider = ProjectDiagnostic(project_path=project_path)
        report = provider.diagnose()

        # 将报告转换为可序列化的格式
        if hasattr(report, 'to_dict'):
            report_data = report.to_dict()
        elif hasattr(report, '__dict__'):
            report_data = {
                k: v for k, v in report.__dict__.items()
                if not k.startswith('_')
            }
        else:
            report_data = {"report": str(report)}

        result = {
            "status": "success",
            "project_path": project_path,
            "report": report_data,
        }

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]  # type: ignore[call-arg]

    async def _handle_status(self, args: Dict[str, Any]) -> List[TextContent]:
        """处理 sprintcycle_status 请求"""
        project_path = args.get("project_path", self.project_path)

        # 查询状态目录
        from pathlib import Path
        state_dir = Path(project_path) / ".sprintcycle" / "state"

        status_info = {
            "status": "success",
            "project_path": project_path,
            "state_dir_exists": state_dir.exists(),
            "state_dir": str(state_dir),
        }

        return [TextContent(type="text", text=json.dumps(status_info, ensure_ascii=False, indent=2))]  # type: ignore[call-arg]

    async def _handle_rollback(self, args: Dict[str, Any]) -> List[TextContent]:
        """处理 sprintcycle_rollback 请求"""
        project_path = args.get("project_path", self.project_path)

        from sprintcycle.execution.rollback import RollbackManager

        manager = RollbackManager()

        result = {
            "status": "success",
            "message": "回滚管理器已初始化",
            "project_path": project_path,
        }

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]  # type: ignore[call-arg]

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
                self._server.create_initialization_options()
            )

    def is_available(self) -> bool:
        """检查 MCP Server 是否可用"""
        return MCP_AVAILABLE


def main() -> None:
    """MCP Server 入口点"""
    import sys

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."

    if not MCP_AVAILABLE:
        print("Error: MCP SDK is not installed.", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = SprintCycleMCPServer(project_path=project_path)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
