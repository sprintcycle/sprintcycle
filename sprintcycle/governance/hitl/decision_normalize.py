"""HITL 决策字符串规范化：兼容原稿/脚本常用别名，再落入正式枚举。"""

from __future__ import annotations

from typing import Optional, Tuple

_DECISION_ALIASES: dict[str, str] = {
    "reject": "abort_execution",
    "deny": "abort_execution",
    "decline": "abort_execution",
    "skip": "skip_sprint",
    "abort": "abort_execution",
    "stop": "abort_execution",
    "halt": "abort_execution",
    "pass": "approve",
    "ok": "approve",
    "yes": "approve",
    "continue": "approve",
    "modify": "modify",
    "fix": "modify",
    "patch": "modify",
    "edit": "modify",
    "request_changes": "request_changes",
    "change": "request_changes",
    "changes": "request_changes",
    "revise": "request_changes",
    "retry": "retry",
    "replay": "retry",
    "rerun": "retry",
    "resume": "resume",
}

_INTENT_MAP: dict[str, str] = {
    "approve": "continue",
    "skip_sprint": "flow_control",
    "abort_execution": "flow_control",
    "reject": "terminate",
    "request_changes": "correction",
    "modify": "correction",
    "retry": "replay",
    "resume": "continue",
}


def normalize_hitl_decision(raw: str) -> str:
    s = (raw or "").strip().lower()
    return _DECISION_ALIASES.get(s, s)


def normalize_hitl_decision_with_intent(raw: str) -> Tuple[str, str]:
    norm = normalize_hitl_decision(raw)
    return norm, _INTENT_MAP.get(norm, "unknown")


def validate_hitl_decision_for_submit(raw: str) -> Optional[str]:
    from .types import HitlDecision

    norm = normalize_hitl_decision(raw)
    try:
        HitlDecision(norm)
    except ValueError:
        return None
    return norm
