"""HITL 决策字符串规范化：兼容原稿/脚本常用别名，再落入三种正式枚举。"""

from __future__ import annotations

from typing import Optional

# 原稿或口语别名 → 正式值（与 HitlDecision 一致）
_DECISION_ALIASES: dict[str, str] = {
    "reject": "abort_execution",
    "deny": "abort_execution",
    "abort": "abort_execution",
    "stop": "abort_execution",
    "halt": "abort_execution",
    "skip": "skip_sprint",
    "pass": "approve",
    "ok": "approve",
    "yes": "approve",
    "continue": "approve",
}


def normalize_hitl_decision(raw: str) -> str:
    """将用户输入规范为 ``approve`` / ``skip_sprint`` / ``abort_execution`` 之一（小写）。"""
    s = (raw or "").strip().lower()
    return _DECISION_ALIASES.get(s, s)


def validate_hitl_decision_for_submit(raw: str) -> Optional[str]:
    """
    若可提交则返回规范化后的正式取值；无法映射到三种决策时返回 ``None``。
    ``regen`` / ``need_info`` / ``modify`` 等不自动映射（避免与 Executor 语义错位）。
    """
    from .types import HitlDecision

    norm = normalize_hitl_decision(raw)
    try:
        HitlDecision(norm)
    except ValueError:
        return None
    return norm
