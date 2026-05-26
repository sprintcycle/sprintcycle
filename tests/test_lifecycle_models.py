"""Lifecycle Models 测试 - 覆盖数据模型"""

from __future__ import annotations

import pytest

from sprintcycle.domain.core.lifecycle.models import (
    LifecycleContract,
    STAGE_EVIDENCE_SCHEMA,
    STAGE_EVIDENCE_TRUTHY_KEYS,
    FAILURE_KIND_BY_STAGE,
    STAGE_EVIDENCE_KEYS,
    CANONICAL_EVIDENCE_KEYS,
    TERMINAL_STATUSES,
    REQUIRED_EVIDENCE_SECTIONS,
    REQUIRED_STAGE_SEQUENCE,
    RECOVERY_STAGE_TARGETS,
    ensure_lifecycle_evidence,
    validate_lifecycle_evidence,
    next_stage,
    normalize_lifecycle_metadata,
    build_lifecycle_contract,
    build_lifecycle_state_machine,
    build_lifecycle_machine,
)


class TestLifecycleContract:
    """测试 LifecycleContract 数据模型"""

    def test_contract_creation(self):
        """测试契约创建"""
        contract = LifecycleContract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            task_type="project_optimization",
            intent="test intent",
        )

        assert contract.execution_id == "exec-1"
        assert contract.task_id == "task-1"
        assert contract.project_path == "/test/project"
        assert contract.task_type == "project_optimization"
        assert contract.intent == "test intent"
        assert contract.stage == "new"
        assert contract.status == "pending"

    def test_contract_validate_valid(self):
        """测试验证有效契约"""
        contract = LifecycleContract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="normalized",
            status="running",
        )

        errors = contract.validate()

        assert len(errors) == 0

    def test_contract_validate_missing_required(self):
        """测试验证缺少必需字段"""
        contract = LifecycleContract(
            execution_id="",
            task_id="",
            project_path="",
        )

        errors = contract.validate()

        assert "execution_id is required" in errors
        assert "task_id is required" in errors
        assert "project_path is required" in errors

    def test_contract_validate_invalid_stage(self):
        """测试验证无效阶段"""
        contract = LifecycleContract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="invalid_stage",
        )

        errors = contract.validate()

        assert "invalid stage: invalid_stage" in errors

    def test_contract_validate_invalid_status(self):
        """测试验证无效状态"""
        contract = LifecycleContract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            status="invalid_status",
        )

        errors = contract.validate()

        assert "invalid status: invalid_status" in errors

    def test_contract_validate_terminal_status_non_terminal_stage(self):
        """测试终端状态与非终端阶段的一致性"""
        contract = LifecycleContract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="executing",
            status="success",
        )

        errors = contract.validate()

        assert any("terminal status requires terminal stage" in error for error in errors)

    def test_contract_to_dict(self):
        """测试转换为字典"""
        contract = LifecycleContract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="normalized",
            status="running",
        )

        result = contract.to_dict()

        assert result["execution_id"] == "exec-1"
        assert result["task_id"] == "task-1"
        assert result["stage"] == "normalized"
        assert result["status"] == "running"
        assert "is_terminal" in result
        assert "stage_index" in result
        assert "stage_hints" in result
        assert "validation" in result
        assert result["validation"]["ok"] is True


class TestLifecycleEvidenceHelpers:
    """测试生命周期证据辅助函数"""

    def test_ensure_lifecycle_evidence_empty(self):
        """测试确保空证据结构"""
        result = ensure_lifecycle_evidence(None)

        assert "contract" in result
        assert "stages" in result
        assert "runtime" in result
        assert "governance" in result
        assert "promotion" in result
        assert "evolution" in result
        assert "suggestion" in result
        assert "trace" in result
        assert "diagnostics" in result
        assert "recovery" in result

    def test_ensure_lifecycle_evidence_with_existing(self):
        """测试确保带现有数据的证据结构"""
        evidence = {
            "contract": {"key": "value"},
            "stages": {"normalized": {"present": True}},
        }

        result = ensure_lifecycle_evidence(evidence)

        assert result["contract"]["key"] == "value"
        assert result["stages"]["normalized"]["present"] is True
        assert "runtime" in result
        assert "governance" in result

    def test_ensure_lifecycle_evidence_stages(self):
        """测试确保所有阶段存在"""
        result = ensure_lifecycle_evidence()

        stages = result["stages"]
        for stage in STAGE_EVIDENCE_KEYS:
            canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
            assert canonical_stage in stages, f"Missing stage: {canonical_stage}"


