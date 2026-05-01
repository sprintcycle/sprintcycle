"""
SprintCycle MCP Module

提供 MCP (Model Context Protocol) Server 实现，
让外部 AI 工具能够通过 MCP 协议调用 SprintCycle 的能力。
"""

from sprintcycle.mcp.server import SprintCycleMCPServer

__all__ = [
    "SprintCycleMCPServer",
]
