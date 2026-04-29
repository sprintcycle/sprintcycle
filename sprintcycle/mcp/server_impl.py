"""
SprintCycle MCP Server Implementation

MCP SDK 集成实现，封装 MCP 协议相关功能
"""
import sys
from typing import Any, Dict, List

# MCP SDK 导入 - 使用绝对导入方式，避免与 sprintcycle.mcp 包冲突
# 通过修改导入路径来确保从系统安装的 mcp 包导入
import importlib

# 确保从系统 mcp 包导入，而不是从 sprintcycle.mcp 导入
_mcp_spec = importlib.util.find_spec("mcp")
if _mcp_spec and _mcp_spec.origin and "sprintcycle" not in _mcp_spec.origin:
    # 系统 mcp 包可用，直接导入
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
else:
    # 备用方案：从系统路径手动导入
    import os
    _sys_path = [p for p in sys.path if "sprintcycle" not in p]
    _old_path = sys.path.copy()
    sys.path = _sys_path
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    finally:
        sys.path = _old_path

__all__ = ["Server", "stdio_server", "Tool", "TextContent"]
