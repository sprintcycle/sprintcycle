"""LifecycleRoot 聚合根的应用层服务。

完全替代旧 API 的新架构实现，保持业务逻辑完整。

**DDD 分层原则:**
- 应用层：事务编排、用例协调、DTO 转换
- 领域层：业务规则、状态转换、核心逻辑

本服务只做编排，核心业务逻辑委托给领域层服务。

**DTO Conversion:**
- Provides conversion between LifecycleRoot (domain) and LifecycleContract (DTO)
- Maintains backward compatibility with existing API contracts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    create_lifecycle,
    LifecycleStateMachine,
    StageEvidence,
    get_lifecycle_state_machine,
    LifecycleContract,
    ensure_lifecycle_evidence,
    normalize_lifecycle_metadata,
    LifecycleSubstage,
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
        reason: str = "",
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
        service = LifecycleStateMachine()
        try:
            target_substage = LifecycleSubstage.from_string(stage)
            if target_substage != lifecycle.substage:
                # 直接转换到目标子状态
                lifecycle = lifecycle.transition_to_substage(target_substage, reason=reason)
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
            normalized_evidence = ensure_lifecycle_evidence(evidence)
            
            for stage_key, stage_data in normalized_evidence.get("stages", {}).items():
                stage_evidence = StageEvidence(
                    stage=stage_key,
                    present=True,
                    evidence=stage_data,
                )
                lifecycle = lifecycle.add_stage_evidence(stage_evidence)
        
        return lifecycle

    def lifecycle_to_contract(self, lifecycle: LifecycleRoot) -> LifecycleContract:
        """将 LifecycleRoot 转换为 LifecycleContract DTO。
        
        用于与外部系统交互时的数据格式转换。
        """
        history = [
            {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
            for h in lifecycle.stage_history
        ]
        
        metadata = dict(lifecycle.metadata)
        
        return LifecycleContract(
            execution_id=lifecycle.execution_id,
            task_id=lifecycle.task_id,
            project_path=lifecycle.project_path,
            task_type=lifecycle.task_type,
            intent=lifecycle.intent,
            stage=lifecycle.substage.value,
            status=lifecycle.status.value,
            failure_kind=lifecycle.failure_kind,
            failure_reason=lifecycle.failure_reason,
            delivery_refs=dict(metadata.get("delivery_refs", {})),
            runtime_refs=dict(metadata.get("runtime_refs", {})),
            suggestion_refs=list(metadata.get("suggestion_refs", [])),
            skill_refs=list(metadata.get("skill_refs", [])),
            skill_matches=list(metadata.get("skill_matches", [])),
            skill_review_checklists=list(metadata.get("skill_review_checklists", [])),
            skill_trace=dict(metadata.get("skill_trace", {})),
            evolution_refs=dict(metadata.get("evolution_refs", {})),
            evidence=ensure_lifecycle_evidence(lifecycle.evidence.to_dict()),
            recovery_refs=dict(metadata.get("recovery_refs", {})),
            recovery_plan_refs=dict(metadata.get("recovery_plan_refs", {})),
            governance_refs=dict(metadata.get("governance_refs", {})),
            trace=dict(metadata.get("trace", {})),
            diagnostics=dict(metadata.get("diagnostics", {})),
            metrics=dict(lifecycle.metrics),
            metadata=metadata,
            correlation=lifecycle.correlation.to_dict() if lifecycle.correlation else {},
            stage_history=history,
            allowed_next_stages=list(lifecycle.allowed_next_stages),
            validation_refs=dict(metadata.get("validation_refs", {})),
            input_refs=dict(metadata.get("input_refs", {})),
            output_refs=dict(metadata.get("output_refs", {})),
            transition_reason=lifecycle.transition_reason,
            failure_code=lifecycle.failure_code,
        )

    def contract_to_lifecycle(self, contract: LifecycleContract) -> LifecycleRoot:
        """将 LifecycleContract DTO 转换为 LifecycleRoot 聚合根。
        
        用于从外部数据重建领域对象。
        """
        from sprintcycle.domain.core.lifecycle import LifecycleSubstage, LifecycleStatus
        
        metadata = dict(contract.metadata)
        
        # 从 metadata 恢复引用数据
        refs_to_remove = [
            "delivery_refs", "runtime_refs", "suggestion_refs", "skill_refs",
            "skill_matches", "skill_review_checklists", "skill_trace",
            "evolution_refs", "recovery_refs", "recovery_plan_refs",
            "governance_refs", "trace", "diagnostics", "validation_refs",
            "input_refs", "output_refs"
        ]
        for ref_key in refs_to_remove:
            metadata.pop(ref_key, None)
        
        lifecycle = create_lifecycle(
            execution_id=contract.execution_id,
            task_id=contract.task_id,
            project_path=contract.project_path,
            task_type=contract.task_type,
            intent=contract.intent,
            metadata=metadata,
        )
        
        # 转换到目标子状态
        try:
            target_substage = LifecycleSubstage.from_string(contract.stage)
            if target_substage != lifecycle.substage:
                lifecycle = lifecycle.transition_to_substage(target_substage)
        except Exception:
            pass
        
        return lifecycle

    def build_lifecycle_contract(
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
    ) -> LifecycleContract:
        """构建 LifecycleContract DTO（兼容旧 API）。
        
        内部使用 LifecycleRoot 聚合根处理业务逻辑，
        然后转换为 DTO 用于外部交互。
        """
        lifecycle = self.build_lifecycle(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path,
            stage=stage,
            status=status,
            metadata=metadata,
            failure_kind=failure_kind,
            failure_reason=failure_reason,
            delivery_refs=delivery_refs,
            runtime_refs=runtime_refs,
            suggestion_refs=suggestion_refs,
            skill_refs=skill_refs,
            skill_matches=skill_matches,
            skill_review_checklists=skill_review_checklists,
            skill_trace=skill_trace,
            evolution_refs=evolution_refs,
            evidence=evidence,
            recovery_refs=recovery_refs,
            recovery_plan_refs=recovery_plan_refs,
            governance_refs=governance_refs,
            trace=trace,
            diagnostics=diagnostics,
            metrics=metrics,
            correlation=correlation,
            stage_history=stage_history,
            allowed_next_stages=allowed_next_stages,
            validation_refs=validation_refs,
            input_refs=input_refs,
            output_refs=output_refs,
            transition_reason=transition_reason,
            failure_code=failure_code,
        )
        
        # 获取阶段历史（包含聚合根生成的历史）
        history_from_root = [
            {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
            for h in lifecycle.stage_history
        ]
        full_history = list(stage_history or []) + history_from_root
        
        # 构建完整的 metadata
        full_metadata = dict(lifecycle.metadata)
        if delivery_refs:
            full_metadata["delivery_refs"] = dict(delivery_refs)
        if runtime_refs:
            full_metadata["runtime_refs"] = dict(runtime_refs)
        if suggestion_refs:
            full_metadata["suggestion_refs"] = list(suggestion_refs)
        if skill_refs:
            full_metadata["skill_refs"] = list(skill_refs)
        if skill_matches:
            full_metadata["skill_matches"] = list(skill_matches)
        if skill_review_checklists:
            full_metadata["skill_review_checklists"] = list(skill_review_checklists)
        if skill_trace:
            full_metadata["skill_trace"] = dict(skill_trace)
        if evolution_refs:
            full_metadata["evolution_refs"] = dict(evolution_refs)
        if recovery_refs:
            full_metadata["recovery_refs"] = dict(recovery_refs)
        if recovery_plan_refs:
            full_metadata["recovery_plan_refs"] = dict(recovery_plan_refs)
        if governance_refs:
            full_metadata["governance_refs"] = dict(governance_refs)
        if trace:
            full_metadata["trace"] = dict(trace)
        if diagnostics:
            full_metadata["diagnostics"] = dict(diagnostics)
        if validation_refs:
            full_metadata["validation_refs"] = dict(validation_refs)
        if input_refs:
            full_metadata["input_refs"] = dict(input_refs)
        if output_refs:
            full_metadata["output_refs"] = dict(output_refs)
        
        return LifecycleContract(
            execution_id=lifecycle.execution_id,
            task_id=lifecycle.task_id,
            project_path=lifecycle.project_path,
            task_type=lifecycle.task_type,
            intent=lifecycle.intent,
            stage=lifecycle.substage.value,
            status=status or lifecycle.status.value,
            failure_kind=failure_kind or lifecycle.failure_kind,
            failure_reason=failure_reason or lifecycle.failure_reason,
            delivery_refs=dict(delivery_refs or {}),
            runtime_refs=dict(runtime_refs or {}),
            suggestion_refs=list(suggestion_refs or []),
            skill_refs=list(skill_refs or []),
            skill_matches=list(skill_matches or []),
            skill_review_checklists=list(skill_review_checklists or []),
            skill_trace=dict(skill_trace or {}),
            evolution_refs=dict(evolution_refs or {}),
            evidence=ensure_lifecycle_evidence(evidence),
            recovery_refs=dict(recovery_refs or {}),
            recovery_plan_refs=dict(recovery_plan_refs or {}),
            governance_refs=dict(governance_refs or {}),
            trace=dict(trace or {}),
            diagnostics=dict(diagnostics or {}),
            metrics=dict(metrics or {}),
            metadata=full_metadata,
            correlation=correlation or (lifecycle.correlation.to_dict() if lifecycle.correlation else {}),
            stage_history=full_history,
            allowed_next_stages=list(allowed_next_stages or lifecycle.allowed_next_stages),
            validation_refs=dict(validation_refs or {}),
            input_refs=dict(input_refs or {}),
            output_refs=dict(output_refs or {}),
            transition_reason=transition_reason or lifecycle.transition_reason,
            failure_code=failure_code or lifecycle.failure_code,
        )

    def advance_to_normalized(
        self,
        lifecycle: LifecycleRoot,
        *,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> LifecycleRoot:
        """将生命周期推进到 normalized 阶段。"""
        updated_lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.NORMALIZED)
        
        if evidence:
            stage_evidence = StageEvidence(
                stage=LifecycleSubstage.NORMALIZED.value,
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
        updated_lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PLANNED)
        
        if evidence:
            stage_evidence = StageEvidence(
                stage=LifecycleSubstage.PLANNED.value,
                present=True,
                evidence=evidence,
            )
            updated_lifecycle = updated_lifecycle.add_stage_evidence(stage_evidence)
        
        return updated_lifecycle

    def advance_to_running(
        self,
        lifecycle: LifecycleRoot,
    ) -> LifecycleRoot:
        """将生命周期推进到 running 阶段。"""
        return lifecycle.transition_to_substage(LifecycleSubstage.RUNNING)

    def complete_execution(
        self,
        lifecycle: LifecycleRoot,
        *,
        success: bool = True,
    ) -> LifecycleRoot:
        """完成执行阶段。"""
        if success:
            lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.OBSERVING)
        
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
                lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PROMOTED)
            except Exception:
                pass
        
        return lifecycle


__all__ = [
    "LifecycleRootService",
]
