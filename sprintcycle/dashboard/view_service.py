"""Dashboard view aggregation services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import asyncio

from sprintcycle.governance.suggestion import SuggestionFacade

from .service import DashboardQueryService
from sprintcycle.execution.state import summarize_state_machine
from sprintcycle.execution.state.state_store import get_state_store
from sprintcycle.integrations.langgraph.graph import build_default_langgraph_graph_spec
from sprintcycle.integrations.langgraph.runtime import LangGraphRuntimeAdapter, LangGraphRuntimeSpec
from sprintcycle.integrations.phoenix.exporter import PhoenixExporterSpec
from sprintcycle.integrations.phoenix.runtime import PhoenixRuntimeAdapter, PhoenixRuntimeSpec
from sprintcycle.platform.overview import build_platform_overview
from sprintcycle.platform.spec import build_platform_spec
from sprintcycle.dashboard.views.architecture_view import ArchitectureView
from sprintcycle.dashboard.views.deploy_view import DeployView
from sprintcycle.dashboard.views.fix_view import FixView
from sprintcycle.dashboard.views.fitness_view import FitnessView
from sprintcycle.dashboard.views.governance_view import GovernanceView


@dataclass
class DashboardViewService:
    project_path: str
    query_service: DashboardQueryService = DashboardQueryService()

    def build_fitness_payload(self, observability: Any, runtime_registry: Any, suggestion: SuggestionFacade) -> Dict[str, Any]:
        return {
            "events": observability.list_events().get("data", []),
            "executions": [],
            "suggestions": [s.to_dict() for s in asyncio.run(suggestion.list_suggestions(limit=100))],
            "runtimes": list(getattr(runtime_registry, "records", [])),
        }

    def suggestion_overview_payload(self, suggestion_overview: Any) -> Dict[str, Any]:
        return suggestion_overview.to_dashboard_payload() if hasattr(suggestion_overview, "to_dashboard_payload") else suggestion_overview

    def suggestion_list_payload(self, suggestions: Any) -> Dict[str, Any]:
        if isinstance(suggestions, dict):
            return suggestions
        return {"suggestions": [s.to_dict() for s in suggestions]}

    def suggestion_board(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        payload = sprintcycle.suggestion_overview_dashboard()
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        if execution_id:
            suggestions = [s for s in data.get("suggestions", []) if str(s.get("execution_id", "")) == str(execution_id)]
            data["suggestions"] = suggestions
            data["execution_id"] = execution_id
            data["total"] = len(suggestions)
        data["suggestions"] = (data.get("suggestions", []) or [])[:limit]
        return {"success": True, "data": data}

    async def hitl_queue(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        payload = await sprintcycle.observability_pending(execution_id=execution_id)
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        requests = list(data or [])
        if limit >= 0:
            requests = requests[:limit]
        return {"success": True, "data": {"execution_id": execution_id or "", "requests": requests, "total": len(requests)}}

    async def suggestion_and_hitl_panel(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        suggestions = self.suggestion_board(sprintcycle, execution_id=execution_id, limit=limit)
        hitl = await self.hitl_queue(sprintcycle, execution_id=execution_id, limit=limit)
        return {
            "success": True,
            "data": {
                "execution_id": execution_id or "",
                "suggestions": suggestions.get("data", {}),
                "hitl": hitl.get("data", {}),
            },
        }

    def platform_overview(self) -> Dict[str, Any]:
        overview = build_platform_overview(self.project_path).to_dict()
        overview["project_path"] = self.project_path
        overview["runtime"]["langgraph_runtime"] = LangGraphRuntimeAdapter(
            spec=LangGraphRuntimeSpec(project_name=self.project_path)
        ).build_graph()
        overview["trace"]["phoenix_runtime"] = PhoenixRuntimeAdapter(
            spec=PhoenixRuntimeSpec(project_name=self.project_path)
        ).build_exporter()
        overview["trace"]["phoenix_exporter"] = PhoenixExporterSpec(project_name=self.project_path).to_dict()
        overview["runtime"]["langgraph_graph"] = build_default_langgraph_graph_spec(self.project_path).to_dict()
        return {"success": True, "data": overview}

    def console_overview(self, *, trace_payload: Dict[str, Any] | None = None, limit: int = 20) -> Dict[str, Any]:
        store = get_state_store()
        states = store.list_executions(limit=max(1, int(limit)))
        executions = [s.to_dict() for s in states]
        running = [s.to_dict() for s in states if str(s.status.value) == "running"]
        latest = executions[0] if executions else None
        recent_events = []
        if trace_payload:
            recent_events = list(trace_payload.get("events", []) or [])[:20]
        return {
            "success": True,
            "data": {
                "executions": executions,
                "running_executions": running,
                "primary_execution": latest,
                "recent_events": recent_events,
                "platform": build_platform_spec(self.project_path).to_dict(),
                "state_machine": summarize_state_machine(),
            },
        }

    def execution_detail(self, *, execution_id: str, state: Any, trace: Dict[str, Any], limit: int = 200) -> Dict[str, Any]:
        detail = {
            "state": state.to_dict(),
            "trace": trace,
            "platform": self.platform_overview().get("data", {}),
            "state_machine": summarize_state_machine(),
            "limit": limit,
        }
        return {"success": True, "data": detail}

    def fitness_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": FitnessView(payload=payload).to_payload()}

    def governance_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": GovernanceView(payload=payload).to_payload()}

    def fix_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": FixView(payload=payload).to_payload()}

    def deploy_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": DeployView(payload=payload).to_payload()}

    def architecture_check_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return ArchitectureView(payload=payload).to_payload()

    def platform_workspace(self, platform_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "data": platform_payload.get("data", platform_payload)}

    def execution_workspace(
        self,
        *,
        execution_id: str,
        execution_detail: Dict[str, Any],
        platform: Dict[str, Any],
        suggestions: Dict[str, Any],
        hitl: Dict[str, Any],
        fitness: Dict[str, Any],
        deployment: Dict[str, Any],
    ) -> Dict[str, Any]:
        from .service import DashboardQueryService

        query_service = DashboardQueryService()
        bundle = query_service.build_bundle(
            execution_id=execution_id,
            trace=execution_detail.get("data", {}).get("trace", {}),
            replay={},
            suggestions=suggestions,
            hitl=hitl,
            deployment=deployment,
            fitness=fitness,
        )
        return {
            "success": True,
            "data": {
                "execution_id": execution_id,
                "execution": execution_detail.get("data", execution_detail),
                "platform": platform.get("data", platform),
                "bundle": bundle.to_dict(),
            },
        }
