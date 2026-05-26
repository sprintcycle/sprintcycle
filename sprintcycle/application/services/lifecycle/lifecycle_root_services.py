"""LifecycleRoot 聚合根的应用层服务。

完全替代旧 API 的新架构实现，保持业务逻辑完整。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
    LifecycleStateMachineService,
    StageEvidence,
)


@dataclass
class LifecycleRootService:
    """LifecycleRoot 聚合根的应用层服务 - 完整替代旧 API。"""

    project_path: str

    def create_lifecycle(
        self,
        *,
        execution_id: str,
        task_id: str,
        project_path: Optional[str] = None,
        task_type: str = "project_optimization",
        intent: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LifecycleRoot:
        """创建新的生命周期。"""
        return create_lifecycle(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            task_type=task_type,
            intent=intent,
            metadata=metadata,
        )

    def build_lifecycle(
        self,
        *,
        execution_id: str,
        task_id: str,
        project_path: str,
        stage: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        failure_kind: str = "",
        failure_reason: str = "",
        delivery_refs: Optional[Dict[str, Any]] = None,
        runtime_refs: Optional[Dict[str, Any]] = None,
        suggestion_refs: Optional[List[Dict[str, Any]]] = None,
        skill_refs: Optional[List[Dict[str, Any]]] = None,
        skill_matches: Optional[List[Dict[str, Any]]] = None,
        skill_review_checklists: Optional[List[Dict[str, Any]]] = None,
        skill_trace: Optional[Dict[str, Any]] = None,
        evolution_refs: Optional[Dict[str, Any]] = None,
        evidence: Optional[Dict[str, Any]] = None,
        recovery_refs: Optional[Dict[str, Any]] = None,
        recovery_plan_refs: Optional[Dict[str, Any]] = None,
        governance_refs: Optional[Dict[str, Any]] = None,
        trace: Optional[Dict[str, Any]] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        correlation: Optional[Dict[str, Any]] = None,
        stage_history: Optional[List[Dict[str, Any]]] = None,
        allowed_next_stages: Optional[List[str]] = None,
        validation_refs: Optional[Dict[str, Any]] = None,
        input_refs: Optional[Dict[str, Any]] = None,
        output_refs: Optional[Dict[str, Any]] = None,
        transition_reason: str = "",
        failure_code: str = "",
    ) -> LifecycleRoot:
        """构建生命周期（兼容旧 API 的 build_lifecycle_contract 参数）。
        
        这是完全兼容旧 API 的新版本实现，内部使用 LifecycleRoot 聚合根。
        """
        from sprintcycle.domain.core.lifecycle import build_default_correlation, normalize_lifecycle_metadata
        
        meta = normalize_lifecycle_metadata(metadata)
        
        lifecycle = self.create_lifecycle(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path,
            task_type=str(meta.get("task_type") or "project_optimization"),
            intent=str(meta.get("intent") or ""),
            metadata=meta,
        )
        
        # 尝试转换到目标阶段
        service = LifecycleStateMachineService()
        try:
            target_stage = LifecycleStage.from_string(stage)
            if target_stage != lifecycle.stage:
                # 构建转换路径
                stages = list(LifecycleStage)
                start_idx = stages.index(lifecycle.stage)
                end_idx = stages.index(target_stage)
                for i in range(start_idx, end_idx):
                    next_stage = stages[i + 1]
                    if service.can_transition(lifecycle.stage.value, next_stage.value):
                        lifecycle = lifecycle.transition_to(next_stage)
        except Exception:
            # 如果转换失败，保持原样
            pass
        
        # 保存兼容引用到 metadata
        extra_metadata = dict(lifecycle.metadata)
        if delivery_refs:
            extra_metadata["delivery_refs"] = dict(delivery_refs)
        if runtime_refs:
            extra_metadata["runtime_refs"] = dict(runtime_refs)
        if suggestion_refs:
            extra_metadata["suggestion_refs"] = list(suggestion_refs)
        if skill_refs:
            extra_metadata["skill_refs"] = list(skill_refs)
        if skill_matches:
            extra_metadata["skill_matches"] = list(skill_matches)
        if skill_review_checklists:
            extra_metadata["skill_review_checklists"] = list(skill_review_checklists)
        if skill_trace:
            extra_metadata["skill_trace"] = dict(skill_trace)
        if evolution_refs:
            extra_metadata["evolution_refs"] = dict(evolution_refs)
        if recovery_refs:
            extra_metadata["recovery_refs"] = dict(recovery_refs)
        if recovery_plan_refs:
            extra_metadata["recovery_plan_refs"] = dict(recovery_plan_refs)
        if governance_refs:
            extra_metadata["governance_refs"] = dict(governance_refs)
        if trace:
            extra_metadata["trace"] = dict(trace)
        if diagnostics:
            extra_metadata["diagnostics"] = dict(diagnostics)
        if metrics:
            extra_metadata["metrics"] = dict(metrics)
        if validation_refs:
            extra_metadata["validation_refs"] = dict(validation_refs)
        if input_refs:
            extra_metadata["input_refs"] = dict(input_refs)
        if output_refs:
            extra_metadata["output_refs"] = dict(output_refs)
        
        # 处理证据
        if evidence and isinstance(evidence, dict):
            # 旧格式证据是 {stage: evidence_data}
            from sprintcycle.domain.core.lifecycle import ensure_lifecycle_evidence
            normalized_evidence = ensure_lifecycle_evidence(evidence)
            
            for stage_key, stage_data in normalized_evidence.get("stages", {}).items():
                stage_evidence = StageEvidence(
                    stage=stage_key,
                    present=True,
                    evidence=stage_data,
                )
                lifecycle = lifecycle.add_stage_evidence(stage_evidence)
        
        return lifecycle

    def advance_to_normalized(
        self,
        lifecycle: LifecycleRoot,
        *,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> LifecycleRoot:
        """将生命周期推进到 normalized 阶段。"""
        updated_lifecycle = lifecycle.transition_to(LifecycleStage.NORMALIZED)
        
        if evidence:
            stage_evidence = StageEvidence(
                stage=LifecycleStage.NORMALIZED.value,
                present=True,
                evidence=evidence,
            )
            updated_lifecycle = updated_lifecycle.add_stage_evidence(stage_evidence)
        
        return updated_lifecycle

    def advance_to_planned(
        self,
        lifecycle: LifecycleRoot,
        *,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> LifecycleRoot:
        """将生命周期推进到 planned 阶段。"""
        updated_lifecycle = lifecycle.transition_to(LifecycleStage.PLANNED)
        
        if evidence:
            stage_evidence = StageEvidence(
                stage=LifecycleStage.PLANNED.value,
                present=True,
                evidence=evidence,
            )
            updated_lifecycle = updated_lifecycle.add_stage_evidence(stage_evidence)
        
        return updated_lifecycle

    def advance_to_executing(
        self,
        lifecycle: LifecycleRoot,
    ) -> LifecycleRoot:
        """将生命周期推进到 executing 阶段。"""
        return lifecycle.transition_to(LifecycleStage.EXECUTING)

    def complete_execution(
        self,
        lifecycle: LifecycleRoot,
        *,
        success: bool = True,
    ) -> LifecycleRoot:
        """完成执行阶段。"""
        if success:
            lifecycle = lifecycle.transition_to(LifecycleStage.OBSERVING)
        
        return lifecycle

    def complete_lifecycle(
        self,
        lifecycle: LifecycleRoot,
        *,
        success: bool = True,
    ) -> LifecycleRoot:
        """完成整个生命周期。"""
        if success:
            try:
                lifecycle = lifecycle.transition_to(LifecycleStage.PROMOTED)
            except Exception:
                pass
        
        return lifecycle

    def lifecycle_to_dict(self, lifecycle: LifecycleRoot) -> Dict[str, Any]:
        """将 LifecycleRoot 转换为字典格式（完全兼容旧格式）。"""
        service = LifecycleStateMachineService()
        
        # 从 metadata 中提取兼容引用
        metadata = dict(lifecycle.metadata)
        
        return {
            "contract_id": lifecycle.contract_id,
            "execution_id": lifecycle.execution_id,
            "task_id": lifecycle.task_id,
            "project_path": lifecycle.project_path,
            "task_type": lifecycle.task_type,
            "intent": lifecycle.intent,
            "stage": lifecycle.stage.value,
            "status": lifecycle.status.value,
            "failure_kind": lifecycle.failure_kind,
            "failure_reason": lifecycle.failure_reason,
            "failure_code": lifecycle.failure_code,
            "transition_reason": lifecycle.transition_reason,
            "plan_refs": metadata.get("plan_refs", {}),
            "execution_refs": metadata.get("execution_refs", {}),
            "observation_refs": metadata.get("observation_refs", {}),
            "recovery_refs": metadata.get("recovery_refs", {}),
            "recovery_plan_refs": metadata.get("recovery_plan_refs", {}),
            "delivery_refs": metadata.get("delivery_refs", {}),
            "runtime_refs": metadata.get("runtime_refs", {}),
            "governance_refs": metadata.get("governance_refs", {}),
            "evolution_refs": metadata.get("evolution_refs", {}),
            "suggestion_refs": metadata.get("suggestion_refs", []),
            "skill_refs": metadata.get("skill_refs", []),
            "skill_matches": metadata.get("skill_matches", []),
            "skill_review_checklists": metadata.get("skill_review_checklists", []),
            "skill_trace": metadata.get("skill_trace", {}),
            "trace": metadata.get("trace", {}),
            "diagnostics": metadata.get("diagnostics", {}),
            "metrics": metadata.get("metrics", {}),
            "metadata": {k: v for k, v in metadata.items() if k not in [
                "plan_refs", "execution_refs", "observation_refs", 
                "recovery_refs", "recovery_plan_refs", "delivery_refs",
                "runtime_refs", "governance_refs", "evolution_refs",
                "suggestion_refs", "skill_refs", "skill_matches",
                "skill_review_checklists", "skill_trace", "trace",
                "diagnostics", "metrics"
            ]},
            "correlation": lifecycle.correlation.to_dict() if lifecycle.correlation else {},
            "stage_history": [
                {
                    "from": h.from_stage,
                    "to": h.to_stage,
                    "at": h.at,
                    "reason": h.reason,
                }
                for h in lifecycle.stage_history
            ],
            "allowed_next_stages": list(lifecycle.allowed_next_stages),
            "validation_refs": metadata.get("validation_refs", {}),
            "input_refs": metadata.get("input_refs", {}),
            "output_refs": metadata.get("output_refs", {}),
            "evidence": {
                ev.stage: ev.evidence
                for ev in lifecycle.evidence.stages.values()
            },
            "is_terminal": service.is_terminal(lifecycle.stage.value),
            "stage_index": service.stage_index(lifecycle.stage.value),
            "stage_hints": {
                "next_stage": service.next_stages(lifecycle.stage.value)[0] if service.next_stages(lifecycle.stage.value) else None,
                "failure_kind": lifecycle.failure_kind or "",
            },
            "plan_hints": metadata.get("plan_refs", {}),
            "execution_hints": metadata.get("execution_refs", {}),
            "observation_hints": metadata.get("observation_refs", {}),
            "recovery_hints": metadata.get("recovery_refs", {}),
            "recovery_plan_hints": metadata.get("recovery_plan_refs", {}),
            "delivery_hints": metadata.get("delivery_refs", {}),
            "runtime_hints": metadata.get("runtime_refs", {}),
            "governance_hints": metadata.get("governance_refs", {}),
            "evolution_hints": metadata.get("evolution_refs", {}),
        }


@dataclass
class WebLifecycleRootOrchestrationService:
    """Web 生命周期编排服务，直接使用新架构。"""

    project_path: str
    start_execution_run: Callable[..., Any]
    runtime_lifecycle: Callable[[str], Dict[str, Any]]
    observability_trace: Callable[[str], Dict[str, Any]]
    evaluate_sprint_contract: Callable[[Dict[str, Any]], Dict[str, Any]]

    def __post_init__(self):
        self._root_service = LifecycleRootService(self.project_path)

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
        """标准化 Web 生命周期请求。"""
        normalized_metadata = dict(metadata or {})
        normalized_metadata.update(
            {"source": source, "task_type": task_type, "intent": intent or task_id, "normalized": True}
        )
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
        
        lifecycle = self._root_service.create_lifecycle(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            task_type=task_type,
            intent=intent,
            metadata=normalized_metadata,
        )
        
        lifecycle = self._root_service.advance_to_normalized(lifecycle)
        
        return {"request": normalized_request, "contract": self._root_service.lifecycle_to_dict(lifecycle)}


__all__ = [
    "LifecycleRootService",
    "WebLifecycleRootOrchestrationService",
]