class TestStageHelpers:
    """测试阶段辅助函数"""

    def test_next_stage(self):
        """测试获取下一阶段"""
        assert next_stage("new") == "normalized"
        assert next_stage("normalized") == "planned"
        assert next_stage("executing") == "observing"
        assert next_stage("promoted") == ""
        assert next_stage("unknown") == ""

    def test_normalize_lifecycle_metadata(self):
        """测试规范化生命周期元数据"""
        metadata = {
            "author": "test",
            "custom_field": "value",
        }

        result = normalize_lifecycle_metadata(metadata)

        assert result["task_type"] == "project_optimization"
        assert result["intent"] == ""
        assert result["source"] == "web"
        assert result["stability_contract"] == "web_end_to_end"
        assert result["author"] == "test"
        assert result["custom_field"] == "value"

    def test_normalize_lifecycle_metadata_with_existing(self):
        """测试规范化带现有值的元数据"""
        metadata = {
            "task_type": "custom_type",
            "intent": "custom intent",
            "source": "api",
        }

        result = normalize_lifecycle_metadata(metadata)

        assert result["task_type"] == "custom_type"
        assert result["intent"] == "custom intent"
        assert result["source"] == "api"


class TestConstants:
    """测试常量定义"""

    def test_stage_evidence_schema(self):
        """测试阶段证据schema"""
        assert "normalized" in STAGE_EVIDENCE_SCHEMA
        assert "plan" in STAGE_EVIDENCE_SCHEMA
        assert "execute" in STAGE_EVIDENCE_SCHEMA
        assert "observe" in STAGE_EVIDENCE_SCHEMA
        assert "diagnose" in STAGE_EVIDENCE_SCHEMA
        assert "repair" in STAGE_EVIDENCE_SCHEMA
        assert "verify" in STAGE_EVIDENCE_SCHEMA
        assert "deliver" in STAGE_EVIDENCE_SCHEMA
        assert "runtime" in STAGE_EVIDENCE_SCHEMA
        assert "governance" in STAGE_EVIDENCE_SCHEMA
        assert "promotion" in STAGE_EVIDENCE_SCHEMA
        assert "evolution" in STAGE_EVIDENCE_SCHEMA

    def test_stage_evidence_truthy_keys(self):
        """测试阶段证据真值key"""
        assert "repair" in STAGE_EVIDENCE_TRUTHY_KEYS
        assert "verify" in STAGE_EVIDENCE_TRUTHY_KEYS
        assert "governance" in STAGE_EVIDENCE_TRUTHY_KEYS

    def test_failure_kind_by_stage(self):
        """测试失败类型定义"""
        assert FAILURE_KIND_BY_STAGE["executing"] == "execution_error"
        assert FAILURE_KIND_BY_STAGE["observing"] == "observation_error"
        assert FAILURE_KIND_BY_STAGE["repairing"] == "repair_error"
        assert FAILURE_KIND_BY_STAGE["verifying"] == "verification_error"
        assert FAILURE_KIND_BY_STAGE["delivering"] == "delivery_error"
        assert FAILURE_KIND_BY_STAGE["new"] == ""
        assert FAILURE_KIND_BY_STAGE["promoted"] == ""

    def test_terminal_statuses(self):
        """测试终端状态"""
        assert "success" in TERMINAL_STATUSES
        assert "failed" in TERMINAL_STATUSES
        assert "cancelled" in TERMINAL_STATUSES
        assert "promoted" in TERMINAL_STATUSES

    def test_required_evidence_sections(self):
        """测试必需证据部分"""
        assert "contract" in REQUIRED_EVIDENCE_SECTIONS
        assert "stages" in REQUIRED_EVIDENCE_SECTIONS
        assert "runtime" in REQUIRED_EVIDENCE_SECTIONS
        assert "governance" in REQUIRED_EVIDENCE_SECTIONS
        assert "promotion" in REQUIRED_EVIDENCE_SECTIONS
        assert "evolution" in REQUIRED_EVIDENCE_SECTIONS

    def test_required_stage_sequence(self):
        """测试必需阶段序列"""
        assert REQUIRED_STAGE_SEQUENCE[0] == "normalized"
        assert REQUIRED_STAGE_SEQUENCE[-1] == "evolution"

    def test_recovery_stage_targets(self):
        """测试恢复阶段目标"""
        assert RECOVERY_STAGE_TARGETS["executing"] == "repair"
        assert RECOVERY_STAGE_TARGETS["observing"] == "repair"
        assert RECOVERY_STAGE_TARGETS["diagnosed"] == "repair"
        assert RECOVERY_STAGE_TARGETS["repairing"] == "verify"
        assert RECOVERY_STAGE_TARGETS["verifying"] == "observe"
        assert RECOVERY_STAGE_TARGETS["failed"] == "repair"

    def test_canonical_evidence_keys(self):
        """测试规范证据key映射"""
        assert CANONICAL_EVIDENCE_KEYS["governing"] == "governance"
        assert CANONICAL_EVIDENCE_KEYS["governance"] == "governance"


