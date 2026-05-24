"""Promotion policy gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PromotionPolicy:
    min_score: int = 70

    def evaluate(
        self,
        contract: Dict[str, Any],
        *,
        runtime: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        score = 0
        evaluation = dict(contract.get("evaluation_refs") or {})
        score_card = dict(evaluation.get("score_card") or {})
        score = int(score_card.get("total") or contract.get("completion_score") or 0)
        runtime_ok = bool((runtime or {}).get("healthy") or (runtime or {}).get("deploy_ready"))
        governance_ok = bool((governance or {}).get("approved") or (governance or {}).get("success"))
        evidence_ok = bool((evidence or {}).get("contract", {}).get("normalized"))
        reasons = []
        if score < self.min_score:
            reasons.append("insufficient_score")
        if not runtime_ok:
            reasons.append("runtime_not_healthy")
        if not governance_ok:
            reasons.append("governance_not_approved")
        if not evidence_ok:
            reasons.append("evidence_not_normalized")
        if not contract.get("validation_refs", {}).get("final_snapshot"):
            reasons.append("missing_final_snapshot")
        if not contract.get("evidence", {}).get("stages", {}).get("repair", {}).get("closed_loop"):
            reasons.append("missing_stage_history")
        passed = score >= self.min_score and runtime_ok and governance_ok and evidence_ok
        return {
            "allowed": passed,
            "passed": passed,
            "score": score,
            "reasons": reasons,
            "runtime_ok": runtime_ok,
            "governance_ok": governance_ok,
            "evidence_ok": evidence_ok,
            "min_score": self.min_score,
            "status": "promotable" if passed else "blocked",
        }
