"""
SprintCycle Public API - 向后兼容层

本模块提供向后兼容的 SprintCycle 类，作为 CLI/MCP/Dashboard 的统一入口点。
核心实现已迁移到 application/http_factories.py 的 HTTPServices 类。
"""

from __future__ import annotations

from typing import Any, Optional

from sprintcycle.application.http_factories import HTTPServices
from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig


class SprintCycle:
    """SprintCycle 统一 API - 向后兼容封装

    实际逻辑委托给 HTTPServices 类。
    """

    def __init__(
        self,
        project_path: str,
        config: Optional[RuntimeConfig] = None,
    ):
        self.project_path = project_path
        self.config = config or RuntimeConfig.from_project(project_path)
        self._services = HTTPServices(project_path)

    # ===== 代理方法（兼容原有调用方式）=====

    def status(self, execution_id: str = "") -> Any:
        return self._services.status(execution_id)

    def hitl_pending(self, execution_id: Optional[str] = None) -> Any:
        return self._services.hitl_pending(execution_id)

    def hitl_history(self, execution_id: Optional[str] = None, limit: int = 50) -> Any:
        return self._services.hitl_history(execution_id, limit)

    def hitl_show(self, request_id: str) -> Any:
        return self._services.hitl_show(request_id)

    def hitl_submit(self, request_id: str, decision: str, note: Optional[str] = None) -> Any:
        return self._services.hitl_submit(request_id, decision, note)

    def console_overview(self, limit: int = 20) -> Any:
        return self._services.console_overview(limit=limit)

    def platform_overview(self) -> Any:
        return self._services.platform_overview()

    def governance_view(self) -> Any:
        return self._services.governance_view()

    def governance_history(self, limit: int = 50) -> Any:
        return self._services.governance_history(limit)

    def governance_lifecycle(self, execution_id: str = "") -> Any:
        return self._services.governance_lifecycle(execution_id)

    def lifecycle_contract(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.lifecycle_contract(execution_id, limit=limit)

    def evaluate_sprint_contract(self, payload: Any) -> Any:
        return self._services.evaluate_sprint_contract(payload)

    def deploy_view(self) -> Any:
        return self._services.deploy_view()

    def deploy_lifecycle(self) -> Any:
        return self._services.deploy_lifecycle()

    def fix_view(self) -> Any:
        return self._services.fix_view()

    def diagnose_repair_observe(self, execution_id: str, repair_plan: Optional[Any] = None) -> Any:
        return self._services.diagnose_repair_observe(execution_id, repair_plan)

    def execution_detail(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.execution_detail(execution_id, limit=limit)

    def execution_events(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.execution_events(execution_id, limit=limit)

    def replay_execution(self, execution_id: str, limit: int = 500) -> Any:
        return self._services.replay_execution(execution_id, limit=limit)

    def observability_trace(self, run_id: str) -> Any:
        return self._services.observability_trace(run_id)

    def observability_replay(self, run_id: str) -> Any:
        return self._services.observability_replay(run_id)

    def fitness_view(self) -> Any:
        return self._services.fitness_view()

    def suggestion_overview(self) -> Any:
        return self._services.suggestion_overview()

    def management_overview(self) -> Any:
        return self._services.management_overview()

    def suggestion_board(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        return self._services.suggestion_board(execution_id=execution_id, limit=limit)

    def suggestion_and_hitl_panel(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        return self._services.suggestion_and_hitl_panel(self, execution_id=execution_id, limit=limit)

    def execution_workspace(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.execution_workspace(execution_id, limit=limit)

    def dashboard_platform_workspace(self) -> Any:
        return self._services.dashboard_platform_workspace()

    def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Any:
        return self._services.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Any:
        return self._services.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)

    def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Any:
        return self._services.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)

    def architecture_check(self) -> Any:
        return self._services.architecture_check()

    def evolution_overview(self) -> Any:
        return self._services.evolution_overview()

    def evolution_overview_cli(self) -> str:
        return self._services.evolution_overview_cli()

    def list_evolution_versions(self, target: Optional[str] = None, limit: int = 20) -> Any:
        return self._services.list_evolution_versions(target=target, limit=limit)

    def get_evolution_version(self, version_id: str) -> Any:
        return self._services.get_evolution_version(version_id)

    def diagnose(self, execution_id: str = "") -> Any:
        return self._services.diagnose(execution_id)

    def stop(self, execution_id: str = "") -> Any:
        return self._services.stop(execution_id)

    def rollback(self, execution_id: str) -> Any:
        return self._services.rollback(execution_id)

    def knowledge_search(self, query: str = "", tags: Optional[list] = None, limit: int = 50) -> Any:
        """搜索知识卡片"""
        from sprintcycle.infrastructure.knowledge_repository import KnowledgeCardRepository

        sqlite_path = getattr(self.config, "sqlite_path", None) or ".sprintcycle/knowledge.db"
        repo = KnowledgeCardRepository(sqlite_path)
        cards = repo.search(query=query, tags=tags, limit=limit)
        return {
            "success": True,
            "total": len(cards),
            "cards": [c.to_dict() for c in cards],
        }

    # ===== 公开 API 方法（plan/run 等）=====

    def plan(
        self,
        intent: str = "",
        mode: str = "auto",
        target: Optional[str] = None,
        release_plan_yaml: Optional[str] = None,
        release_plan_path: Optional[str] = None,
        product: Optional[str] = None,
        reference_paths: Optional[list] = None,
        write_policy: str = "auto",
    ) -> Any:
        """生成发布计划"""
        from sprintcycle.application.sprint_orchestrator import SprintOrchestrator

        orchestrator = SprintOrchestrator(project_path=self.project_path, config=self.config)
        return orchestrator.plan(
            intent=intent,
            mode=mode,
            target=target,
            release_plan_yaml=release_plan_yaml,
            release_plan_path=release_plan_path,
            product=product,
            reference_paths=reference_paths,
            write_policy=write_policy,
        )

    def run(
        self,
        intent: Optional[str] = None,
        mode: str = "auto",
        target: Optional[str] = None,
        release_plan_yaml: Optional[str] = None,
        release_plan_path: Optional[str] = None,
        product: Optional[str] = None,
        reference_paths: Optional[list] = None,
    ) -> Any:
        """执行发布计划"""
        from sprintcycle.application.sprint_orchestrator import SprintOrchestrator

        orchestrator = SprintOrchestrator(project_path=self.project_path, config=self.config)
        return orchestrator.run(
            intent=intent,
            mode=mode,
            target=target,
            release_plan_yaml=release_plan_yaml,
            release_plan_path=release_plan_path,
            product=product,
            reference_paths=reference_paths,
        )


__all__ = ["SprintCycle"]
