"""HITL 决策字符串规范化：兼容原稿/脚本常用别名，再落入正式枚举。"""

from __future__ import annotations

from typing import Optional

_DECISION_ALIASES: dict[str, str] = {
    "reject": "reject",
    "deny": "reject",
    "decline": "reject",
    "skip": "skip_sprint",
    "abort": "abort_execution",
    "stop": "abort_execution",
    "halt": "abort_execution",
    "pass": "approve",
    "ok": "approve",
    "yes": "approve",
    "continue": "approve",
    "modify": "request_changes",
    "change": "request_changes",
    "request_changes": "request_changes",
}


def normalize_hitl_decision(raw: str) -> str:
    s = (raw or "").strip().lower()
    return _DECISION_ALIASES.get(s, s)


def validate_hitl_decision_for_submit(raw: str) -> Optional[str]:
    from .types import HitlDecision

    norm = normalize_hitl_decision(raw)
    try:
        HitlDecision(norm)
    except ValueError:
        return None
    return norm
