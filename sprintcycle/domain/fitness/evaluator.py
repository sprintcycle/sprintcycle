"""Fitness evaluator.

This module belongs to the fitness / evaluation layer. It should only score and
recommend; it must not mutate state, render UI, or execute governance decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sprintcycle.application.services.evaluator_agent import EvaluatorAgent
from sprintcycle.domain.fitness.aggregator import FitnessAggregator


@dataclass
class FitnessEvaluator:
    aggregator: FitnessAggregator = field(default_factory=FitnessAggregator)

    def __post_init__(self) -> None:
        self._agent = EvaluatorAgent()

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dimensions: List[Dict[str, Any]] = list(payload.get("dimensions") or [])
        aggregate: Dict[str, Any]

        if dimensions:
            aggregate = self.aggregator.aggregate(dimensions)
        else:
            events: List[Dict[str, Any]] = list(payload.get("events") or [])
            executions: List[Dict[str, Any]] = list(payload.get("executions") or [])
            suggestions: List[Dict[str, Any]] = list(payload.get("suggestions") or [])
            runtimes: List[Dict[str, Any]] = list(payload.get("runtimes") or [])

            derived_dimensions = [
                {
                    "name": "events",
                    "score": max(
                        0,
                        min(
                            100,
                            50
                            + min(len(events), 15)
                            + sum(
                                1
                                for e in events
                                if str(e.get("type") or e.get("kind") or "") in {"task_complete", "execution_complete"}
                            )
                            * 8
                            - sum(
                                1
                                for e in events
                                if str(e.get("type") or e.get("kind") or "") in {"task_failed", "execution_failed"}
                            )
                            * 12,
                        ),
                    ),
                    "weight": 0.3,
                    "reason": "derived from event success/failure balance",
                    "metadata": {
                        "core": {"source": "payload.events", "count": len(events)},
                        "extra": {"raw": events},
                    },
                },
                {
                    "name": "suggestions",
                    "score": max(
                        0,
                        min(
                            100,
                            50
                            + sum(1 for s in suggestions if str(s.get("status") or "") == "promoted") * 6
                            + sum(1 for s in suggestions if str(s.get("status") or "") == "approved") * 3,
                        ),
                    ),
                    "weight": 0.2,
                    "reason": "derived from suggestion promotion/approval counts",
                    "metadata": {
                        "core": {
                            "source": "payload.suggestions",
                            "promoted_count": sum(1 for s in suggestions if str(s.get("status") or "") == "promoted"),
                            "approved_count": sum(1 for s in suggestions if str(s.get("status") or "") == "approved"),
                        },
                        "extra": {"raw": suggestions},
                    },
                },
                {
                    "name": "runtime",
                    "score": max(
                        0,
                        min(
                            100,
                            50
                            + sum(
                                1
                                for r in runtimes
                                if str(r.get("status") or "") in {"deployed", "running", "succeeded"}
                            )
                            * 4
                            + sum(
                                1
                                for ex in executions
                                if str(ex.get("status") or "") in {"succeeded", "deployed", "running"}
                            )
                            * 5,
                        ),
                    ),
                    "weight": 0.25,
                    "reason": "derived from runtime and execution health",
                    "metadata": {
                        "core": {
                            "source": "payload.runtime_and_executions",
                            "healthy_runtimes": sum(
                                1
                                for r in runtimes
                                if str(r.get("status") or "") in {"deployed", "running", "succeeded"}
                            ),
                            "healthy_executions": sum(
                                1
                                for ex in executions
                                if str(ex.get("status") or "") in {"succeeded", "deployed", "running"}
                            ),
                        },
                        "extra": {"runtimes": runtimes, "executions": executions},
                    },
                },
                {
                    "name": "agent",
                    "score": 100.0,
                    "weight": 0.25,
                    "reason": "domain agent evaluation attached",
                    "metadata": {
                        "core": {"source": "EvaluatorAgent", "contract_present": bool(payload.get("contract"))},
                        "extra": {},
                    },
                },
            ]
            aggregate = self.aggregator.aggregate(derived_dimensions)

        contract = dict(payload.get("contract") or {})
        agent_result = self._agent.evaluate(
            contract
            or {
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

        aggregate_data = dict(aggregate.get("data") or {})
        aggregate_data.update(
            {
                "agent": agent_data,
                "agent_score": agent_data.get("score_card", {}),
                "agent_verdict": agent_data.get("verdict", ""),
            }
        )
        return {"success": True, "data": aggregate_data}
