"""Public API service for external integrations.

This layer deliberately exposes only the stable, minimal contract that external
systems should depend on.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from sprintcycle.api import SprintCycle

from .request_context import RequestContext


class PublicAPIService:
    def __init__(self, sprint_cycle: SprintCycle):
        self.sc = sprint_cycle

    def plan(
        self,
        *,
        intent: str = "",
        mode: str = "auto",
        target: Optional[str] = None,
        release_plan_yaml: Optional[str] = None,
        release_plan_path: Optional[str] = None,
        product: Optional[str] = None,
        reference_paths: Optional[List[str]] = None,
        write_policy: str = "auto",
        context: Optional[RequestContext] = None,
    ) -> Dict[str, Any]:
        result = self.sc.plan(
            intent=intent,
            mode=mode,
            target=target,
            release_plan_yaml=release_plan_yaml,
            release_plan_path=release_plan_path,
            product=product,
            reference_paths=reference_paths,
            write_policy=write_policy,
        )
        return result.to_dict()

    def run(
        self,
        *,
        intent: Optional[str] = None,
        mode: str = "auto",
        target: Optional[str] = None,
        release_plan_yaml: Optional[str] = None,
        release_plan_path: Optional[str] = None,
        product: Optional[str] = None,
        execution_id: Optional[str] = None,
        resume: bool = False,
        reference_paths: Optional[List[str]] = None,
        write_policy: str = "auto",
        context: Optional[RequestContext] = None,
    ) -> Dict[str, Any]:
        result = self.sc.run(
            intent=intent,
            mode=mode,
            target=target,
            release_plan_yaml=release_plan_yaml,
            release_plan_path=release_plan_path,
            product=product,
            execution_id=execution_id,
            resume=resume,
            reference_paths=reference_paths,
            write_policy=write_policy,
        )
        return result.to_dict()

    def status(self, execution_id: Optional[str] = None, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        result = self.sc.status(execution_id=execution_id)
        return result.to_dict()

    def stop(self, *, execution_id: str, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        result = self.sc.stop(execution_id=execution_id)
        return result.to_dict()

    def rollback(self, *, execution_id: str, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        result = self.sc.rollback(execution_id=execution_id)
        return result.to_dict()

    def diagnose(self, context: Optional[RequestContext] = None) -> Dict[str, Any]:
        result = self.sc.diagnose()
        return result.to_dict()

    def governance_check(self, gate: str = "review", context: Optional[RequestContext] = None) -> Dict[str, Any]:
        from sprintcycle.governance.runner import run_governance_check_and_persist
        from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig

        cfg = RuntimeConfig.from_project(self.sc.project_path)

        planning_report, review_report, fail = asyncio.run(
            asyncio.to_thread(run_governance_check_and_persist, self.sc.project_path, cfg, gate)
        )
        out: Dict[str, Any] = {"should_fail_ci": fail, "gate": gate}
        if planning_report is not None:
            out["planning"] = planning_report.to_dict()
        if review_report is not None:
            out["review"] = review_report.to_dict()
        return out
