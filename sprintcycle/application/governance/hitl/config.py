"""HITL 配置适配。"""

from __future__ import annotations

from typing import Any

from .types import HitlGate, hitl_gate_enabled, parse_hitl_gates


def is_hitl_enabled(config: Any, gate: str) -> bool:
    try:
        return hitl_gate_enabled(config, HitlGate(gate))
    except Exception:
        return False


def get_hitl_timeout_seconds(config: Any) -> int:
    return int(getattr(config, "hitl_default_timeout_seconds", 300) or 300)


def get_hitl_timeout_behavior(config: Any) -> str:
    return str(getattr(config, "hitl_timeout_behavior", "approve") or "approve")


def get_hitl_gates(config: Any):
    return parse_hitl_gates(getattr(config, "hitl_gates", "") or "")
