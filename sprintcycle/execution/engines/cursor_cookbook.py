"""
Cursor Cookbook 适配：生成本地「食谱」Markdown + 可选 Cursor Agent CLI。

1. **Cookbook（无 CLI 也可用）**  
   将任务说明、上下文摘要写入 ``<project>/.sprintcycle/cursor-cookbook/``，便于在 Cursor 中打开后复制到 Chat / Agent。

2. **Cursor Agent CLI（可选）**  
   若已安装官方 CLI（默认命令名为 ``agent``），可设置 ``SPRINTCYCLE_CURSOR_USE_CLI=1`` 并在项目目录执行 ``agent -p ...``。  
   文档: https://cursor.com/docs/cli/overview
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

COOKBOOK_REL = Path(".sprintcycle") / "cursor-cookbook"


def _agent_executable() -> str:
    return (os.environ.get("SPRINTCYCLE_CURSOR_AGENT_BIN") or "agent").strip() or "agent"


def check_cursor_agent_cli() -> bool:
    return shutil.which(_agent_executable()) is not None


def _split_agent_prefix_args() -> List[str]:
    raw = os.environ.get("SPRINTCYCLE_CURSOR_AGENT_PREFIX_ARGS", "").strip()
    if not raw:
        return []
    import shlex

    return shlex.split(raw)


def write_cookbook_recipe(
    cwd: str,
    *,
    title: str,
    body: str,
    slug: Optional[str] = None,
) -> Path:
    """
    写入一条 Cookbook 条目，返回绝对路径。

    ``slug`` 缺省时对 ``title`` 做短哈希，避免文件名冲突。
    """
    root = Path(cwd).expanduser().resolve()
    out_dir = root / COOKBOOK_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    if slug:
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug)[:80]
    else:
        h = hashlib.sha256(f"{title}:{body[:200]}".encode()).hexdigest()[:12]
        safe = f"recipe-{h}"
    path = out_dir / f"{safe}.md"
    header = f"""# {title}

> SprintCycle Cursor Cookbook — {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")} (UTC)
> 项目目录: `{root}`

---

"""
    path.write_text(header + body.strip() + "\n", encoding="utf-8")
    logger.info("Cursor Cookbook 已写入: %s", path)
    return path


def build_cookbook_body(
    task_prompt: str,
    *,
    prd_overlay_hint: str = "",
    architecture_hint: str = "",
) -> str:
    """组装 Cookbook 正文（供人工在 Cursor 中跟进）。"""
    parts = [
        "## 任务",
        "",
        task_prompt.strip(),
        "",
    ]
    if architecture_hint.strip():
        parts.extend(["## 架构上下文", "", architecture_hint.strip(), ""])
    if prd_overlay_hint.strip():
        parts.extend(["## PRD / 经验覆盖（摘录）", "", prd_overlay_hint.strip(), ""])
    parts.extend(
        [
            "## 在 Cursor 中的建议用法",
            "",
            "1. 打开本文件，将「任务」整段复制到 **Agent** 或 **Chat**（可按需附加 `@文件` 引用）。",
            "2. 若使用 **Plan** 模式，可先让模型列出变更清单再改代码。",
            "3. 完成后可将要点回写到 SprintCycle 知识库（见项目文档）。",
            "",
        ]
    )
    return "\n".join(parts)


async def run_cursor_agent_print(
    message: str,
    cwd: str,
    timeout: int = 600,
) -> Tuple[int, str, str]:
    """
    执行 ``agent -p <message>``（前缀参数可通过 ``SPRINTCYCLE_CURSOR_AGENT_PREFIX_ARGS`` 注入）。

    Returns:
        (returncode, stdout, stderr)
    """
    exe = _agent_executable()
    if shutil.which(exe) is None:
        return 127, "", f"{exe} executable not found on PATH"

    cmd: List[str] = [exe] + _split_agent_prefix_args() + ["-p", message]

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


async def run_cursor_cookbook_flow(
    *,
    cwd: str,
    title: str,
    task_prompt: str,
    prd_overlay_hint: str = "",
    architecture_hint: str = "",
    timeout: int = 600,
) -> Tuple[int, str, str]:
    """
    先写 Cookbook 文件，再按需调用 Cursor Agent CLI。

    Returns:
        (returncode, stdout, stderr) — 仅写文件且未跑 CLI 时 returncode 为 0，stdout 含文件路径说明。
    """
    body = build_cookbook_body(
        task_prompt,
        prd_overlay_hint=prd_overlay_hint,
        architecture_hint=architecture_hint,
    )
    path = write_cookbook_recipe(cwd, title=title, body=body)
    header_out = f"Cookbook: {path}\n"

    use_cli = os.environ.get("SPRINTCYCLE_CURSOR_USE_CLI", "").lower() in ("1", "true", "yes")
    if use_cli and check_cursor_agent_cli():
        rc, out, err = await run_cursor_agent_print(task_prompt, cwd=cwd, timeout=timeout)
        combined = header_out + (out or "")
        if err:
            combined += "\n" + err
        return rc, combined, err or ""

    if use_cli and not check_cursor_agent_cli():
        logger.warning("已设置 SPRINTCYCLE_CURSOR_USE_CLI 但未找到 %s，仅写入 Cookbook", _agent_executable())

    return 0, header_out + "(未执行 Cursor CLI；设置 SPRINTCYCLE_CURSOR_USE_CLI=1 并安装 agent 可自动跑一轮)\n", ""
