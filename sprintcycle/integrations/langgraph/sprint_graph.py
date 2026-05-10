"""LangGraph sprint graph for SprintCycle V2.

This graph drives a single Sprint lifecycle:
Prepare -> Execute -> Observe -> Repair -> Finalize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .graph_runtime import LangGraphExecutionRuntime
from ...observability.facade import ObservabilityFacade
from ...integrations.phoenix.trace_runtime import PhoenixTraceRuntime
from ...integrations.phoenix.exporter import PhoenixExporterSpec


@dataclass
class SprintGraphRuntime:
    project_name: str = "sprintcycle"
    config: Dict[str, Any] = field(default_factory=dict)

    def build(self) -> Dict[str, Any]:
        runtime = LangGraphExecutionRuntime().build()
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "runtime": runtime,
            "nodes": ["prepare", "execute", "observe", "repair", "finalize"],
        }

    async def run(self, sprint: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            "sprint": dict(sprint),
            "context": dict(context),
            "project_name": self.project_name,
        }
        state = self.prepare(state)
        max_retries = int(state.get("context", {}).get("max_retries", self.config.get("max_retries", 1)) or 1)
        attempt = 0
        while True:
            attempt += 1
            state["attempt"] = attempt
            state = await self.execute(state)
            state = self.observe(state)
            state = self.repair(state)
            action = state.get("repair_decision", {}).get("action", "finalize")
            if action != "retry" or attempt >= max_retries:
                state = self.finalize(state)
                break
            state.setdefault("timeline", []).append({"node": "retry", "status": "ok", "attempt": attempt})
        return state

    async def resume(self, sprint_id: str) -> Dict[str, Any]:
        return {
            "sprint_id": sprint_id,
            "project_name": self.project_name,
            "status": "resume_not_implemented",
        }

    def prepare(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["sprint_context"] = {
            "sprint_name": state.get("sprint", {}).get("name", ""),
            "project_name": self.project_name,
            "runtime_config": state.get("context", {}).get("runtime_config", {}),
        }
        state.setdefault("timeline", []).append({"node": "prepare", "status": "ok"})
        return state

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        sprint_executor = state.get("context", {}).get("sprint_executor")
        sprint = state.get("sprint", {})
        sprint_context = state.get("sprint_context", {})
        if sprint_executor is not None and hasattr(sprint_executor, "execute_sprint"):
            sprint_result_obj = await sprint_executor.execute_sprint(sprint=sprint, context=sprint_context)
            sprint_result = sprint_result_obj.to_dict() if hasattr(sprint_result_obj, "to_dict") else {
                "sprint_name": sprint.get("name", ""),
                "status": getattr(getattr(sprint_result_obj, "status", None), "value", str(getattr(sprint_result_obj, "status", "success"))),
                "task_results": [],
                "duration": float(getattr(sprint_result_obj, "duration", 0.0)),
            }
        else:
            sprint_result = {
                "sprint_name": sprint.get("name", ""),
                "status": "failed",
                "task_results": [],
                "duration": 0.0,
                "error": "sprint_executor_unavailable",
            }
        state["sprint_result"] = sprint_result
        state.setdefault("timeline", []).append({"node": "execute", "status": "ok", "attempt": state.get("attempt", 1), "task_count": len(sprint_result.get("task_results", []) or [])})
        return state

    def observe(self, state: Dict[str, Any]) -> Dict[str, Any]:
        sprint_result = state.get("sprint_result", {})
        context = state.get("context", {})
        run_id = str(context.get("run_id") or context.get("execution_id") or "")
        obs = ObservabilityFacade()
        recorded_events = list(context.get("events", []) or [])
        trace_payload = obs.to_trace_payload(run_id) if run_id else {"run_id": run_id, "execution_id": run_id, "total": 0, "events": [], "phoenix_trace": PhoenixTraceRuntime(PhoenixExporterSpec(project_name=self.project_name)).emit_trace([])}
        task_results = list(sprint_result.get("task_results", []) or [])
        failed_tasks = [
            task_result.get("work_item", {}).get("description", "")
            for task_result in task_results
            if str(task_result.get("status", "")).lower() not in {"success", "succeeded", "completed"}
        ]
        task_count = len(task_results)
        failed_task_count = len(failed_tasks)
        task_success_rate = self._task_success_rate(task_results)
        task_failure_rate = self._task_failure_rate(task_results)
        observation_payload = {
            "sprint_name": state.get("sprint", {}).get("name", ""),
            "trace_ready": True,
            "result_status": sprint_result.get("status", "unknown"),
            "task_count": task_count,
            "failed_task_count": failed_task_count,
            "failed_tasks": failed_tasks,
            "events": recorded_events,
            "trace": trace_payload,
            "metrics": {
                "duration": sprint_result.get("duration", 0.0),
                "success": sprint_result.get("status") == "success",
                "task_success_rate": task_success_rate,
                "task_failure_rate": task_failure_rate,
            },
        }
        state["observation_payload"] = observation_payload
        state.setdefault("timeline", []).append({"node": "observe", "status": "ok", "attempt": state.get("attempt", 1), "task_count": task_count, "failed_task_count": failed_task_count})
        return state

    def repair(self, state: Dict[str, Any]) -> Dict[str, Any]:
        observation = state.get("observation_payload", {})
        metrics = observation.get("metrics", {})
        task_success_rate = float(metrics.get("task_success_rate", 1.0) or 0.0)
        task_failure_rate = float(metrics.get("task_failure_rate", 0.0) or 0.0)
        failed_task_count = int(observation.get("failed_task_count", 0) or 0)
        if observation.get("result_status") == "failed" or not metrics.get("success", True) or task_success_rate < 1.0 or task_failure_rate > 0.0 or failed_task_count > 0:
            state["repair_decision"] = {
                "action": "retry",
                "reason": "sprint_failed_or_metrics_unhealthy",
                "task_success_rate": task_success_rate,
                "task_failure_rate": task_failure_rate,
                "failed_task_count": failed_task_count,
            }
        else:
            state["repair_decision"] = {
                "action": "finalize",
                "reason": "no_repair_needed",
                "task_success_rate": task_success_rate,
                "task_failure_rate": task_failure_rate,
                "failed_task_count": failed_task_count,
            }
        state.setdefault("timeline", []).append({"node": "repair", "status": "ok", "action": state["repair_decision"]["action"], "attempt": state.get("attempt", 1)})
        return state

    def finalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["final_sprint_result"] = state.get("sprint_result", {})
        state.setdefault("timeline", []).append({"node": "finalize", "status": "ok"})
        return state

    def _task_success_rate(self, task_results: List[Dict[str, Any]]) -> float:
        if not task_results:
            return 1.0
        total = len(task_results)
        success = 0
        for result in task_results:
            status = str(result.get("status", "")).lower()
            if status in {"success", "succeeded", "completed"}:
                success += 1
        return success / total if total else 1.0

    def _task_failure_rate(self, task_results: List[Dict[str, Any]]) -> float:
        if not task_results:
            return 0.0
        total = len(task_results)
        failed = 0
        for result in task_results:
            status = str(result.get("status", "")).lower()
            if status not in {"success", "succeeded", "completed"}:
                failed += 1
        return failed / total if total else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
        }


__all__ = ["SprintGraphRuntime"]
