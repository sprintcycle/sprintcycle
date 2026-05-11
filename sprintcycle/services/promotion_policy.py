"""Promotion policy for versioned evolution.

Promotion is only allowed when evidence, runtime health, and governance are
all sufficiently complete.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PromotionPolicy:
    min_completion_score: float = 70.0
    require_runtime_healthy: bool = True
    require_suggestion_approved: bool = True
    require_trace_evidence: bool = True
    require_repair_closed: bool = True

    def evaluate(self, lifecycle_contract: Dict[str, Any], runtime: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lifecycle_contract = dict(lifecycle_contract or {})
        runtime = dict(runtime or {})
        governance = dict(governance or {})
        health = dict(lifecycle_contract.get("health") or {})
        repair = dict(lifecycle_contract.get("repair") or {})
        trace = dict(lifecycle_contract.get("trace") or {})
        diagnostics = dict(lifecycle_contract.get("diagnostics") or {})
        suggestion = dict(lifecycle_contract.get("suggestion") or {})
        reasons = []

        completion_score = float(lifecycle_contract.get("completion_score") or health.get("completion_score") or 0.0)
        if completion_score < self.min_completion_score:
            reasons.append(f"completion_score<{self.min_completion_score}")
        if self.require_runtime_healthy and not bool(runtime.get("healthy") or runtime.get("verification", {}).get("healthy")):
            reasons.append("runtime_not_healthy")
        if self.require_suggestion_approved and not bool(suggestion.get("approved") or governance.get("approved") or governance.get("status") == "approved"):
            reasons.append("suggestion_not_approved")
        if self.require_trace_evidence and not bool(trace.get("events") or diagnostics.get("event_count", 0) > 0):
            reasons.append("missing_trace_evidence")
        if self.require_repair_closed and bool(repair.get("ready") is False and diagnostics.get("repair_ready")):
            reasons.append("repair_not_closed")
        if not lifecycle_contract.get("validation_refs") and self.require_trace_evidence:
            reasons.append("missing_validation_refs")

        return {
            "allowed": not reasons,
            "reasons": reasons,
            "score": completion_score,
            "checks": {
                "completion_score": completion_score,
                "runtime_healthy": bool(runtime.get("healthy") or runtime.get("verification", {}).get("healthy")),
                "suggestion_approved": bool(suggestion.get("approved") or governance.get("approved") or governance.get("status") == "approved"),
                "trace_evidence": bool(trace.get("events") or diagnostics.get("event_count", 0) > 0),
                "repair_closed": not bool(repair.get("ready") is False and diagnostics.get("repair_ready")),
                "validation_refs": bool(lifecycle_contract.get("validation_refs")),
            },
        }


__all__ = ["PromotionPolicy"]
