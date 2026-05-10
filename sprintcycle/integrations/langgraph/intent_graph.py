"""LangGraph intent graph for SprintCycle V2.

This graph drives the top-level lifecycle:
Intent -> Plan -> Sprint Split -> Sprint Dispatch -> Finalize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .graph_runtime import LangGraphExecutionRuntime
from .plan_runtime import PlanRuntime
from .sprint_graph import SprintGraphRuntime


@dataclass
class IntentGraphRuntime:
    project_name: str = "sprintcycle"
    config: Dict[str, Any] = field(default_factory=dict)
    sprint_graph: SprintGraphRuntime = field(default_factory=SprintGraphRuntime)
    plan_runtime: PlanRuntime = field(default_factory=PlanRuntime)

    def build(self) -> Dict[str, Any]:
        runtime = LangGraphExecutionRuntime().build()
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "runtime": runtime,
            "nodes": ["intent_received", "plan_generated", "sprint_split", "sprint_dispatch", "finalize"],
        }

    async def run(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            "intent": intent,
            "context": dict(context),
            "project_name": self.project_name,
        }
        state = self.intent_received(state)
        max_retries = int(state.get("context", {}).get("max_retries", self.config.get("max_retries", 1)) or 1)
        attempt = 0
        while True:
            attempt += 1
            state["attempt"] = attempt
            state = self.plan_generated(state)
            state = self.sprint_split(state)
            state = await self.sprint_dispatch(state)
            state = self.evaluate(state)
            action = state.get("evaluation", {}).get("action", "finalize")
            if action != "retry" or attempt >= max_retries:
                state = self.finalize(state)
                break
            state.setdefault("timeline", []).append({"node": "retry", "status": "ok", "attempt": attempt})
        return state

    async def resume(self, run_id: str) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "project_name": self.project_name,
            "status": "resume_not_implemented",
        }

    def intent_received(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["intent_context"] = {
            "intent": state.get("intent", ""),
            "project_path": state.get("context", {}).get("project_path", ""),
            "runtime_config": state.get("context", {}).get("runtime_config", {}),
        }
        state.setdefault("timeline", []).append({"node": "intent_received", "status": "ok"})
        return state

    def plan_generated(self, state: Dict[str, Any]) -> Dict[str, Any]:
        intent_context = state.get("intent_context", {})
        release_plan = state.get("context", {}).get("release_plan")
        if hasattr(release_plan, "to_dict"):
            plan_data = release_plan.to_dict()
        elif isinstance(release_plan, dict):
            plan_data = dict(release_plan)
        else:
            plan_data = self.plan_runtime.build_release_plan_from_intent(
                intent=str(intent_context.get("intent", "")),
                context={**state.get("context", {}), **intent_context},
            ).to_dict()
        state["release_plan"] = plan_data
        state.setdefault("timeline", []).append({"node": "plan_generated", "status": "ok", "attempt": state.get("attempt", 1)})
        return state

    def sprint_split(self, state: Dict[str, Any]) -> Dict[str, Any]:
        release_plan = state.get("release_plan", {})
        sprints: List[Dict[str, Any]] = []
        if isinstance(release_plan, dict) and release_plan.get("sprints"):
            for sprint in release_plan.get("sprints", []):
                sprints.append(dict(sprint))
        else:
            intent = str(release_plan.get("intent", ""))
            sprints = [
                {
                    "name": "sprint-1",
                    "goals": [intent or "deliver value"],
                    "tasks": [],
                }
            ]
        state["sprints"] = sprints
        state.setdefault("timeline", []).append({"node": "sprint_split", "status": "ok", "sprint_count": len(sprints), "attempt": state.get("attempt", 1)})
        return state

    async def sprint_dispatch(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        sprint_executor = state.get("context", {}).get("sprint_executor")
        for sprint in state.get("sprints", []):
            sprint_context = dict(state.get("intent_context", {}))
            sprint_context["sprint_executor"] = sprint_executor
            if sprint_executor is not None:
                sprint_context["sprint_executor"] = sprint_executor
            result = await self.sprint_graph.run(sprint=sprint, context=sprint_context)
            results.append(result)
        state["sprint_results"] = results
        state.setdefault("timeline", []).append({"node": "sprint_dispatch", "status": "ok", "result_count": len(results), "attempt": state.get("attempt", 1)})
        return state

    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        sprint_results = list(state.get("sprint_results", []) or [])
        failed_sprints: List[Dict[str, Any]] = []
        retryable_failure_types = {"failed", "error", "cancelled", "timeout", "blocked"}
        abort_failure_types = {"blocked", "timeout"}
        for result in sprint_results:
            final_result = result.get("final_sprint_result", {}) or {}
            sprint_status = str(final_result.get("status", "")).lower()
            sprint_name = final_result.get("sprint_name", result.get("sprint", {}).get("name", ""))
            repair_decision = result.get("repair_decision", {}) or {}
            observation = result.get("observation_payload", {}) or {}
            task_failure_rate = float(observation.get("metrics", {}).get("task_failure_rate", 0.0) or 0.0)
            failed_task_count = int(observation.get("failed_task_count", 0) or 0)
            failure_type = sprint_status if sprint_status else ("failed" if failed_task_count > 0 or task_failure_rate > 0 else "unknown")
            if sprint_status not in {"success", "skipped"}:
                failed_sprints.append(
                    {
                        "sprint_name": sprint_name,
                        "status": sprint_status or "unknown",
                        "failure_type": failure_type,
                        "retryable": failure_type in retryable_failure_types,
                        "abort": failure_type in abort_failure_types,
                        "failed_task_count": failed_task_count,
                        "task_failure_rate": task_failure_rate,
                        "repair_action": repair_decision.get("action", "unknown"),
                    }
                )
        failed_sprint_count = len(failed_sprints)
        if failed_sprint_count > 0:
            abort_required = any(item.get("abort", False) for item in failed_sprints)
            retryable_count = sum(1 for item in failed_sprints if item.get("retryable", False))
            evaluation = {
                "action": "abort" if abort_required and retryable_count == 0 else "retry",
                "reason": "sprint_failure_types_require_abort" if abort_required and retryable_count == 0 else "one_or_more_sprints_failed",
                "failed_sprint_count": failed_sprint_count,
                "retryable_failure_count": retryable_count,
                "abort_required": abort_required,
                "failed_sprints": failed_sprints,
            }
        else:
            evaluation = {"action": "finalize", "reason": "all_sprints_successful", "failed_sprint_count": 0, "retryable_failure_count": 0, "abort_required": False, "failed_sprints": []}
        state["evaluation"] = evaluation
        state.setdefault("timeline", []).append({"node": "evaluate", "status": "ok", "action": evaluation["action"], "attempt": state.get("attempt", 1), "failed_sprint_count": failed_sprint_count})
        return state

    def finalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["final_result"] = {
            "project_name": self.project_name,
            "intent": state.get("intent", ""),
            "sprint_results": state.get("sprint_results", []),
            "evaluation": state.get("evaluation", {}),
            "status": "done",
        }
        state.setdefault("timeline", []).append({"node": "finalize", "status": "ok"})
        return state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "sprint_graph": self.sprint_graph.to_dict(),
        }


__all__ = ["IntentGraphRuntime"]
