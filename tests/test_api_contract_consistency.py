"""API契约一致性测试 - 验证REST API响应与contract语义一致"""

from __future__ import annotations

import pytest

from sprintcycle.application.dto.results import (
    ResultBase,
    PlanResult,
    RunResult,
    DiagnoseResult,
    StatusResult,
    RollbackResult,
    StopResult,
    EvolutionSummary,
    EvolutionVersionSummary,
    FinalSnapshotResult,
    EvolutionOverviewResult,
)


class TestResultBase:
    """测试所有Result的基类"""

    def test_result_base_success(self):
        """测试成功结果"""
        result = ResultBase(success=True)
        
        assert result.success is True
        assert result.error is None
        assert result.duration == 0.0
        
        result_dict = result.to_dict()
        assert result_dict == {"success": True, "duration": 0.0}

    def test_result_base_with_error(self):
        """测试带有错误信息的结果"""
        result = ResultBase(success=False, error="test error", duration=1.5)
        
        assert result.success is False
        assert result.error == "test error"
        assert result.duration == 1.5
        
        result_dict = result.to_dict()
        assert result_dict == {"success": False, "error": "test error", "duration": 1.5}

    def test_result_base_to_dict_filters_none(self):
        """测试to_dict过滤None值"""
        result = ResultBase(success=True, error=None, duration=0.0)
        
        result_dict = result.to_dict()
        assert "error" not in result_dict


class TestPlanResult:
    """测试PlanResult响应结构"""

    def test_plan_result_structure(self):
        """测试PlanResult基本结构"""
        evolution = EvolutionSummary(stage="planning", signals=["signal1"])
        result = PlanResult(
            success=True,
            release_plan_yaml="plan: test",
            sprints=[{"id": "s1"}, {"id": "s2"}],
            mode="normal",
            release_plan_name="test-plan",
            evolution=evolution,
        )
        
        assert result.success is True
        assert result.release_plan_yaml == "plan: test"
        assert len(result.sprints) == 2
        assert result.mode == "normal"
        assert result.release_plan_name == "test-plan"
        assert result.evolution.stage == "planning"

    def test_plan_result_to_dict(self):
        """测试PlanResult序列化"""
        evolution = EvolutionSummary(stage="planning", signals=["signal1", "signal2"])
        result = PlanResult(
            success=True,
            release_plan_yaml="plan: test",
            sprints=[{"id": "s1"}],
            mode="normal",
            release_plan_name="test-plan",
            evolution=evolution,
        )
        
        result_dict = result.to_dict()
        
        assert "success" in result_dict
        assert "release_plan_yaml" in result_dict
        assert "sprints" in result_dict
        assert "mode" in result_dict
        assert "release_plan_name" in result_dict
        assert "evolution" in result_dict
        assert result_dict["evolution"]["stage"] == "planning"
        assert result_dict["evolution"]["signals"] == ["signal1", "signal2"]


