"""Fitness evaluator.

This module belongs to the fitness / evaluation layer. It should only score and
recommend; it must not mutate state, render UI, or execute governance decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from sprintcycle.application.services.evaluator_agent import EvaluatorAgent


@dataclass
class FitnessEvaluator:
    def __post_init__(self) -> None:
        self._agent = EvaluatorAgent()

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        events: List[Dict[str, Any]] = list(payload.get("events") or [])
        executions: List[Dict[str, Any]] = list(payload.get("executions") or [])
        suggestions: List[Dict[str, Any]] = list(payload.get("suggestions") or [])
        runtimes: List[Dict[str, Any]] = list(payload.get("runtimes") or [])
        contract = dict(payload.get("contract") or {})

        total_events = len(events)
        success_events = sum(
            1 for e in events if str(e.get("type") or e.get("kind") or "") in {"task_complete", "execution_complete"}
        )
        failure_events = sum(
            1 for e in events if str(e.get("type") or e.get("kind") or "") in {"task_failed", "execution_failed"}
        )
        promoted = sum(1 for s in suggestions if str(s.get("status") or "") == "promoted")
        approved = sum(1 for s in suggestions if str(s.get("status") or "") == "approved")
        runtime_ok = sum(1 for r in runtimes if str(r.get("status") or "") in {"deployed", "running", "succeeded"})
        exec_ok = sum(1 for ex in executions if str(ex.get("status") or "") in {"succeeded", "deployed", "running"})

        score = 50
        score += min(total_events, 15)
        score += success_events * 8
        score -= failure_events * 12
        score += promoted * 6
        score += approved * 3
        score += runtime_ok * 4
        score += exec_ok * 5
        score = max(0, min(100, score))

        agent_result = self._agent.evaluate(
            contract or {
                "execution_id": str(payload.get("execution_id") or ""),
                "task_id": str(payload.get("task_id") or ""),
                "project_path": str(payload.get("project_path") or ""),
                "goal": str(payload.get("goal") or payload.get("intent") or ""),
                "acceptance_criteria": list(payload.get("acceptance_criteria") or []),
                "evidence": dict(payload.get("evidence") or {"contract": {}, "stages": {}}),
            },
            evidence=dict(payload.get("evidence") or {}),
        )

        agent_data = agent_result.get("data", {})
        return {
            "success": True,
            "data": {
                "score": score,
                "event_count": total_events,
                "success_signals": success_events,
                "failure_signals": failure_events,
                "promoted_suggestions": promoted,
                "approved_suggestions": approved,
                "healthy_runtimes": runtime_ok,
                "healthy_executions": exec_ok,
                "agent": agent_data,
                "agent_score": agent_data.get("score_card", {}),
                "agent_verdict": agent_data.get("verdict", ""),
            },
        }
