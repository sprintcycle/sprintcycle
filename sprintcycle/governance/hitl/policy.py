"""HITL 触发策略。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import HitlGate, HitlRiskLevel


@dataclass
class HitlPolicyResult:
    should_trigger: bool
    mode: str = "confirm"
    risk_level: str = HitlRiskLevel.MEDIUM.value
    reason: str = ""
    timeout_seconds: Optional[int] = None
    recommended_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


_DEF_MODE_BY_GATE = {
    HitlGate.SPEC_CONFIRM.value: "confirm",
    HitlGate.EXECUTION_APPROVAL.value: "approval",
    HitlGate.RELEASE_APPROVAL.value: "approval",
    HitlGate.BEFORE_SPRINT.value: "approval",
    HitlGate.AFTER_SPRINT.value: "review",
    HitlGate.AFTER_TASK.value: "review",
}


def evaluate_hitl_policy(*, gate: str, context: Dict[str, Any], config: Any) -> HitlPolicyResult:
    enabled = bool(getattr(config, "hitl_enabled", False))
    gates = str(getattr(config, "hitl_gates", "") or "")
    gate_enabled = gate in {g.strip() for g in gates.split(",") if g.strip()}
    if not enabled or not gate_enabled:
        return HitlPolicyResult(should_trigger=False, reason="hitl disabled for gate", metadata={"gate": gate})

    risk_level = str(context.get("risk_level") or getattr(config, "hitl_default_risk_level", "medium")).lower()
    mode = _DEF_MODE_BY_GATE.get(gate, "confirm")
    timeout_seconds = int(getattr(config, "hitl_default_timeout_seconds", 300) or 300)

    recommended_actions = ["approve", "reject", "modify"]
    if gate == HitlGate.BEFORE_SPRINT.value:
        recommended_actions = ["approve", "reject", "skip_sprint", "abort_execution"]
    elif gate == HitlGate.AFTER_TASK.value:
        recommended_actions = ["approve", "reject", "abort_execution", "modify"]

    reason = str(context.get("hitl_reason") or context.get("summary") or "human confirmation required")
    return HitlPolicyResult(
        should_trigger=True,
        mode=mode,
        risk_level=risk_level if risk_level in {"low", "medium", "high", "critical"} else HitlRiskLevel.MEDIUM.value,
        reason=reason,
        timeout_seconds=timeout_seconds,
        recommended_actions=recommended_actions,
        metadata={"gate": gate, "context_keys": sorted(context.keys())},
    )
