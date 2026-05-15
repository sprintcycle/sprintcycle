"""Evaluator agent and sprint contract primitives.

This module introduces a minimal independent evaluator boundary that can score
execution evidence, produce an explainable conclusion, and write the result
back into a structured sprint contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class SprintScoreCard:
    functionality: int = 0
    structure: int = 0
    evidence: int = 0
    delivery: int = 0
    total: int = 0
    passed: bool = False
    reason: str = ""
    missing_evidence: List[str] = field(default_factory=list)
    weights: Dict[str, int] = field(default_factory=lambda: {
        "functionality": 30,
        "structure": 20,
        "evidence": 30,
        "delivery": 20,
    })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SprintContractRecord:
    execution_id: str
    task_id: str
    project_path: str
    goal: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    score_card: SprintScoreCard = field(default_factory=SprintScoreCard)
    evidence: Dict[str, Any] = field(default_factory=dict)
    verdict: str = "pending"
    evaluator_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["score_card"] = self.score_card.to_dict()
        return data


class EvaluatorAgent:
    """Independent scorer for Sprint contracts.

    The agent only evaluates and explains. It does not mutate runtime state or
    make deployment decisions.
    """

    def _score_functionality(self, payload: Dict[str, Any]) -> int:
        score = 0
        if payload.get("goal"):
            score += 50
        if payload.get("acceptance_criteria"):
            score += 50
        return score

    def _score_structure(self, evidence: Dict[str, Any]) -> int:
        stages = dict(evidence.get("stages") or {})
        contract_section = dict(evidence.get("contract") or {})
        score = 0
        if contract_section.get("normalized"):
            score += 25
        for key in ("plan", "prepare", "decompose"):
            if stages.get(key):
                score += 25
        return score

    def _score_evidence(self, evidence: Dict[str, Any]) -> tuple[int, List[str]]:
        stages = dict(evidence.get("stages") or {})
        runtime_section = dict(evidence.get("runtime") or {})
        promotion_section = dict(evidence.get("promotion") or {})
        score = 0
        missing: List[str] = []
        for key in ("execute", "observe", "diagnose", "repair", "verify"):
            if stages.get(key):
                score += 20
            else:
                missing.append(key)
        if runtime_section:
            score += 10
        if promotion_section:
            score += 10
        return score, missing

    def _score_delivery(self, evidence: Dict[str, Any]) -> int:
        runtime_section = dict(evidence.get("runtime") or {})
        promotion_section = dict(evidence.get("promotion") or {})
        score = 0
        if runtime_section.get("linked"):
            score += 35
        if runtime_section.get("healthy"):
            score += 35
        if promotion_section.get("evidence"):
            score += 30
        return score

    def evaluate(self, contract: Dict[str, Any], evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = dict(contract or {})
        merged_evidence = dict(payload.get("evidence") or {})
        if evidence:
            merged_evidence.update(evidence)

        functionality = self._score_functionality(payload)
        structure = self._score_structure(merged_evidence)
        evidence_score, missing = self._score_evidence(merged_evidence)
        delivery = self._score_delivery(merged_evidence)

        weighted_total = round(
            functionality * 0.30 + structure * 0.20 + evidence_score * 0.30 + delivery * 0.20
        )
        passed = weighted_total >= 70 and not missing
        verdict = "passed" if passed else ("needs_repair" if missing else "blocked")
        reason = "all gates satisfied" if passed else ("missing evidence: " + ", ".join(missing) if missing else "score below threshold")

        score_card = SprintScoreCard(
            functionality=min(functionality, 100),
            structure=min(structure, 100),
            evidence=min(evidence_score, 100),
            delivery=min(delivery, 100),
            total=min(weighted_total, 100),
            passed=passed,
            reason=reason,
            missing_evidence=missing,
        )
        record = SprintContractRecord(
            execution_id=str(payload.get("execution_id") or ""),
            task_id=str(payload.get("task_id") or ""),
            project_path=str(payload.get("project_path") or ""),
            goal=str(payload.get("goal") or payload.get("intent") or ""),
            acceptance_criteria=list(payload.get("acceptance_criteria") or []),
            score_card=score_card,
            evidence=merged_evidence,
            verdict=verdict,
            evaluator_notes=[reason],
        )
        return {
            "success": True,
            "data": {
                "score_card": score_card.to_dict(),
                "contract": record.to_dict(),
                "verdict": verdict,
                "reason": reason,
                "weights": score_card.weights,
            },
        }
