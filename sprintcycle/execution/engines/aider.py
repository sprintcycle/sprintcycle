"""
Aider CLI 最小集成：非交互单轮消息。

需本机已安装 ``aider`` 并在 PATH 中。未安装时由调用方回退到 LiteLLM 直调。
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def check_aider_cli() -> bool:
    return shutil.which("aider") is not None


async def run_aider_message(
    message: str,
    cwd: str,
    timeout: int = 600,
    model: Optional[str] = None,
) -> Tuple[int, str, str]:
    """
    在 ``cwd`` 下执行 ``aider --yes -m <message>``。

    Returns:
        (returncode, stdout, stderr)
    """
    if not check_aider_cli():
        return 127, "", "aider executable not found on PATH"

    cmd = ["aider", "--yes", "-m", message]
    if model:
        cmd.extend(["--model", model])

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
