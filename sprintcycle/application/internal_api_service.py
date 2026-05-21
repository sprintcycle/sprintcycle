"""Internal API service for Dashboard and internal control surfaces.

This service keeps the full operational surface available to the Dashboard
without exposing those capabilities to the public integration API.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from sprintcycle.api import SprintCycle

from .request_context import RequestContext


class InternalAPIService:
    def __init__(self, sprint_cycle: SprintCycle):
        self.sc = sprint_cycle

    def project_path(self) -> str:
        return self.sc.project_path

    def status(self, execution_id: Optional[str] = None, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.status(execution_id=execution_id).to_dict()

    def hitl_pending(
        self, execution_id: Optional[str] = None, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return asyncio.run(self.sc.hitl_pending(execution_id=execution_id))

    def hitl_history(
        self, execution_id: Optional[str] = None, limit: int = 50, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return asyncio.run(self.sc.hitl_history(execution_id=execution_id, limit=limit))

    def hitl_show(self, request_id: str, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return asyncio.run(self.sc.hitl_show(request_id))

    def hitl_submit(
        self, request_id: str, decision: str, note: Optional[str] = None, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return asyncio.run(self.sc.hitl_submit(request_id, decision, note))

    def console_overview(self, *, limit: int = 20, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.console_overview(limit=limit)

    def platform_overview(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.platform_overview()

    def management_overview(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.management_overview()

    def fitness_view(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.fitness_view()

    def evaluate_sprint_contract(
        self, payload: Dict[str, Any], context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return self.sc.evaluate_sprint_contract(payload)

    def lifecycle_contract_review(
        self, execution_id: str, payload: Optional[Dict[str, Any]] = None, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        body = dict(payload or {})
        body.setdefault("contract", self.sc.lifecycle_contract(execution_id).get("data", {}))
        return self.sc.evaluate_sprint_contract(body)

    def deploy_view(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.deploy_view()

    def deploy_lifecycle(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.deploy_lifecycle()

    def governance_view(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.governance_view()

    def governance_lifecycle(self, execution_id: str = "", context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.governance_lifecycle(execution_id=execution_id)

    def governance_history(self, limit: int = 50, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.governance_history(limit=limit)

    def read_governance_reports(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig

        cfg = RuntimeConfig.from_project(self.sc.project_path)
        root = Path(self.sc.project_path).expanduser().resolve()
        rel = (cfg.governance_report_dir or ".sprintcycle").strip() or ".sprintcycle"
        out_dir = (root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        last = out_dir / "governance_last.json"
        planning = out_dir / "governance_planning_last.json"
        if not last.is_file() and not planning.is_file():
            raise FileNotFoundError("未找到治理报告")
        payload: Dict[str, Any] = {}
        if planning.is_file():
            payload["planning"] = planning.read_text(encoding="utf-8")
        if last.is_file():
            payload["review"] = last.read_text(encoding="utf-8")
        return payload

    def fix_view(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.fix_view()

    def architecture_check(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.architecture_check()

    def execution_detail(
        self, execution_id: str, *, limit: int = 200, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return self.sc.execution_detail(execution_id, limit=limit)

    def execution_events(
        self, execution_id: str, *, limit: int = 200, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return self.sc.execution_events(execution_id, limit=limit)

    def replay_execution(
        self, execution_id: str, *, limit: int = 500, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return self.sc.replay_execution(execution_id, limit=limit)

    def runtime_latest(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.runtime_latest()

    def runtime_update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        return self.sc.runtime_update(runtime_id, **changes)

    def observability_trace(self, run_id: str, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.observability_trace(run_id)

    def observability_replay(self, run_id: str, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.observability_replay(run_id)

    def lifecycle_contract(
        self, execution_id: str, *, limit: int = 200, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        return self.sc.lifecycle_contract(execution_id, limit=limit)

    def diagnose_repair_observe(
        self,
        execution_id: str,
        *,
        repair_plan: Optional[Dict[str, Any]] = None,
        context: Optional[RequestContext] = None,
    ) -> Dict[str, Any]:
        return self.sc.diagnose_repair_observe(execution_id, repair_plan=repair_plan)

    def suggestion_overview(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        return self.sc.suggestion_overview()

    def suggestion_board(
        self, execution_id: Optional[str] = None, limit: int = 20, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        from sprintcycle.dashboard.view_service import DashboardViewService
        from sprintcycle.dashboard.workbench import DashboardWorkbenchService

        dashboard_views = DashboardViewService(project_path=self.sc.project_path)
        dashboard_workbench = DashboardWorkbenchService(view_service=dashboard_views)
        return dashboard_workbench.suggestion_board(self.sc, execution_id=execution_id, limit=limit)

    def suggestion_and_hitl_panel(
        self, execution_id: Optional[str] = None, limit: int = 20, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        from sprintcycle.dashboard.view_service import DashboardViewService
        from sprintcycle.dashboard.workbench import DashboardWorkbenchService

        dashboard_views = DashboardViewService(project_path=self.sc.project_path)
        dashboard_workbench = DashboardWorkbenchService(view_service=dashboard_views)
        return asyncio.run(
            dashboard_workbench.suggestion_and_hitl_panel(self.sc, execution_id=execution_id, limit=limit)
        )

    def execution_workspace(
        self, execution_id: str, limit: int = 200, context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        from sprintcycle.dashboard.view_service import DashboardViewService

        dashboard_views = DashboardViewService(project_path=self.sc.project_path)
        return dashboard_views.execution_workspace(self.sc, execution_id=execution_id, limit=limit)

    def dashboard_platform_workspace(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        from sprintcycle.dashboard.view_service import DashboardViewService

        dashboard_views = DashboardViewService(project_path=self.sc.project_path)
        return dashboard_views.platform_workspace(self.sc.platform_overview())

    def review_suggestion(
        self,
        execution_id: str,
        suggestion_id: str,
        *,
        reviewer: str = "",
        notes: str = "",
        context: Optional[RequestContext] = None,
    ) -> Dict[str, Any]:
        return self.sc.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    def approve_suggestion(
        self,
        execution_id: str,
        suggestion_id: str,
        *,
        approver: str = "",
        notes: str = "",
        context: Optional[RequestContext] = None,
    ) -> Dict[str, Any]:
        return self.sc.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)

    def reject_suggestion(
        self,
        execution_id: str,
        suggestion_id: str,
        *,
        rejected_by: str = "",
        notes: str = "",
        context: Optional[RequestContext] = None,
    ) -> Dict[str, Any]:
        return self.sc.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)