class TestEvidenceValidation:
    """测试证据验证函数"""

    def test_validate_lifecycle_evidence_valid(self):
        """测试验证有效证据"""
        contract = {
            "evidence": {
                "contract": {"normalized": True},
                "stages": {
                    "normalized": {"normalized": True},
                    "plan": {"objective": "test", "present": True},
                    "prepare": {"ready": True, "checks": [], "blockers": [], "present": True},
                    "decompose": {"subtasks": [], "present": True},
                    "execute": {"trace": {}, "present": True},
                    "observe": {"trace": {}, "diagnostics": {}, "present": True},
                    "diagnose": {"root_causes": [], "repair_ready": True, "confidence": 0.8, "recommendations": [], "present": True},
                    "repair": {"attempted": True, "closed_loop": True, "verify_result": "success", "present": True},
                    "verify": {"closed_loop": True, "verify_result": "success", "present": True},
                    "deliver": {"outputs": [], "runtime_linkage": {}, "present": True},
                },
                "runtime": {"linked": True, "healthy": True, "present": True},
                "governance": {"approved": True, "present": True},
                "promotion": {"evidence": {"validated": True}, "completion_score": 1.0},
                "evolution": {"versioned": True, "version_id": "v1", "present": True},
            }
        }

        errors = validate_lifecycle_evidence(contract)

        assert len(errors) == 0

    def test_validate_lifecycle_evidence_missing_contract(self):
        """测试验证缺少contract.normalized"""
        contract = {
            "evidence": {
                "contract": {},
                "stages": {},
                "runtime": {},
                "governance": {},
                "promotion": {},
                "evolution": {},
            }
        }

        errors = validate_lifecycle_evidence(contract)

        assert "evidence.contract.normalized must be truthy" in errors

    def test_validate_lifecycle_evidence_missing_sections(self):
        """测试验证缺少必需部分"""
        contract = {"evidence": {}}

        errors = validate_lifecycle_evidence(contract)

        assert "evidence.contract.normalized must be truthy" in errors
        assert "evidence.runtime must be present" in errors
        assert "evidence.promotion must be present" in errors
        assert "evidence.evolution must be present" in errors

    def test_validate_lifecycle_evidence_missing_stage_keys(self):
        """测试验证缺少阶段必需key"""
        contract = {
            "evidence": {
                "contract": {"normalized": True},
                "stages": {
                    "normalized": {},
                    "plan": {"objective": "test"},
                },
                "runtime": {},
                "governance": {},
                "promotion": {},
                "evolution": {},
            }
        }

        errors = validate_lifecycle_evidence(contract)
        errors_str = "\n".join(errors)

        assert "evidence.normalized missing keys:" in errors_str
        assert "evidence.plan missing keys:" in errors_str

    def test_validate_lifecycle_evidence_non_truthy_keys(self):
        """测试验证非真值key"""
        contract = {
            "evidence": {
                "contract": {"normalized": True},
                "stages": {
                    "repair": {"attempted": False, "closed_loop": True, "verify_result": "success", "present": True},
                },
                "runtime": {"linked": True, "healthy": True, "present": True},
                "governance": {"approved": False, "present": True},
                "promotion": {"evidence": {}, "completion_score": 0.5},
                "evolution": {"versioned": True, "version_id": "v1", "present": True},
            }
        }

        errors = validate_lifecycle_evidence(contract)

        assert "evidence.governance.approved must be truthy" in errors


class TestContractBuilder:
    """测试契约构建函数"""

    def test_build_lifecycle_contract(self):
        """测试构建生命周期契约"""
        contract = build_lifecycle_contract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="normalized",
            status="running",
            metadata={"custom": "value"},
        )

        assert isinstance(contract, LifecycleContract)
        assert contract.execution_id == "exec-1"
        assert contract.task_id == "task-1"
        assert contract.project_path == "/test/project"
        assert contract.stage == "normalized"
        assert contract.status == "running"

    def test_build_lifecycle_contract_with_refs(self):
        """测试构建带引用的契约"""
        contract = build_lifecycle_contract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="normalized",
            status="running",
            delivery_refs={"key": "value"},
            runtime_refs={"runtime_key": "runtime_value"},
            suggestion_refs=[{"id": "sug-1"}],
        )

        assert contract.delivery_refs == {"key": "value"}
        assert contract.runtime_refs == {"runtime_key": "runtime_value"}
        assert contract.suggestion_refs == [{"id": "sug-1"}]

    def test_build_lifecycle_contract_with_evidence(self):
        """测试构建带证据的契约"""
        contract = build_lifecycle_contract(
            execution_id="exec-1",
            task_id="task-1",
            project_path="/test/project",
            stage="normalized",
            status="running",
            evidence={"contract": {"normalized": True}},
        )

        assert contract.evidence is not None
        assert contract.evidence.get("contract", {}).get("normalized") is True


class TestStateMachineBuilder:
    """测试状态机构建函数"""

    def test_build_lifecycle_state_machine(self):
        """测试构建状态机"""
        machine = build_lifecycle_state_machine()

        assert machine is not None
        assert hasattr(machine, "next_stages")
        assert hasattr(machine, "is_terminal")

    def test_build_lifecycle_machine_alias(self):
        """测试旧别名函数"""
        machine = build_lifecycle_machine()

        assert machine is not None
