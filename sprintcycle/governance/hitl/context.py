"""HITL 上下文构建与摘要。"""

from __future__ import annotations

from typing import Any, Dict, Optional


def build_hitl_context(*, gate: str, summary: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ctx = {"gate": gate, "summary": summary}
    if extra:
        ctx.update(extra)
    return ctx


def summarize_hitl_context(context: Dict[str, Any], max_len: int = 240) -> str:
    summary = str(context.get("summary") or context.get("reason") or context.get("gate") or "")
    if len(summary) <= max_len:
        return summary
    return summary[: max_len - 3] + "..."
