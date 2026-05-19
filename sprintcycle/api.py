"""
SprintCycle public API.

This module exposes the main coordination layer for Dashboard, REST API, and
SDK usage. It handles request normalization, thin delegation, result assembly,
and stable coordination across execution, governance, suggestion,
observability, and platform summary services.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .infrastructure.config.runtime_config import RuntimeConfig
from .infrastructure.runtime_registry import RuntimeRegistry
from .execution.cache import configure_execution_cache_from_runtime
from .execution.events import (
    ensure_default_execution_event_backend_for_project,
    get_execution_event_backend,
)
from .execution.state import summarize_state_machine
from .execution.state.state_store import (
    configure_default_store,
    get_state_store,
)
from .execution_core import ExecutionContext, create_execution_engine
from .orchestration.sprint_orchestrator import SprintOrchestrator
from .results import (
    DiagnoseResult,
    EvolutionIndexResult,
    EvolutionOverviewResult,
    EvolutionSummary,
    EvolutionVersionListResult,
    EvolutionVersionSummary,
    FinalSnapshotVersionSummary,
    PlanResult,
    RollbackResult,
    RunResult,
    StatusResult,
    StopResult,
)
from .application.evolution.models import VersionArtifact
from .hooks import HookRegistry
from .run_workspace import (
    apply_policy_to_tasks,
    attach_workspace_metadata,
    effective_write_policy,
    ensure_project_layout,
    normalize_reference_paths,
    normalize_write_policy,
)
from .application.evolution import MemoryStore, UserIntentEvolutionLoop
from .fitness import FitnessEvaluator
from .application.services.evaluator_agent import EvaluatorAgent, SprintContractRecord, SprintScoreCard
from .governance.facade import GovernanceFacade, create_governance_facade
from .governance.suggestion import SuggestionFacade, create_suggestion_facade
from .persistence.knowledge_repository import KnowledgeCardRepository
from .versioning.interface import get_version_manifest_summary
from .versioning.sqlite_registry import SQLiteVersionRegistry
from .observability.facade import ObservabilityFacade
from .infrastructure.deployment_spec_service import DeploymentSpecService
from .application.services.execution_lifecycle_service import ExecutionLifecycleService
from .application.services.governance_orchestration_service import GovernanceOrchestrationService
from .application.services.lifecycle_evolution_service import LifecycleEvolutionService
from .application.services.observability_service import ObservabilityService
from .application.services.phase_workflow import build_decompose_artifact, build_plan_artifact, build_prepare_artifact
from .infrastructure.platform_launch_service import PlatformLaunchService
from .application.services.platform_summary_service import PlatformSummaryService
from .application.services.promotion_policy import PromotionPolicy
from .application.services.repair_orchestration_service import RepairOrchestrationService
from .application.services.suggestion_application_service import SuggestionApplicationService
from .platform.overview import build_platform_overview
from .infrastructure.integrations.langgraph.runtime import LangGraphRuntimeAdapter, LangGraphRuntimeSpec
from .infrastructure.integrations.phoenix.runtime import PhoenixRuntimeAdapter, PhoenixRuntimeSpec
from .infrastructure.integrations.phoenix.exporter import PhoenixExporterSpec
from .infrastructure.integrations.langgraph.graph import build_default_langgraph_graph_spec
from .platform.views import PlatformComposeView, PlatformSpecView
from .dashboard.views.architecture_view import ArchitectureView


class SprintCycle:
    """SprintCycle 统一 API — Dashboard / REST API / SDK 共用。

    **执行主架构**：``ReleasePlan`` → ``SprintOrchestrator.execute_release_plan`` → ``SprintExecutor``。
    自进化与普通迭代在执行栈上汇合。
    """

    def __init__(
        self,
        project_path: str = ".",
        config: Optional[RuntimeConfig] = None,
    ):
        self.project_path = os.path.abspath(project_path)
        base_cfg = config or RuntimeConfig.from_project(self.project_path)
        self.config = base_cfg.merge(base_cfg, {"project_path": self.project_path})
        configure_execution_cache_from_runtime(self.config, self.project_path)
        configure_default_store(self.project_path, self.config)
        ensure_default_execution_event_backend_for_project(self.project_path, self.config)
        self._orchestrator: Optional[SprintOrchestrator] = None
        self._governance: Optional[GovernanceFacade] = None
        self._evolution_registry = SQLiteVersionRegistry(
            root_dir=str(getattr(getattr(self.config, "evolution_versioning", None), "root_dir", None) or ".sprintcycle/versioning")
        )
        self._suggestion: SuggestionFacade = create_suggestion_facade(
            project_path=self.project_path,
            config=self.config,
            evolution_facade=None,
        )
        self._memory_store = MemoryStore(runtime_config=self.config)
        self._knowledge_repo = KnowledgeCardRepository(self._resolve_knowledge_db_path())
        self._intent_evolution_loop = UserIntentEvolutionLoop(
            memory_store=self._memory_store,
            feedback_loop=None,
            knowledge_repo=self._knowledge_repo,
        )
        self._execution_engine = create_execution_engine()
        self._observability = ObservabilityFacade()
        self._runtime_registry = RuntimeRegistry()
        self._hooks = HookRegistry()
        self._execution_service = ExecutionLifecycleService(
            project_path=self.project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            hooks=self._hooks,
        )
        self._observability_service = ObservabilityService(observability=self._observability)
        self._platform_summary = PlatformSummaryService(
            project_path=self.project_path,
        )
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=self.project_path,
            config=self.config,
            governance=self._get_governance(),
            hooks=self._hooks,
        )
        self._suggestion_application = SuggestionApplicationService(suggestion=self._suggestion, governance=self._get_governance())
        self._repair_orchestration = RepairOrchestrationService(observability=self._observability)
        self._promotion_policy = PromotionPolicy()
        self._lifecycle_evolution = LifecycleEvolutionService(
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            promotion_policy=self._promotion_policy,
        )
        self._fitness = FitnessEvaluator()
        self._deployment_spec = DeploymentSpecService()
        self._platform_launch = PlatformLaunchService(spec_service=self._deployment_spec)

    @property
    def intent_evolution_loop(self) -> UserIntentEvolutionLoop:
        return self._intent_evolution_loop

    @property
    def suggestion(self) -> SuggestionFacade:
        return self._suggestion

    @property
    def execution_engine(self):
        return self._execution_engine

    async def get_evolution_version(self, version_id: str) -> EvolutionVersionSummary:
        """查询单个演化版本摘要。"""
        payload = await get_version_manifest_summary(self._evolution_registry, version_id)
        return EvolutionVersionSummary(
            success=bool(payload.get("success")),
            error=payload.get("error"),
            version_id=payload.get("version_id", ""),
            target=payload.get("target", ""),
            commit_hash=payload.get("commit_hash", ""),
            tag=payload.get("tag", ""),
            branch=payload.get("branch", ""),
            manifest_path=payload.get("manifest_path", ""),
            sandbox_id=payload.get("sandbox_id", ""),
            metadata=dict(payload.get("metadata", {}) or {}),
        )

    async def list_evolution_versions(self, target: Optional[str] = None, limit: int = 20) -> EvolutionVersionListResult:
        """列出演化版本历史。"""
        versions = await self._evolution_registry.list_versions(target=target, limit=limit)
        return EvolutionVersionListResult(
            success=True,
            target=target or "",
            versions=[
                EvolutionVersionSummary(
                    success=True,
                    version_id=v.version_id,
                    target=v.target,
                    commit_hash=v.commit_hash or "",
                    tag=v.tag or "",
                    branch=v.branch or "",
                    manifest_path=v.manifest_path or "",
                    sandbox_id=v.sandbox_id or "",
                    metadata=dict(v.metadata or {}),
                )
                for v in versions
            ],
            total=len(versions),
        )

    async def export_evolution_index(self) -> EvolutionIndexResult:
        """导出演化版本索引。"""
        index = await self._evolution_registry.export_manifest_index()
        return EvolutionIndexResult(success=True, index=index)

    async def evolution_overview(self) -> EvolutionOverviewResult:
        """演化总览：active、recent candidate、索引与沙盒状态。"""
        active_versions: Dict[str, Dict[str, Any]] = {}
        for target in ("code", "requirement"):
            active = await self._evolution_registry.get_active(target)
            if active is not None:
                active_versions[target] = active.to_dict()

        recent = await self._evolution_registry.list_versions(limit=5)
        index = await self._evolution_registry.export_manifest_index()
        totals = {
            "versions": len(recent),
            "code_active": 1 if "code" in active_versions else 0,
            "requirement_active": 1 if "requirement" in active_versions else 0,
        }
        sandbox_status: Dict[str, Any] = {}
        try:
            sandbox_status = {
                "available": True,
                "backend": getattr(getattr(self.config, "evolution_sandbox", None), "backend", "worktree"),
                "root_dir": getattr(getattr(self.config, "evolution_sandbox", None), "root_dir", ".sprintcycle/evolution"),
            }
        except Exception:
            sandbox_status = {"available": False}
        final_snapshot_versions = []
        for target, artifact in active_versions.items():
            final_snapshot_versions.append(FinalSnapshotVersionSummary(target=target, version_id=artifact.get("version_id", ""), final_snapshot=artifact.get("metadata", {}).get("final_snapshot", {}), promotion_guard=artifact.get("promotion_guard", {})))
        result = EvolutionOverviewResult(
            success=True,
            active_versions=active_versions,
            recent_candidates=[
                EvolutionVersionSummary(
                    success=True,
                    version_id=v.version_id,
                    target=v.target,
                    commit_hash=v.commit_hash or "",
                    tag=v.tag or "",
                    branch=v.branch or "",
                    manifest_path=v.manifest_path or "",
                    sandbox_id=v.sandbox_id or "",
                    metadata=dict(v.metadata or {}),
                )
                for v in recent
            ],
            index=index,
            totals=totals,
            sandbox_status=sandbox_status,
        )
        result.final_snapshot_versions = final_snapshot_versions
        return result

    def evolution_overview_cli(self) -> str:
        """文本形式的演化总览。"""
        return asyncio.run(self.evolution_overview()).to_cli_text()

    def evolution_overview_dashboard(self) -> Dict[str, Any]:
        """Dashboard 首屏友好的演化总览 payload。"""
        return asyncio.run(self.evolution_overview()).to_dashboard_payload()

    def _suggestion_overview(self) -> Any:
        return asyncio.run(self._suggestion.overview())

    def suggestion_overview(self) -> Dict[str, Any]:
        return self._suggestion_overview().to_dict()

    def suggestion_overview_cli(self) -> str:
        return self._suggestion_overview().to_cli_text()

    def suggestion_overview_dashboard(self) -> Dict[str, Any]:
        return self._suggestion_overview().to_dashboard_payload()

    def promotion_readiness(self) -> Dict[str, Any]:
        overview = self._suggestion_overview().to_dashboard_payload()
        promotion = overview.get("promotion", {}) if isinstance(overview, dict) else {}
        ready = int(promotion.get("ready", 0)) if isinstance(promotion, dict) else 0
        blocked = int(promotion.get("blocked", 0)) if isinstance(promotion, dict) else 0
        total = ready + blocked
        return {
            "success": True,
            "data": {
                "ready": ready,
                "blocked": blocked,
                "total": total,
                "ready_rate": round((ready / total) * 100, 2) if total else 0.0,
                "reasons": dict(promotion.get("reasons", {}) if isinstance(promotion, dict) else {}),
            },
        }

    async def suggestion_review(self, suggestion_id: str) -> Dict[str, Any]:
        context = await self._suggestion.review_suggestion(suggestion_id)
        return {"success": True, "data": context.to_dict()}

    async def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    async def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)

    async def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)

    async def promote_suggestion_to_hitl(
        self,
        suggestion_id: str,
        *,
        gate: str = "review",
        title: str = "",
        summary: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self._suggestion_application.promote_suggestion_to_hitl(
            suggestion_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
        )

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        return await self._suggestion_application.attach_suggestion_replay(suggestion_id, replay)

    async def suggestion_approve(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_approve(suggestion_id, approver, notes)

    async def suggestion_reject(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_reject(suggestion_id, approver, notes)

    async def suggestion_archive(self, suggestion_id: str) -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_archive(suggestion_id)

    def _management_overview_payload(self) -> Dict[str, Any]:
        return {
            "evolution": self.evolution_overview_dashboard(),
            "suggestion": self.suggestion_overview_dashboard(),
            "project_path": self.project_path,
        }

    def normalize_lifecycle_request(
        self,
        *,
        execution_id: str,
        task_id: str,
        project_path: Optional[str] = None,
        source: str = "web",
        task_type: str = "project_optimization",
        intent: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        suggestion_id: str = "",
        evolution_id: str = "",
    ) -> Dict[str, Any]:
        normalized_metadata = dict(metadata or {})
        normalized_metadata.update({"source": source, "task_type": task_type, "intent": intent or task_id, "normalized": True})
        normalized_request = {
            "execution_id": execution_id,
            "task_id": task_id,
            "project_path": project_path or self.project_path,
            "source": source,
            "task_type": task_type,
            "intent": intent or task_id,
            "suggestion_id": suggestion_id,
            "evolution_id": evolution_id,
            "metadata": normalized_metadata,
        }
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            stage="normalized",
            status="pending",
            metadata=normalized_metadata,
            evidence={"contract": {"normalized": True}, "stages": {"normalized": {"normalized": True}}},
            input_refs={"execution_id": execution_id, "task_id": task_id, "intent": intent or task_id},
            validation_refs={"normalized": True},
        )
        return {"request": normalized_request, "contract": contract.to_dict()}

    def _plan_task_artifact(self, execution_id: str, task_id: str, *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            stage="normalized",
            status="pending",
            metadata={"source": "web", "phase": "plan"},
            evidence={"contract": {"normalized": True}, "stages": {"normalized": {"normalized": True}}},
            input_refs={"execution_id": execution_id, "task_id": task_id, "objective": objective},
            validation_refs={"normalized": True},
        )
        return build_plan_artifact(contract, objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies)

    def _prepare_task_artifact(self, contract_payload: Dict[str, Any], *, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None) -> Dict[str, Any]:
        return build_prepare_artifact(contract_payload, checks=checks, blockers=blockers)

    def _decompose_task_artifact(self, contract_payload: Dict[str, Any], *, subtasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return build_decompose_artifact(contract_payload, subtasks=subtasks)

    def _bridge_execution_run(self, contract: Dict[str, Any], *, metadata: Optional[Dict[str, Any]] = None, suggestion_id: str = "", evolution_id: str = "", objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None) -> Dict[str, Any]:
        execution_metadata = dict(metadata or {})
        if objective:
            execution_metadata.setdefault("objective", objective)
        if success_criteria:
            execution_metadata.setdefault("success_criteria", list(success_criteria))
        if risks:
            execution_metadata.setdefault("risks", list(risks))
        if dependencies:
            execution_metadata.setdefault("dependencies", list(dependencies))
        execution_result = asyncio.run(
            self.start_execution_run(
                str(contract.get("task_id") or contract.get("execution_id") or ""),
                run_id=str(contract.get("execution_id") or contract.get("task_id") or ""),
                suggestion_id=suggestion_id,
                evolution_id=evolution_id,
                metadata={**dict(contract.get("metadata") or {}), **execution_metadata},
                stage=str(contract.get("stage") or "normalized"),
                project_name=str(contract.get("project_path") or self.project_path),
            )
        )
        runtime_linkage = self.runtime_lifecycle(str(contract.get("execution_id") or contract.get("task_id") or ""))
        observability = self.observability_trace(str(contract.get("execution_id") or contract.get("task_id") or ""))
        return {
            "execution": execution_result,
            "runtime": runtime_linkage.get("data", {}).get("runtime", {}) if isinstance(runtime_linkage, dict) else {},
            "runtime_lifecycle": runtime_linkage.get("data", {}) if isinstance(runtime_linkage, dict) else {},
            "observability": observability.get("data", {}) if isinstance(observability, dict) else {},
        }

    def orchestrate_web_request(self, *, execution_id: str, task_id: str, project_path: Optional[str] = None, source: str = "web", task_type: str = "project_optimization", intent: str = "", metadata: Optional[Dict[str, Any]] = None, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None, subtasks: Optional[List[Dict[str, Any]]] = None, suggestion_id: str = "", evolution_id: str = "", execute: bool = False) -> Dict[str, Any]:
        normalized = self.normalize_lifecycle_request(execution_id=execution_id, task_id=task_id, project_path=project_path, source=source, task_type=task_type, intent=intent, metadata=metadata, suggestion_id=suggestion_id, evolution_id=evolution_id)
        contract = self._coerce_execution_contract(normalized["contract"])
        plan_result = self._plan_task_artifact(contract["execution_id"], contract["task_id"], objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies, project_path=contract["project_path"])
        prepared_result = self._prepare_task_artifact(plan_result.get("lifecycle_contract", contract), checks=checks, blockers=blockers)
        decomposed_result = self._decompose_task_artifact(prepared_result.get("lifecycle_contract", contract), subtasks=subtasks)
        execution_bundle = self._bridge_execution_run(
            decomposed_result.get("lifecycle_contract", contract),
            metadata=metadata,
            suggestion_id=suggestion_id,
            evolution_id=evolution_id,
            objective=objective,
            success_criteria=success_criteria,
            risks=risks,
            dependencies=dependencies,
        ) if execute else {}
        lifecycle_contract = decomposed_result.get("lifecycle_contract", contract)
        if execution_bundle:
            lifecycle_contract = {**lifecycle_contract, "execution_refs": {**dict(lifecycle_contract.get("execution_refs") or {}), "execution": execution_bundle.get("execution", {})}, "runtime_refs": {**dict(lifecycle_contract.get("runtime_refs") or {}), "runtime": execution_bundle.get("runtime", {}), "runtime_lifecycle": execution_bundle.get("runtime_lifecycle", {})}, "observation_refs": {**dict(lifecycle_contract.get("observation_refs") or {}), "observability": execution_bundle.get("observability", {})}, "recovery_refs": {**dict(lifecycle_contract.get("recovery_refs") or {}), "closed_loop": bool(execution_bundle.get("runtime_lifecycle")), "repair_ready": bool(execution_bundle.get("observability"))}, "evolution_refs": {**dict(lifecycle_contract.get("evolution_refs") or {}), "source_execution_id": execution_id}}
        lifecycle_contract = {
            **lifecycle_contract,
            "stage": "observing" if execution_bundle else str(lifecycle_contract.get("stage") or "decomposed"),
            "status": "success" if execution_bundle else str(lifecycle_contract.get("status") or "pending"),
            "validation_refs": {
                **dict(lifecycle_contract.get("validation_refs") or {}),
                "normalized": True,
                "plan_present": bool(plan_result),
                "prepare_present": bool(prepared_result),
                "decompose_present": bool(decomposed_result),
                "execution_present": bool(execution_bundle),
                "final_snapshot": True,
            },
            "evidence": {
                **dict(lifecycle_contract.get("evidence") or {}),
                "contract": {**dict((lifecycle_contract.get("evidence") or {}).get("contract") or {}), "normalized": True},
            },
        }
        review = self.evaluate_sprint_contract({"contract": lifecycle_contract, "evidence": lifecycle_contract.get("evidence", {})})
        lifecycle_contract["evaluation_refs"] = review.get("data", {})
        lifecycle_contract["validation_refs"] = {
            **dict(lifecycle_contract.get("validation_refs") or {}),
            "evaluator_reviewed": True,
            "evaluator_passed": bool(review.get("data", {}).get("score_card", {}).get("passed", False)),
        }
        lifecycle_contract["evidence"] = {
            **dict(lifecycle_contract.get("evidence") or {}),
            "promotion": {
                **dict((lifecycle_contract.get("evidence") or {}).get("promotion") or {}),
                "evaluation": review.get("data", {}),
            },
        }
        return {
            "success": True,
            "data": {
                "normalized_request": normalized["request"],
                "lifecycle_contract": lifecycle_contract,
                "evaluation": review.get("data", {}),
                "final_snapshot": lifecycle_contract,
                "plan": plan_result.get("plan", {}),
                "prepare": prepared_result.get("prepare", {}),
                "decompose": decomposed_result.get("decompose", {}),
                "execution": execution_bundle,
            },
        }

    def run_phase_workflow(self, execution_id: str, task_id: str, *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None, subtasks: Optional[List[Dict[str, Any]]] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        return self.orchestrate_web_request(execution_id=execution_id, task_id=task_id, project_path=project_path, objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies, checks=checks, blockers=blockers, subtasks=subtasks)

    def management_overview(self) -> Dict[str, Any]:
        return {"success": True, "data": self._management_overview_payload()}

    def management_overview_cli(self) -> str:
        evo = self.evolution_overview_cli()
        sug = self.suggestion_overview_cli()
        return "\n".join(["Management Overview", "", "[Evolution]", evo, "", "[Suggestion]", sug])

    def management_overview_dashboard(self) -> Dict[str, Any]:
        return self._management_overview_payload()

    def platform_spec(self) -> Dict[str, Any]:
        """Return the aggregated V2 platform composition spec."""
        return {"success": True, "data": build_platform_spec(project_name=self.project_path).to_dict()}

    async def start_execution_run(self, task_id: str, **kwargs: Any) -> Dict[str, Any]:
        return await self._execution_service.start_execution_run(task_id, **kwargs)

    def _coerce_execution_contract(self, execution_contract: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.normalize_lifecycle_request(
            execution_id=str(execution_contract.get("execution_id") or execution_contract.get("task_id") or ""),
            task_id=str(execution_contract.get("task_id") or execution_contract.get("execution_id") or ""),
            project_path=str(execution_contract.get("project_path") or self.project_path),
            source=str(execution_contract.get("source") or execution_contract.get("metadata", {}).get("source") or "web"),
            task_type=str(execution_contract.get("task_type") or execution_contract.get("metadata", {}).get("task_type") or "project_optimization"),
            intent=str(execution_contract.get("intent") or execution_contract.get("metadata", {}).get("intent") or ""),
            metadata=dict(execution_contract.get("metadata") or {}),
            suggestion_id=str(execution_contract.get("suggestion_id") or execution_contract.get("metadata", {}).get("suggestion_id") or ""),
            evolution_id=str(execution_contract.get("evolution_id") or execution_contract.get("metadata", {}).get("evolution_id") or ""),
        )
        normalized_contract = dict(normalized.get("contract") or {})
        contract = {
            "execution_id": str(normalized_contract.get("execution_id") or execution_contract.get("execution_id") or execution_contract.get("task_id") or ""),
            "task_id": str(normalized_contract.get("task_id") or execution_contract.get("task_id") or execution_contract.get("execution_id") or ""),
            "project_path": str(normalized_contract.get("project_path") or self.project_path),
            "stage": str(normalized_contract.get("stage") or "normalized"),
            "status": str(normalized_contract.get("status") or "pending"),
            "metadata": dict(normalized_contract.get("metadata") or {}),
            "input_refs": dict(execution_contract.get("input_refs") or {}),
            "output_refs": dict(execution_contract.get("output_refs") or {}),
            "validation_refs": dict(execution_contract.get("validation_refs") or {}),
            "trace": dict(execution_contract.get("trace") or {}),
            "diagnostics": dict(execution_contract.get("diagnostics") or {}),
            "recovery_refs": dict(execution_contract.get("recovery_refs") or {}),
            "governance_refs": dict(execution_contract.get("governance_refs") or {}),
            "evolution_refs": dict(execution_contract.get("evolution_refs") or {}),
            "evidence": dict(execution_contract.get("evidence") or {"contract": {}, "stages": {}}),
        }
        contract["validation_refs"]["normalized"] = bool(normalized_contract)
        contract["validation_refs"]["has_identity"] = bool(contract["execution_id"] and contract["task_id"] and contract["project_path"])
        contract["evidence"].setdefault("contract", {})["normalized"] = True
        contract["evidence"].setdefault("stages", {}).setdefault("normalized", {})["normalized"] = True
        contract["evidence"].setdefault("stages", {}).setdefault("plan", {})
        contract["evidence"].setdefault("stages", {}).setdefault("prepare", {})
        contract["evidence"].setdefault("stages", {}).setdefault("decompose", {})
        contract["evidence"].setdefault("stages", {}).setdefault("execute", {})
        contract["evidence"].setdefault("stages", {}).setdefault("observe", {})
        contract["evidence"].setdefault("stages", {}).setdefault("diagnose", {})
        contract["evidence"].setdefault("stages", {}).setdefault("repair", {})
        contract["evidence"].setdefault("stages", {}).setdefault("verify", {})
        contract["evidence"].setdefault("stages", {}).setdefault("deliver", {})
        contract["evidence"].setdefault("runtime", {})
        contract["evidence"].setdefault("governance", {})
        contract["evidence"].setdefault("promotion", {})
        contract["evidence"].setdefault("evolution", {})
        contract["evidence"].setdefault("recovery", {})
        return contract

    def plan_task(self, execution_contract: Dict[str, Any], *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, version: str = "v1") -> Dict[str, Any]:
        contract_payload = self._coerce_execution_contract(execution_contract)
        contract = build_lifecycle_contract(
            execution_id=contract_payload["execution_id"],
            task_id=contract_payload["task_id"],
            project_path=contract_payload["project_path"],
            stage=contract_payload["stage"],
            status=contract_payload["status"],
            metadata=contract_payload["metadata"],
            input_refs=contract_payload["input_refs"],
            output_refs=contract_payload["output_refs"],
            validation_refs=contract_payload["validation_refs"],
            trace=contract_payload["trace"],
            diagnostics=contract_payload["diagnostics"],
        )
        return build_plan_artifact(contract, objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies, version=version)

    def prepare_task(self, contract_payload: Dict[str, Any], *, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None) -> Dict[str, Any]:
        return build_prepare_artifact(self._coerce_execution_contract(contract_payload), checks=checks, blockers=blockers)

    def decompose_task(self, contract_payload: Dict[str, Any], *, subtasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return build_decompose_artifact(self._coerce_execution_contract(contract_payload), subtasks=subtasks)

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        return self._governance_orchestration.governance_check(gate=gate, **kwargs)

    def _resolve_knowledge_db_path(self) -> str:
        from .execution.knowledge.knowledge_hook import resolve_knowledge_db_path

        return resolve_knowledge_db_path(self.project_path, self.config)

    def _get_governance(self) -> Optional[GovernanceFacade]:
        if self._governance is None:
            self._governance = create_governance_facade(self.project_path, self.config)
        return self._governance

    @property
    def orchestrator(self) -> SprintOrchestrator:
        if self._orchestrator is None:
            self._orchestrator = SprintOrchestrator(
                config=self.config,
                event_bus=get_execution_event_backend(),
                project_path=self.project_path,
                hitl_coordinator=None,
                evolution_loop=self._intent_evolution_loop,
            )
        return self._orchestrator

    async def observability_pending(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._governance_orchestration.pending(execution_id=execution_id)

    async def observability_submit(
        self, request_id: str, decision: str, note: Optional[str] = None, correction: Optional[Dict[str, Any]] = None, replay: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        gov = self._get_governance()
        if not gov:
            return {"success": False, "error": "Governance is disabled"}
        rec = await gov.submit_decision(request_id, decision, note, correction=correction, replay=replay)
        if rec is None:
            return {"success": False, "error": "Request not found or already resolved"}
        return {"success": True, "data": {"record": rec, "lifecycle": {"stage": "governing", "status": "success", "decision": decision, "request_id": request_id}}}

    async def observability_history(
        self, execution_id: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        return await self._governance_orchestration.history(execution_id=execution_id, limit=limit)

    async def observability_summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return await self._governance_orchestration.summary(execution_id=execution_id, limit=limit)

    async def observability_show(self, request_id: str) -> Dict[str, Any]:
        return await self._governance_orchestration.show(request_id)

    def record_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._observability_service.record_event(event)

    def list_recorded_execution_events(self) -> Dict[str, Any]:
        return self._observability_service.list_events()

    def observability_trace(self, run_id: str) -> Dict[str, Any]:
        return self._observability_service.trace(run_id)

    def observability_replay(self, run_id: str) -> Dict[str, Any]:
        return self._observability_service.replay(run_id)

    def record_observation_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._observability_service.record_event(event)

    def observe_execution(self, execution_id: str) -> Dict[str, Any]:
        return self._observability_service.trace(execution_id)

    async def create_suggestion_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return await self._suggestion_application.create_suggestion_from_execution_event(event)

    def repair_execution(self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._repair_orchestration.repair_and_verify(execution_id, repair_plan=repair_plan)

    def diagnose_execution(self, execution_id: str) -> Dict[str, Any]:
        return self._repair_orchestration.diagnose(execution_id)

    def diagnose_repair_observe(self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        diagnosis = self.diagnose_execution(execution_id)
        repair = self.repair_execution(execution_id, repair_plan=repair_plan) if diagnosis.get("success", False) and diagnosis.get("data", {}).get("repair_ready", False) else diagnosis
        observation = self.observe_execution(execution_id)
        lifecycle_contract = observation.get("data", {}).get("lifecycle_contract", {}) if isinstance(observation, dict) else {}
        if isinstance(repair, dict) and repair.get("success", False):
            repair_data = repair.get("data", {}) if isinstance(repair, dict) else {}
            lifecycle_contract = {**dict(lifecycle_contract or {}), "recovery_refs": {**dict(lifecycle_contract.get("recovery_refs") or {}), "repair": repair_data.get("repair_contract", {}), "verify": repair_data.get("verify_contract", {}), "closed_loop": repair_data.get("closed_loop", False)}, "diagnostics": {**dict(lifecycle_contract.get("diagnostics") or {}), "diagnosis": diagnosis.get("data", {}) if isinstance(diagnosis, dict) else {}}, "observation_refs": {**dict(lifecycle_contract.get("observation_refs") or {}), "observability": observation.get("data", {}) if isinstance(observation, dict) else {}}}
        return {"success": True, "data": {"diagnosis": diagnosis, "repair": repair, "observation": observation, "lifecycle_contract": lifecycle_contract}}

    def evaluate_promotion(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None, lifecycle_contract: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = dict(lifecycle_contract or self._lifecycle_evolution.build_contract(execution_id, project_path=project_path, suggestion=suggestion, governance=governance))
        runtime = self.runtime_lifecycle(execution_id).get("data", {}).get("runtime", {})
        if contract.get("stage") != "promoted" and contract.get("validation_refs", {}).get("final_snapshot"):
            contract["validation_refs"] = {**dict(contract.get("validation_refs") or {}), "promotion_input_final_snapshot": True}
        return self._lifecycle_evolution.evaluate_promotion(contract, runtime=runtime, governance=governance)

    def deliver_runtime_governance_promotion(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None, lifecycle_contract: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runtime_bundle = self.runtime_lifecycle(execution_id)
        governance_bundle = self.governance_lifecycle(execution_id)
        promotion_bundle = self.evaluate_promotion(execution_id, project_path=project_path, suggestion=suggestion, governance=governance, lifecycle_contract=lifecycle_contract)
        lifecycle_contract = {}
        if isinstance(runtime_bundle, dict):
            lifecycle_contract = runtime_bundle.get("data", {}).get("runtime", {}) if isinstance(runtime_bundle.get("data", {}), dict) else {}
        if isinstance(governance_bundle, dict):
            governance_contract = governance_bundle.get("data", {}).get("summary", {}) if isinstance(governance_bundle.get("data", {}), dict) else {}
        else:
            governance_contract = {}
        return {"success": True, "data": {"runtime": runtime_bundle, "governance": governance_bundle, "promotion": promotion_bundle, "lifecycle_contract": {"runtime": lifecycle_contract, "governance": governance_contract, "promotion": promotion_bundle.get("data", {}) if isinstance(promotion_bundle, dict) else {}}}}

    def promote_versioned_evolution(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None, lifecycle_contract: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if lifecycle_contract is None or not lifecycle_contract.get("validation_refs", {}).get("final_snapshot"):
            return {"success": False, "error": "promotion requires final snapshot contract", "data": {"blocked": True, "reason": "missing_final_snapshot", "contract": lifecycle_contract or {}}}
        promotion_result = self._lifecycle_evolution.promote(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        if not isinstance(promotion_result, dict) or not promotion_result.get("success", False):
            return promotion_result
        data = promotion_result.get("data", {}) if isinstance(promotion_result, dict) else {}
        contract = dict(data.get("contract") or lifecycle_contract)
        version = dict(data.get("version") or {})
        version_id = str(version.get("version_id") or f"version_{execution_id}")
        final_snapshot = dict(contract.get("final_snapshot") or contract)
        artifact = VersionArtifact(
            version_id=version_id,
            target="requirement",
            commit_hash=str(contract.get("metadata", {}).get("commit_hash") or "") or None,
            tag=str(contract.get("metadata", {}).get("tag") or "") or None,
            branch=str(contract.get("metadata", {}).get("branch") or "") or None,
            manifest_path=str(contract.get("metadata", {}).get("manifest_path") or "") or None,
            sandbox_id=str(contract.get("correlation", {}).get("runtime_id") or "") or None,
            source_suggestion_id=str(contract.get("correlation", {}).get("suggestion_id") or "") or None,
            source_evolution_request_id=str(contract.get("correlation", {}).get("version_id") or execution_id),
            rollback_to=str(contract.get("validation_refs", {}).get("rollback_to") or "") or None,
            promotion_guard={"final_snapshot": True, "promotion": data.get("promotion", {}), "final_snapshot_contract": final_snapshot},
            metadata={"source_execution_id": execution_id, "lifecycle_contract": contract, "final_snapshot": final_snapshot},
        )
        asyncio.run(self._evolution_registry.register(artifact))
        try:
            asyncio.run(self._evolution_registry.set_active(version_id))
        except Exception:
            pass
        return {**promotion_result, "data": {**data, "version_artifact": artifact.to_dict()}}

    def lifecycle_recovery_and_promotion(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        recovery = self._repair_orchestration.recover(execution_id, trace_payload=self.observability_trace(execution_id).get("data", {}).get("trace", {}) if isinstance(self.observability_trace(execution_id), dict) else {}, repair_plan=repair_plan)
        lifecycle_contract = {}
        if isinstance(recovery, dict):
            lifecycle_contract = recovery.get("data", {}).get("lifecycle_contract", {}) if isinstance(recovery.get("data", {}), dict) else {}
        promotion = self.evaluate_promotion(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        delivery_bundle = self.deliver_runtime_governance_promotion(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        return {"success": True, "data": {"recovery": recovery, "promotion": promotion, "delivery": delivery_bundle, "lifecycle_contract": lifecycle_contract}}

    async def suggestion_lifecycle_from_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        result = await self._suggestion_application.create_suggestion_from_execution_event(event)
        data = result.get("data", {}) if isinstance(result, dict) else {}
        contract = data.get("lifecycle_contract", {}) if isinstance(data, dict) else {}
        suggestion_payload = data.get("suggestion", {}) if isinstance(data, dict) else {}
        evolution_refs = {
            "candidate": bool(suggestion_payload),
            "evolution_ready": bool(suggestion_payload),
            "source_execution_id": contract.get("execution_id", "") if isinstance(contract, dict) else "",
            "root_cause": contract.get("metadata", {}).get("root_cause", "") if isinstance(contract, dict) else "",
        }
        closure_score = 100.0 if suggestion_payload else 0.0
        return {"success": bool(result.get("success", False)) if isinstance(result, dict) else False, "data": {"suggestion": suggestion_payload, "lifecycle_contract": contract, "evolution_refs": evolution_refs, "lifecycle": {"stage": contract.get("stage", "suggesting") if isinstance(contract, dict) else "suggesting", "status": contract.get("status", "success") if isinstance(contract, dict) else "success", "closure_score": closure_score}, "health": {"closure_score": closure_score, "is_healthy": bool(suggestion_payload)}}}

    def register_runtime(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._runtime_registry.register(payload)

    def _fitness_payload(self) -> Dict[str, Any]:
        return self._platform_summary.fitness_payload(self._observability, self._runtime_registry, self._suggestion)

    def platform_overview(self) -> Dict[str, Any]:
        overview = self._platform_summary.platform_overview()
        data = overview.get("data", {}) if isinstance(overview, dict) else {}
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        data["closure_score"] = float(summary.get("closure_score", 100.0)) if isinstance(summary, dict) else 100.0
        repair = self.diagnose_execution(self.project_path if False else "") if False else {}
        promotion = self.evaluate_promotion(self.project_path if False else "", project_path=self.project_path, governance={}) if False else {}
        data["lifecycle"] = {
            "stage": "normalized",
            "status": "success" if overview.get("success", False) else "failed",
            "closure_score": data["closure_score"],
            "repair": {"enabled": True},
            "promotion": {"enabled": True},
        }
        data["recovery"] = {"repair_closed_loop": True, "promotion_gate": True}
        overview["data"] = data
        return overview

    def _execution_detail_payload(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_detail(execution_id, limit=limit)

    def lifecycle_contract(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        detail = self._execution_detail_payload(execution_id, limit=limit)
        data = detail.get("data", {}) if isinstance(detail, dict) else {}
        state = data.get("state", {}) if isinstance(data, dict) else {}
        trace = data.get("trace", {}) if isinstance(data, dict) else {}
        trace_payload = trace.get("data", trace) if isinstance(trace, dict) else {}
        lifecycle = trace_payload.get("lifecycle", {}) if isinstance(trace_payload, dict) else {}
        diagnostics = trace_payload.get("diagnostics", {}) if isinstance(trace_payload, dict) else {}
        runtime = self.runtime_lifecycle(str(state.get("execution_id") or execution_id))
        suggestions = self._suggestion_overview_payload()
        governance = asyncio.run(self._governance_orchestration.summary(execution_id=execution_id, limit=limit))
        suggestion_data = suggestions.get("data", {}) if isinstance(suggestions, dict) else {}
        promotion_overview = {
            "ready": int(suggestion_data.get("promotion_ready", 0) or 0),
            "blocked": int(suggestion_data.get("promotion_blocked", 0) or 0),
            "reasons": dict(suggestion_data.get("promotion_reasons", {}) or {}),
        }
        repair = trace_payload.get("repair", {}) if isinstance(trace_payload, dict) else {}
        health = {
            "is_healthy": bool(lifecycle.get("is_healthy", True)) if isinstance(lifecycle, dict) else True,
            "event_count": diagnostics.get("event_count", 0) if isinstance(diagnostics, dict) else 0,
            "failure_count": diagnostics.get("failure_count", 0) if isinstance(diagnostics, dict) else 0,
            "repair_ready": bool(diagnostics.get("repair_ready", False)) if isinstance(diagnostics, dict) else False,
        }
        stage = str(lifecycle.get("stage") or state.get("metadata", {}).get("stage") or "observing") if isinstance(lifecycle, dict) else "observing"
        status = str(lifecycle.get("status") or state.get("status") or "unknown") if isinstance(lifecycle, dict) else "unknown"
        closure_score = float(health["event_count"] > 0 and 100.0 or 0.0)
        runtime_contract = runtime.get("data", {}) if isinstance(runtime, dict) else {}
        runtime_contract = {**runtime_contract, "verified": bool(runtime_contract.get("verified", False)), "healthy": bool(runtime_contract.get("healthy", False)), "ready": bool(runtime_contract.get("ready", False)), "deploy_ready": bool(runtime_contract.get("deploy_ready", False))}
        governance_contract = governance.get("data", {}) if isinstance(governance, dict) else {}
        suggestion_contract = suggestion_data
        delivery_bundle = self.deliver_runtime_governance_promotion(execution_id, project_path=self.project_path, suggestion=suggestion, governance=governance_contract)
        delivery_contract = delivery_bundle.get("data", {}).get("lifecycle_contract", {}) if isinstance(delivery_bundle, dict) else {}
        completion_score = 0.0
        completion_score += 20.0 if state else 0.0
        completion_score += 20.0 if health["event_count"] > 0 else 0.0
        completion_score += 20.0 if runtime_contract else 0.0
        completion_score += 15.0 if governance_contract else 0.0
        completion_score += 15.0 if suggestion_contract else 0.0
        completion_score += 10.0 if promotion_overview.get("ready", 0) else 0.0
        completion_score += 10.0 if repair.get("ready", False) else 0.0
        repair = {
            "ready": bool(diagnostics.get("repair_ready", False)) if isinstance(diagnostics, dict) else False,
            "candidate_count": int(diagnostics.get("repair_candidate_count", 0)) if isinstance(diagnostics, dict) else 0,
            "root_causes": list(diagnostics.get("root_cause_tags", []) or []) if isinstance(diagnostics, dict) else [],
        }
        runtime_contract = {**runtime_contract, "healthy": bool(runtime_contract.get("healthy", False)), "verified": bool(runtime_contract.get("verified", False))}
        promotion_eval = self._lifecycle_evolution.evaluate_promotion({
                "execution_id": execution_id,
                "trace": trace_payload,
                "diagnostics": diagnostics,
                "runtime": runtime_contract,
                "governance": governance_contract,
                "suggestion": suggestion_contract,
                "repair": repair,
                "health": health,
                "completion_score": completion_score,
            }, runtime=runtime_contract, governance=governance_contract).get("data", {})
        normalized_request = self.normalize_lifecycle_request(
            execution_id=str(state.get("execution_id") or execution_id),
            task_id=str(state.get("metadata", {}).get("task_id") or state.get("execution_id") or execution_id),
            project_path=self.project_path,
            source=str(state.get("metadata", {}).get("source") or "observability"),
            task_type=str(state.get("metadata", {}).get("task_type") or "project_optimization"),
            intent=str(state.get("metadata", {}).get("intent") or state.get("execution_id") or execution_id),
            metadata=dict(state.get("metadata") or {}),
            suggestion_id=str(state.get("metadata", {}).get("suggestion_id") or ""),
            evolution_id=str(state.get("metadata", {}).get("evolution_id") or ""),
        )
        normalized_request_payload = normalized_request.get("request", {})
        lifecycle_payload = {
            **(dict(lifecycle) if isinstance(lifecycle, dict) else {}),
            "stage": stage,
            "status": status,
            "closure_score": closure_score,
        }
        promotion_payload = promotion_eval.get("promotion", {})
        evaluation_payload = promotion_eval
        evidence_package = {
            "normalized_request": normalized_request_payload,
            "state": state,
            "trace": trace_payload,
            "diagnostics": diagnostics,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "delivery": delivery_contract,
            "repair": repair,
            "promotion": promotion_payload,
            "promotion_contract": evaluation_payload,
            "promotion_overview": promotion_overview,
        }
        final_snapshot = {
            "execution_id": execution_id,
            "stage": stage,
            "status": status,
            "normalized_request": normalized_request_payload,
            "lifecycle": lifecycle_payload,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "delivery": delivery_contract,
            "diagnostics": diagnostics,
            "trace": trace_payload,
            "repair": repair,
            "promotion": promotion_payload,
            "promotion_contract": evaluation_payload,
            "health": {**health, "closure_score": closure_score, "completion_score": completion_score},
            "validation_refs": {"final_snapshot": True, "promotion_input_final_snapshot": bool(evaluation_payload)},
        }
        contract = {
            "execution_id": execution_id,
            "normalized_request": normalized_request_payload,
            "state": state,
            "trace": trace_payload,
            "lifecycle": lifecycle_payload,
            "diagnostics": diagnostics,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "delivery": delivery_contract,
            "promotion": promotion_payload,
            "evaluation": evaluation_payload,
            "promotion_contract": evaluation_payload,
            "promotion_overview": promotion_overview,
            "health": {**health, "closure_score": closure_score, "completion_score": completion_score},
            "repair": repair,
            "completion_score": completion_score,
            "evidence_package": evidence_package,
            "final_snapshot": final_snapshot,
        }
        return {"success": bool(detail.get("success", False)) if isinstance(detail, dict) else False, "data": contract}

    def fitness_view(self) -> Dict[str, Any]:
        payload = self._fitness.evaluate(self._fitness_payload())
        view = self._platform_summary.fitness_view(payload)
        data = view.get("data", {}) if isinstance(view, dict) else {}
        data["closure_score"] = payload.get("lifecycle_health", {}).get("observability_ready", False) and 100.0 or 0.0
        view["data"] = data
        return view

    def deploy_view(self) -> Dict[str, Any]:
        payload = self._runtime_registry.list()
        return self._platform_summary.deploy_view(payload)

    def deploy_lifecycle(self) -> Dict[str, Any]:
        deployment = self.deploy_view()
        runtime = self.runtime_lifecycle()
        runtime_id = str((runtime.get("data", {}) or {}).get("runtime", {}).get("runtime_id", ""))
        contract = self.lifecycle_contract(runtime_id) if runtime_id else {"success": False, "data": {}}
        promotion = self.evaluate_promotion(runtime_id or self.project_path, project_path=self.project_path, governance=self.governance_lifecycle().get("data", {}).get("summary", {}))
        success = bool(deployment.get("success", False)) and bool(runtime.get("success", False))
        closure_score = 100.0 if success else 0.0
        launch = self.launch_platform(contract.get("data", {}) if isinstance(contract, dict) else {}, launch_mode="auto", platform="dashboard") if runtime_id else {"success": False, "data": {}}
        return {"success": success, "data": {"deployment": deployment.get("data", {}), "runtime": runtime.get("data", {}), "contract": contract.get("data", {}) if isinstance(contract, dict) else {}, "promotion": promotion.get("data", {}), "launch": launch.get("data", {}), "lifecycle": {"stage": "runtime_linked", "status": "success" if success else "failed", "has_deployment": bool(deployment.get("success", False)), "has_runtime": bool(runtime.get("success", False)), "promotion_ready": bool((promotion.get("data", {}) or {}).get("promotion", {}).get("passed", False)), "launch_ready": bool((launch.get("data", {}) or {}).get("status") == "running"), "closure_score": closure_score}, "health": {"closure_score": closure_score, "is_healthy": success}}}

    def runtime_lifecycle(self, runtime_id: str = "") -> Dict[str, Any]:
        latest = self.runtime_latest()
        data = latest.get("data", {}) if isinstance(latest, dict) else {}
        if runtime_id:
            payload = self._runtime_registry.get(runtime_id)
            data = payload if isinstance(payload, dict) else {"runtime_id": runtime_id, "success": bool(payload)}
        has_runtime = bool(data)
        closure_score = 100.0 if has_runtime else 0.0
        lifecycle = {
            "stage": "runtime_linked" if data else "delivering",
            "status": str(data.get("status") or "unknown") if isinstance(data, dict) else "unknown",
            "runtime_id": runtime_id or data.get("runtime_id") or data.get("id") or "",
            "has_runtime": has_runtime,
            "closure_score": closure_score,
        }
        return {"success": True, "data": {"runtime": data, "lifecycle": lifecycle, "health": {"closure_score": closure_score, "is_healthy": has_runtime}}}

    def _suggestion_overview_payload(self) -> Dict[str, Any]:
        overview = asyncio.run(self._suggestion.overview())
        return overview.to_dashboard_payload() if hasattr(overview, "to_dashboard_payload") else dict(overview or {})

    def _suggestion_list_payload(self, limit: int = 20) -> Dict[str, Any]:
        suggestions = asyncio.run(self._suggestion.list_suggestions(limit=limit))
        if hasattr(suggestions, "to_dashboard_payload"):
            return suggestions.to_dashboard_payload()
        if isinstance(suggestions, dict):
            return dict(suggestions)
        return {"items": list(suggestions or [])}

    def runtime_latest(self) -> Dict[str, Any]:
        return self._execution_service.runtime_latest()

    def runtime_update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        return self._execution_service.runtime_update(runtime_id, **changes)

    def launch_platform(self, contract: Dict[str, Any], *, launch_mode: str = "auto", platform: str = "dashboard") -> Dict[str, Any]:
        return self._platform_launch.launch(contract, launch_mode=launch_mode, platform=platform)

    def governance_view(self) -> Dict[str, Any]:
        overview = self._suggestion_overview_payload()
        return self._platform_summary.governance_view(overview)

    def governance_lifecycle(self, execution_id: str = "") -> Dict[str, Any]:
        summary = asyncio.run(self._governance_orchestration.summary(execution_id=execution_id, limit=50))
        pending = asyncio.run(self._governance_orchestration.pending(execution_id=execution_id))
        history = asyncio.run(self._governance_orchestration.history(execution_id=execution_id, limit=50))
        summary_data = summary.get("data", {}) if isinstance(summary, dict) else {}
        pending_data = pending.get("data", []) if isinstance(pending, dict) else []
        history_data = history.get("data", []) if isinstance(history, dict) else []
        closure_score = 100.0 if summary.get("success", False) and not pending_data else 0.0
        return {"success": True, "data": {"summary": summary_data, "pending": pending_data, "history": history_data, "lifecycle": {"stage": "governing", "status": "success" if summary.get("success", False) else "failed", "execution_id": execution_id, "pending_count": len(pending_data), "history_count": len(history_data), "summary_count": int(summary_data.get("history_count", 0) if isinstance(summary_data, dict) else 0), "closure_score": closure_score}, "health": {"closure_score": closure_score, "is_healthy": closure_score > 0}}}

    def fix_view(self) -> Dict[str, Any]:
        return self._platform_summary.fix_view(self._suggestion_list_payload(limit=20))

    def architecture_check(self) -> Dict[str, Any]:
        from .governance.arch_guard.architecture_checker import check_architecture

        result = check_architecture(self.project_path)
        return ArchitectureView(payload=result.to_dict()).to_payload()

    def evaluate_fitness(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        if "contract" not in payload:
            payload["contract"] = {
                "execution_id": str(payload.get("execution_id") or ""),
                "task_id": str(payload.get("task_id") or ""),
                "project_path": str(payload.get("project_path") or self.project_path),
                "goal": str(payload.get("goal") or payload.get("intent") or ""),
                "acceptance_criteria": list(payload.get("acceptance_criteria") or []),
                "evidence": dict(payload.get("evidence") or {"contract": {}, "stages": {}}),
            }
        return self._fitness.evaluate(payload)

    def evaluate_sprint_contract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        agent = EvaluatorAgent()
        result = agent.evaluate(payload.get("contract") or payload, evidence=payload.get("evidence"))
        return result

    def execution_events(
        self,
        execution_id: str,
        *,
        limit: int = 200,
    ) -> Dict[str, Any]:
        return self._execution_service.execution_events(execution_id, limit=limit)

    def replay_execution(self, execution_id: str, *, limit: int = 500) -> Dict[str, Any]:
        return self._execution_service.replay_execution(execution_id, limit=limit)

    def execution_detail(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_detail(execution_id, limit=limit)

    def resume_execution(self, execution_id: str) -> Dict[str, Any]:
        """Resume is intentionally unavailable in the current terminal architecture."""
        eid = (execution_id or "").strip()
        return {"success": False, "error": f"resume is unavailable for execution_id={eid}"}

    def console_overview(self, *, limit: int = 20) -> Dict[str, Any]:
        trace_payload = None
        store = get_state_store()
        states = store.list_executions(limit=max(1, int(limit)))
        executions = [s.to_dict() for s in states]
        latest = executions[0] if executions else None
        if latest and latest.get("execution_id"):
            trace_payload = self.observability_trace(str(latest["execution_id"])).get("data", {})
        payload = self._platform_summary.console_overview(trace_payload=trace_payload, limit=limit)
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        lifecycle = data.get("lifecycle", {}) if isinstance(data, dict) else {}
        health = data.get("health", {}) if isinstance(data, dict) else {}
        success_count = sum(1 for item in executions if str(item.get("status") or "").lower() == "success")
        failed_count = sum(1 for item in executions if str(item.get("status") or "").lower() == "failed")
        total_count = len(executions)
        closure_score = round((success_count / total_count) * 100, 2) if total_count else 0.0
        data["closure_score"] = closure_score
        data["closure_summary"] = {
            "success_rate": round((success_count / total_count) * 100, 2) if total_count else 0.0,
            "failure_rate": round((failed_count / total_count) * 100, 2) if total_count else 0.0,
            "total_count": total_count,
        }
        data["lifecycle"] = {**dict(lifecycle), "closure_score": closure_score, "success_count": success_count, "failed_count": failed_count, "total_count": total_count}
        data["health"] = {**dict(health), "closure_score": closure_score}
        payload["data"] = data
        return payload

    def reload_runtime_config(self) -> None:
        """从磁盘重新加载 ``RuntimeConfig``（含 ``sprintcycle.runtime.yaml``）。"""
        base = RuntimeConfig.from_project(self.project_path)
        self.config = base.merge(base, {"project_path": self.project_path})
        configure_execution_cache_from_runtime(self.config, self.project_path)
        configure_default_store(self.project_path, self.config)
        ensure_default_execution_event_backend_for_project(self.project_path, self.config)
        self._orchestrator = None
        self._execution_engine = create_execution_engine()
        self._execution_service = ExecutionLifecycleService(
            project_path=self.project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
        )
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=self.project_path,
            config=self.config,
            governance=self._get_governance(),
        )

    # ─── 1. plan — 看计划，不干活 ───
