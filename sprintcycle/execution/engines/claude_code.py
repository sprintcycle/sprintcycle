"""
Claude Code CLI 适配（非交互 ``-p`` / ``--print``）。

需本机已安装 Anthropic ``claude`` 并在 PATH；或通过环境变量指定可执行文件。
文档: https://code.claude.com/docs/en/headless
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def _claude_executable() -> str:
    return (os.environ.get("SPRINTCYCLE_CLAUDE_BIN") or "claude").strip() or "claude"


def check_claude_code_cli() -> bool:
    return shutil.which(_claude_executable()) is not None


def _split_extra_args() -> List[str]:
    raw = os.environ.get("SPRINTCYCLE_CLAUDE_EXTRA_ARGS", "").strip()
    if not raw:
        return []
    import shlex

    return shlex.split(raw)


async def run_claude_print_message(
    message: str,
    cwd: str,
    timeout: int = 600,
    output_format: str = "text",
) -> Tuple[int, str, str]:
    """
    在 ``cwd`` 下执行 ``claude -p <message>``（及可选 ``--output-format``）。

    Returns:
        (returncode, stdout, stderr)
    """
    exe = _claude_executable()
    if shutil.which(exe) is None:
        return 127, "", f"{exe} executable not found on PATH"

    cmd: List[str] = [exe, "-p", message, "--output-format", output_format]
    if os.environ.get("SPRINTCYCLE_CLAUDE_BARE", "").lower() in ("1", "true", "yes"):
        cmd.append("--bare")
    cmd.extend(_split_extra_args())

    def _run() -> Tuple[int, str, str]:
        import subprocess

        p = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.returncode, p.stdout or "", p.stderr or ""

    return await asyncio.to_thread(_run)
