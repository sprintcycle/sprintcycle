"""Promotion policy for versioned evolution.

Promotion is only allowed when the lifecycle contract contains complete,
structured evidence for runtime, governance, recovery, and evolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .lifecycle_contracts import validate_lifecycle_evidence


REQUIRED_EVIDENCE_PATHS: tuple[str, ...] = (
    "contract.normalized",
    "stages.plan",
    "stages.prepare",
    "stages.decompose",
    "stages.execute",
    "stages.observe",
    "stages.diagnose",
    "stages.repair",
    "stages.verify",
    "stages.deliver",
    "runtime.linked",
    "governance.approved",
    "promotion.evidence",
    "evolution.versioned",
)


def _path_exists(payload: Dict[str, Any], path: str) -> bool:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return bool(current)


@dataclass
class PromotionPolicy:
    min_completion_score: float = 70.0
    require_runtime_healthy: bool = True
    require_suggestion_approved: bool = True
    require_trace_evidence: bool = True
    require_repair_closed: bool = True

    def evaluate(self, lifecycle_contract: Dict[str, Any], runtime: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lifecycle_contract = dict(lifecycle_contract or {})
        evidence = dict(lifecycle_contract.get("evidence") or {})
        runtime = dict(runtime or {})
        governance = dict(governance or {})
        reasons = []

        evidence_errors = validate_lifecycle_evidence(lifecycle_contract)
        if evidence_errors:
            reasons.extend([f"evidence_invalid:{error}" for error in evidence_errors])

        contract_evidence = dict(evidence.get("contract") or {})
        stages = dict(evidence.get("stages") or {})
        runtime_evidence = dict(evidence.get("runtime") or {})
        suggestion_evidence = dict(evidence.get("suggestion") or {})
        governance_evidence = dict(evidence.get("governance") or evidence.get("governing") or {})
        promotion_evidence = dict(evidence.get("promotion") or {})
        evolution_evidence = dict(evidence.get("evolution") or {})

        completion_score = float(promotion_evidence.get("completion_score") or lifecycle_contract.get("completion_score") or 0.0)
        stage_history = list(lifecycle_contract.get("stage_history") or [])
        stage = str(lifecycle_contract.get("stage") or "")
        terminal_ok = bool(lifecycle_contract.get("is_terminal") or stage in {"promoted", "failed", "cancelled", "aborted"})
        promotable_stage = stage in {"promotion_ready", "promoted"}
        required_paths_present = all(
            bool(
                path == "contract.normalized" and contract_evidence.get("normalized")
                or path == "runtime.linked" and (runtime_evidence.get("linked") or runtime_evidence.get("healthy") or runtime.get("healthy") or runtime.get("verification", {}).get("healthy"))
                or path == "governance.approved" and bool(governance_evidence.get("approved") or governance.get("approved") or governance.get("status") == "approved")
                or path == "promotion.evidence" and bool(promotion_evidence)
                or path == "evolution.versioned" and bool(evolution_evidence.get("version_id") or evolution_evidence.get("versioned"))
                or path in {"stages.normalized", "stages.plan", "stages.prepare", "stages.decompose", "stages.execute", "stages.observe", "stages.diagnose", "stages.repair", "stages.verify", "stages.deliver"} and bool(stages.get(path.split(".")[1]))
            )
            for path in REQUIRED_EVIDENCE_PATHS
        )

        if completion_score < self.min_completion_score:
            reasons.append(f"completion_score<{self.min_completion_score}")
        if self.require_runtime_healthy and not bool(runtime_evidence.get("healthy") or runtime.get("healthy") or runtime.get("verification", {}).get("healthy")):
            reasons.append("runtime_not_healthy")
        if self.require_suggestion_approved and not bool(suggestion_evidence.get("approved") or governance_evidence.get("approved") or governance.get("approved") or governance.get("status") == "approved"):
            reasons.append("suggestion_not_approved")
        if self.require_trace_evidence and not bool(stages.get("execute", {}).get("trace") or stages.get("observe", {}).get("trace") or lifecycle_contract.get("trace", {}).get("events")):
            reasons.append("missing_trace_evidence")
        if self.require_repair_closed and bool(stages.get("repair", {}).get("open") or stages.get("repairing", {}).get("open") or not stages.get("repair", {}).get("closed_loop", True)):
            reasons.append("repair_not_closed")
        validation_refs = dict(lifecycle_contract.get("validation_refs") or {})
        if self.require_trace_evidence and not validation_refs:
            reasons.append("missing_validation_refs")
        if self.require_trace_evidence and not bool(validation_refs.get("normalized") or validation_refs.get("trace_present") or validation_refs.get("versioned_evolution")):
            reasons.append("validation_refs_incomplete")
        if self.require_trace_evidence and not bool(validation_refs.get("promotion_allowed") or lifecycle_contract.get("stage") == "promoted"):
            reasons.append("promotion_not_verified")
        if self.require_trace_evidence and not stage_history:
            reasons.append("missing_stage_history")
        if self.require_trace_evidence and not terminal_ok:
            reasons.append("not_terminal")
        if self.require_trace_evidence and not promotable_stage:
            reasons.append("not_promotion_ready")
        if self.require_trace_evidence and not required_paths_present:
            reasons.append("missing_required_evidence")

        return {
            "allowed": not reasons,
            "reasons": reasons,
            "score": completion_score,
            "checks": {
                "completion_score": completion_score,
                "runtime_healthy": bool(runtime_evidence.get("healthy") or runtime.get("healthy") or runtime.get("verification", {}).get("healthy")),
                "suggestion_approved": bool(suggestion_evidence.get("approved") or governance_evidence.get("approved") or governance.get("approved") or governance.get("status") == "approved"),
                "trace_evidence": bool(stages.get("execute", {}).get("trace") or stages.get("observe", {}).get("trace") or lifecycle_contract.get("trace", {}).get("events")),
                "repair_closed": not bool(stages.get("repair", {}).get("open") or stages.get("repairing", {}).get("open")),
                "validation_refs": bool(validation_refs),
                "stage_history": bool(stage_history),
                "terminal_ok": terminal_ok,
                "promotion_ready_stage": promotable_stage,
                "required_evidence": required_paths_present,
            },
        }


__all__ = ["PromotionPolicy"]