class TestRunResult:
    """测试RunResult响应结构"""

    def test_run_result_structure(self):
        """测试RunResult基本结构"""
        result = RunResult(
            success=True,
            execution_id="exec-123",
            release_plan_name="test-plan",
            mode="normal",
            duration=45.5,
            completed_sprints=2,
            completed_tasks=5,
            total_sprints=3,
            total_tasks=10,
            current_sprint=3,
            lifecycle_state="running",
            lifecycle_stage="executing",
            message="Execution completed",
        )
        
        assert result.execution_id == "exec-123"
        assert result.release_plan_name == "test-plan"
        assert result.duration == 45.5
        assert result.completed_sprints == 2
        assert result.completed_tasks == 5
        assert result.total_sprints == 3
        assert result.total_tasks == 10
        assert result.current_sprint == 3
        assert result.lifecycle_state == "running"
        assert result.lifecycle_stage == "executing"
        assert result.message == "Execution completed"

    def test_run_result_failure(self):
        """测试失败的RunResult"""
        result = RunResult(
            success=False,
            execution_id="exec-456",
            failure_kind="task_failure",
            failure_reason="Test failure",
        )
        
        assert result.success is False
        assert result.failure_kind == "task_failure"
        assert result.failure_reason == "Test failure"

    def test_run_result_to_dict(self):
        """测试RunResult序列化"""
        evolution = EvolutionSummary(stage="completed", signals=["success"])
        result = RunResult(
            success=True,
            execution_id="exec-789",
            lifecycle_stage="promoted",
            evolution=evolution,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["execution_id"] == "exec-789"
        assert result_dict["lifecycle_stage"] == "promoted"
        assert "evolution" in result_dict
        assert result_dict["evolution"]["stage"] == "completed"


class TestDiagnoseResult:
    """测试DiagnoseResult响应结构"""

    def test_diagnose_result_structure(self):
        """测试DiagnoseResult基本结构"""
        result = DiagnoseResult(
            success=True,
            health_score=85.5,
            issues=[{"severity": "warning", "message": "test issue"}],
            coverage=78.0,
            complexity={"cyclomatic": 10},
        )
        
        assert result.health_score == 85.5
        assert len(result.issues) == 1
        assert result.coverage == 78.0
        assert result.complexity == {"cyclomatic": 10}

    def test_diagnose_result_without_issues(self):
        """测试没有问题的DiagnoseResult"""
        result = DiagnoseResult(
            success=True,
            health_score=100.0,
            issues=[],
            coverage=100.0,
        )
        
        assert len(result.issues) == 0
        assert result.health_score == 100.0


class TestStatusResult:
    """测试StatusResult响应结构"""

    def test_status_result_structure(self):
        """测试StatusResult基本结构"""
        result = StatusResult(
            success=True,
            execution_id="exec-1",
            status="running",
            current_sprint=2,
            total_sprints=3,
            sprint_history=[{"sprint": 1, "status": "completed"}],
            executions=[{"id": "exec-1", "status": "running"}],
        )
        
        assert result.execution_id == "exec-1"
        assert result.status == "running"
        assert result.current_sprint == 2
        assert result.total_sprints == 3
        assert len(result.sprint_history) == 1
        assert len(result.executions) == 1

    def test_status_result_with_state_machine(self):
        """测试包含状态机信息的StatusResult"""
        result = StatusResult(
            success=True,
            state_machine={
                "current_stage": "executing",
                "next_stages": ["observing", "diagnosed"],
                "is_terminal": False,
            },
        )
        
        assert "current_stage" in result.state_machine
        assert "next_stages" in result.state_machine
        assert "is_terminal" in result.state_machine


class TestRollbackResult:
    """测试RollbackResult响应结构"""

    def test_rollback_result_structure(self):
        """测试RollbackResult基本结构"""
        result = RollbackResult(
            success=True,
            execution_id="exec-1",
            rollback_point="commit-abc123",
            files_restored=["file1.txt", "file2.py"],
        )
        
        assert result.execution_id == "exec-1"
        assert result.rollback_point == "commit-abc123"
        assert result.files_restored == ["file1.txt", "file2.py"]


class TestStopResult:
    """测试StopResult响应结构"""

    def test_stop_result_structure(self):
        """测试StopResult基本结构"""
        result = StopResult(
            success=True,
            execution_id="exec-1",
            cancelled=True,
            current_sprint=2,
            message="Execution stopped",
        )
        
        assert result.execution_id == "exec-1"
        assert result.cancelled is True
        assert result.current_sprint == 2
        assert result.message == "Execution stopped"


class TestEvolutionVersionSummary:
    """测试EvolutionVersionSummary响应结构"""

    def test_version_summary_structure(self):
        """测试版本摘要结构"""
        summary = EvolutionVersionSummary(
            success=True,
            version_id="v1.0.0",
            target="code",
            commit_hash="abc123",
            tag="v1.0.0",
            branch="main",
            manifest_path="manifest.yaml",
            sandbox_id="sandbox-1",
            metadata={"author": "test"},
        )
        
        assert summary.success is True
        assert summary.version_id == "v1.0.0"
        assert summary.target == "code"
        assert summary.commit_hash == "abc123"
        assert summary.tag == "v1.0.0"
        assert summary.branch == "main"
        assert summary.manifest_path == "manifest.yaml"
        assert summary.sandbox_id == "sandbox-1"

    def test_version_summary_to_dict(self):
        """测试版本摘要序列化"""
        summary = EvolutionVersionSummary(
            success=True,
            version_id="v1.0.0",
            target="code",
            commit_hash="abc123",
        )
        
        result_dict = summary.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["version_id"] == "v1.0.0"
        assert result_dict["target"] == "code"
        assert result_dict["commit_hash"] == "abc123"


class TestFinalSnapshotResult:
    """测试FinalSnapshotResult响应结构"""

    def test_final_snapshot_structure(self):
        """测试最终快照结构"""
        snapshot = FinalSnapshotResult(
            execution_id="exec-1",
            stage="promoted",
            status="success",
            lifecycle={"stage": "promoted", "status": "success"},
            runtime={"healthy": True},
            governance={"approved": True},
            promotion={"allowed": True},
        )
        
        assert snapshot.execution_id == "exec-1"
        assert snapshot.stage == "promoted"
        assert snapshot.status == "success"
        assert snapshot.lifecycle["stage"] == "promoted"
        assert snapshot.runtime["healthy"] is True
        assert snapshot.governance["approved"] is True
        assert snapshot.promotion["allowed"] is True


class TestEvolutionOverviewResult:
    """测试EvolutionOverviewResult响应结构"""

    def test_overview_result_structure(self):
        """测试演化总览结构"""
        version1 = EvolutionVersionSummary(success=True, version_id="v1", target="code")
        version2 = EvolutionVersionSummary(success=True, version_id="v2", target="requirement")
        
        result = EvolutionOverviewResult(
            success=True,
            active_versions={
                "code": {"version_id": "v1", "tag": "latest"},
                "requirement": {"version_id": "v2", "tag": "v2.0"},
            },
            recent_candidates=[version1, version2],
            totals={"versions": 10, "code_active": 1, "requirement_active": 1},
            sandbox_status={"backend": "running", "root_dir": "/tmp"},
        )
        
        assert result.success is True
        assert len(result.active_versions) == 2
        assert len(result.recent_candidates) == 2
        assert result.totals["versions"] == 10
        assert result.sandbox_status["backend"] == "running"

    def test_overview_to_dashboard_payload(self):
        """测试Dashboard payload转换"""
        version1 = EvolutionVersionSummary(
            success=True,
            version_id="v1",
            target="code",
            commit_hash="abc123",
            tag="latest",
            manifest_path="manifest.yaml",
        )
        
        result = EvolutionOverviewResult(
            success=True,
            active_versions={"code": {"version_id": "v1", "tag": "latest"}},
            recent_candidates=[version1],
            totals={"versions": 10},
            sandbox_status={"backend": "running"},
        )
        
        payload = result.to_dashboard_payload()
        
        assert "active_versions" in payload
        assert "recent_candidates" in payload
        assert "totals" in payload
        assert "sandbox_status" in payload
        assert payload["active_versions"]["code"]["version_id"] == "v1"


class TestContractSemanticConsistency:
    """测试契约语义一致性"""

    def test_lifecycle_stage_values(self):
        """测试生命周期阶段值的一致性"""
        stages = [
            "new", "normalized", "planned", "prepared", "decomposed",
            "executing", "observing", "diagnosed", "repairing", "verifying",
            "delivering", "runtime_linked", "governing", "promotion_ready", "promoted",
        ]
        
        from sprintcycle.domain.core.lifecycle.state_machine import LIFECYCLE_STAGES
        
        assert list(LIFECYCLE_STAGES) == stages

    def test_run_result_lifecycle_stage_semantics(self):
        """测试RunResult中lifecycle_stage的语义一致性"""
        valid_stages = set([
            "new", "normalized", "planned", "prepared", "decomposed",
            "executing", "observing", "diagnosed", "repairing", "verifying",
            "delivering", "runtime_linked", "governing", "promotion_ready", "promoted",
            "failed", "aborted", "cancelled",
        ])
        
        result = RunResult(
            success=True,
            execution_id="exec-1",
            lifecycle_stage="executing",
        )
        
        assert result.lifecycle_stage in valid_stages

    def test_final_snapshot_status_semantics(self):
        """测试FinalSnapshotResult中status的语义一致性"""
        valid_statuses = {"success", "failed", "pending", "running", "cancelled", "promoted"}
        
        snapshot = FinalSnapshotResult(
            execution_id="exec-1",
            stage="promoted",
            status="success",
        )
        
        assert snapshot.status in valid_statuses

    def test_promotion_result_semantics(self):
        """测试promotion结果的语义一致性"""
        snapshot = FinalSnapshotResult(
            execution_id="exec-1",
            promotion={"allowed": True, "status": "promotable"},
        )
        
        assert "allowed" in snapshot.promotion
        assert "status" in snapshot.promotion
        assert isinstance(snapshot.promotion["allowed"], bool)
        assert snapshot.promotion["status"] in {"promotable", "blocked"}
