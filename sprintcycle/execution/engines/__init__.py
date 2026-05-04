"""可插拔编码引擎（Aider / LiteLLM 直调 等）。"""

from .aider import check_aider_cli, run_aider_message
from .claude_code import check_claude_code_cli, run_claude_print_message
from .cursor_cookbook import (
    build_cookbook_body,
    check_cursor_agent_cli,
    run_cursor_agent_print,
    run_cursor_cookbook_flow,
    write_cookbook_recipe,
)

__all__ = [
    "check_aider_cli",
    "run_aider_message",
    "check_claude_code_cli",
    "run_claude_print_message",
    "build_cookbook_body",
    "check_cursor_agent_cli",
    "run_cursor_agent_print",
    "run_cursor_cookbook_flow",
    "write_cookbook_recipe",
]
