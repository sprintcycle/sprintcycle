"""SprintCycle MCP 模块测试"""
import pytest
from unittest.mock import MagicMock, patch
import sys


def test_mcp_server_import():
    """测试 MCP 模块导入"""
    from sprintcycle.mcp import Server, stdio_server, Tool, TextContent
    assert Server is not None
    assert stdio_server is not None
    assert Tool is not None
    assert TextContent is not None


def test_mcp_init_exports():
    """测试 __init__.py 导出"""
    from sprintcycle.mcp import __all__
    expected = ["Server", "stdio_server", "Tool", "TextContent"]
    for item in expected:
        assert item in __all__


def test_mcp_server_impl_types():
    """测试 server_impl.py 中的类型定义"""
    from sprintcycle.mcp.server_impl import (
        __all__ as impl_all,
        Server, stdio_server, Tool, TextContent
    )
    assert isinstance(impl_all, list)
    assert len(impl_all) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
