"""GovernanceRunner 测试 - 覆盖治理检查执行器"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from sprintcycle.domain.core.governance.core.runner import (
    GovernanceRunner,
    run_planning_gate_sync,
    run_review_gate_sync,
    persist_report,
    persist_planning_report,
    _resolve_lint_imports_exe,
    _maybe_downgrade_errors_to_warnings,
    _truncate,
    run_governance_check_and_persist,
    emit_governance_gate_cli_sync,
)
from sprintcycle.domain.core.governance.arch_guard.model import GuardReport, GuardFinding


class MockRuntimeConfig:
    """Mock runtime configuration for testing"""
    
    def __init__(self):
        self.governance_downgrade_errors_to_warnings = False
        self.governance_spec_glob = ""
        self.governance_spec_marker = ""
        self.governance_acceptance_glob = ""
        self.governance_planning_validate_release_plan = True
        self.hitl_enabled = False
        self.hitl_default_risk_level = "medium"
        self.governance_review_static = True
        self.governance_review_import_linter = False
        self.governance_check_adr = False
        self.governance_check_compose = False
        self.governance_compose_supply_chain = False
        self.governance_report_dir = ".sprintcycle"
        self.governance_block_on = "none"
        self.governance_cli_emit_events = False
        
    def effective_quality_level(self):
        return "strict"


class TestGovernanceRunnerBasics:
    """测试治理运行器基本功能"""

    def test_runner_initialization(self):
        """测试运行器初始化"""
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        assert runner._cfg == cfg
        assert runner._observability is None

    def test_truncate_function(self):
        """测试截断函数"""
        short_str = "hello world"
        assert _truncate(short_str) == "hello world"
        
        long_str = "a" * 5000
        result = _truncate(long_str)
        assert len(result) == 3996  # 4000 - 20 (for "... [truncated]") + len("\n... [truncated]") = 3996
        assert "... [truncated]" in result

    def test_maybe_downgrade_errors_to_warnings_disabled(self):
        """测试降级错误到警告功能（禁用状态）"""
        cfg = MockRuntimeConfig()
        cfg.governance_downgrade_errors_to_warnings = False
        
        findings = [
            GuardFinding(rule_id="test", severity="error", message="test"),
            GuardFinding(rule_id="test2", severity="warning", message="test2"),
        ]
        
        _maybe_downgrade_errors_to_warnings(cfg, findings)
        
        assert findings[0].severity == "error"
        assert findings[1].severity == "warning"

    def test_maybe_downgrade_errors_to_warnings_enabled(self):
        """测试降级错误到警告功能（启用状态）"""
        cfg = MockRuntimeConfig()
        cfg.governance_downgrade_errors_to_warnings = True
        
        findings = [
            GuardFinding(rule_id="test", severity="error", message="test"),
            GuardFinding(rule_id="test2", severity="warning", message="test2"),
        ]
        
        _maybe_downgrade_errors_to_warnings(cfg, findings)
        
        assert findings[0].severity == "warning"
        assert findings[1].severity == "warning"


class TestPlanningGate:
    """测试规划门检查"""

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_pytest")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_architecture_guard")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    async def test_run_planning_gate_empty_project(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate,
        mock_arch_guard, mock_pytest, mock_static_gate, tmp_path
    ):
        """测试空项目的规划门检查"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        mock_pytest.return_value = False
        mock_arch_guard.return_value = False
        
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        report = await runner.run_planning_gate(str(tmp_path))
        
        assert report is not None
        assert report.gate == "planning"
        assert "project_path" in report.metadata
        assert "duration_sec" in report.metadata

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_pytest")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_architecture_guard")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    async def test_run_planning_gate_with_spec_glob(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate,
        mock_arch_guard, mock_pytest, mock_static_gate, tmp_path
    ):
        """测试带spec_glob配置的规划门检查"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        mock_pytest.return_value = False
        mock_arch_guard.return_value = False
        
        cfg = MockRuntimeConfig()
        cfg.governance_spec_glob = "*.nonexistent"
        runner = GovernanceRunner(cfg)
        
        report = await runner.run_planning_gate(str(tmp_path))
        
        assert report is not None
        assert len(report.findings) >= 1
        assert any(f.rule_id == "planning:spec_glob" for f in report.findings)

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_pytest")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_architecture_guard")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    async def test_run_planning_gate_with_checks(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate,
        mock_arch_guard, mock_pytest, mock_static_gate, tmp_path
    ):
        """测试规划门检查执行规则"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        mock_pytest.return_value = False
        mock_arch_guard.return_value = False
        
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        report = await runner.run_planning_gate(str(tmp_path))
        
        assert report is not None
        assert report.gate == "planning"
        mock_run_checks.assert_called_once()


class TestReviewGate:
    """测试评审门检查"""

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    async def test_run_review_gate_empty_project(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate, mock_static_gate, tmp_path
    ):
        """测试空项目的评审门检查"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        report = await runner.run_review_gate(str(tmp_path))
        
        assert report is not None
        assert report.gate == "review"
        assert "project_path" in report.metadata
        assert "duration_sec" in report.metadata
        assert "steps" in report.metadata

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    async def test_run_review_gate_with_checks(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate, mock_static_gate, tmp_path
    ):
        """测试评审门检查执行规则"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        report = await runner.run_review_gate(str(tmp_path))
        
        assert report is not None
        assert report.gate == "review"
        mock_run_checks.assert_called_once()

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    async def test_run_review_gate_with_import_linter_disabled(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate, mock_static_gate, tmp_path
    ):
        """测试禁用import-linter的评审门检查"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        
        cfg = MockRuntimeConfig()
        cfg.governance_review_import_linter = False
        runner = GovernanceRunner(cfg)
        
        report = await runner.run_review_gate(str(tmp_path))
        
        assert report is not None
        assert "import_linter_disabled" in report.metadata["steps"]


class TestSyncFunctions:
    """测试同步函数"""

    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_pytest")
    @patch("sprintcycle.domain.core.governance.core.runner._runs_architecture_guard")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    def test_run_planning_gate_sync(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate,
        mock_arch_guard, mock_pytest, mock_static_gate, tmp_path
    ):
        """测试同步运行规划门检查"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        mock_pytest.return_value = False
        mock_arch_guard.return_value = False
        
        cfg = MockRuntimeConfig()
        
        report = run_planning_gate_sync(str(tmp_path), cfg)
        
        assert report is not None
        assert report.gate == "planning"

    @patch("sprintcycle.domain.core.governance.core.runner._runs_static_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.checks_for_gate")
    @patch("sprintcycle.domain.core.governance.core.runner.run_argv_checks")
    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    def test_run_review_gate_sync(
        self, mock_load_data, mock_run_checks, mock_checks_for_gate, mock_static_gate, tmp_path
    ):
        """测试同步运行评审门检查"""
        mock_load_data.return_value = {}
        mock_checks_for_gate.return_value = []
        mock_run_checks.return_value = []
        mock_static_gate.return_value = False
        
        cfg = MockRuntimeConfig()
        
        report = run_review_gate_sync(str(tmp_path), cfg)
        
        assert report is not None
        assert report.gate == "review"


class TestReportPersistence:
    """测试报告持久化"""

    def test_persist_report(self, tmp_path):
        """测试持久化报告"""
        cfg = MockRuntimeConfig()
        cfg.governance_report_dir = ".test_reports"
        
        report = GuardReport(gate="review", findings=[], metadata={"test": "value"})
        
        result = persist_report(report, str(tmp_path), cfg)
        
        assert result is not None
        assert result.exists()
        assert result.name == "governance_last.json"

    def test_persist_planning_report(self, tmp_path):
        """测试持久化规划报告"""
        cfg = MockRuntimeConfig()
        cfg.governance_report_dir = ".test_reports"
        
        report = GuardReport(gate="planning", findings=[], metadata={"test": "value"})
        
        result = persist_planning_report(report, str(tmp_path), cfg)
        
        assert result is not None
        assert result.exists()
        assert result.name == "governance_planning_last.json"


class TestGuardReport:
    """测试GuardReport模型"""

    def test_guard_report_creation(self):
        """测试GuardReport创建"""
        findings = [
            GuardFinding(rule_id="test1", severity="error", message="error message"),
            GuardFinding(rule_id="test2", severity="warning", message="warning message"),
        ]
        metadata = {"key": "value"}
        
        report = GuardReport(gate="planning", findings=findings, metadata=metadata)
        
        assert report.gate == "planning"
        assert len(report.findings) == 2
        assert report.metadata == metadata

    def test_guard_report_has_error_severity(self):
        """测试has_error_severity方法"""
        report_with_errors = GuardReport(
            gate="test",
            findings=[
                GuardFinding(rule_id="test", severity="error", message="error"),
            ],
            metadata={},
        )
        
        report_without_errors = GuardReport(
            gate="test",
            findings=[
                GuardFinding(rule_id="test", severity="warning", message="warning"),
            ],
            metadata={},
        )
        
        assert report_with_errors.has_error_severity() is True
        assert report_without_errors.has_error_severity() is False

    def test_guard_report_to_dict(self):
        """测试to_dict方法"""
        findings = [GuardFinding(rule_id="test", severity="error", message="test")]
        report = GuardReport(gate="planning", findings=findings, metadata={"key": "value"})
        
        result = report.to_dict()
        
        assert result["gate"] == "planning"
        assert len(result["findings"]) == 1
        assert result["metadata"]["key"] == "value"


class TestGuardFinding:
    """测试GuardFinding模型"""

    def test_guard_finding_creation(self):
        """测试GuardFinding创建"""
        finding = GuardFinding(
            rule_id="test_rule",
            severity="error",
            message="test message",
            location={"file": "test.py", "line": 10},
        )
        
        assert finding.rule_id == "test_rule"
        assert finding.severity == "error"
        assert finding.message == "test message"
        assert finding.location == {"file": "test.py", "line": 10}

    def test_guard_finding_to_dict(self):
        """测试to_dict方法"""
        finding = GuardFinding(
            rule_id="test_rule",
            severity="warning",
            message="test message",
            location={"file": "test.py"},
        )
        
        result = finding.to_dict()
        
        assert result["rule_id"] == "test_rule"
        assert result["severity"] == "warning"
        assert result["message"] == "test message"
        assert result["location"] == {"file": "test.py"}


class TestGovernanceCheckAndPersist:
    """测试治理检查和持久化函数"""

    @patch("sprintcycle.domain.core.governance.core.runner.run_planning_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.run_review_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_planning_report")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_report")
    @patch("sprintcycle.domain.core.governance.core.runner.emit_governance_gate_cli_sync")
    def test_run_governance_check_and_persist_planning(
        self, mock_emit, mock_persist, mock_persist_plan, mock_review, mock_planning, tmp_path
    ):
        """测试仅运行规划门检查"""
        mock_planning.return_value = GuardReport(gate="planning", findings=[], metadata={})
        mock_review.return_value = None
        
        cfg = MockRuntimeConfig()
        
        planning_report, review_report, fail = run_governance_check_and_persist(
            str(tmp_path), cfg, "planning"
        )
        
        assert planning_report is not None
        assert review_report is None
        assert fail is False
        mock_planning.assert_called_once()
        mock_persist_plan.assert_called_once()
        mock_emit.assert_called_once()

    @patch("sprintcycle.domain.core.governance.core.runner.run_planning_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.run_review_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_planning_report")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_report")
    @patch("sprintcycle.domain.core.governance.core.runner.emit_governance_gate_cli_sync")
    def test_run_governance_check_and_persist_review(
        self, mock_emit, mock_persist, mock_persist_plan, mock_review, mock_planning, tmp_path
    ):
        """测试仅运行评审门检查"""
        mock_planning.return_value = None
        mock_review.return_value = GuardReport(gate="review", findings=[], metadata={})
        
        cfg = MockRuntimeConfig()
        
        planning_report, review_report, fail = run_governance_check_and_persist(
            str(tmp_path), cfg, "review"
        )
        
        assert planning_report is None
        assert review_report is not None
        assert fail is False
        mock_review.assert_called_once()
        mock_persist.assert_called_once()
        mock_emit.assert_called_once()

    @patch("sprintcycle.domain.core.governance.core.runner.run_planning_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.run_review_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_planning_report")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_report")
    @patch("sprintcycle.domain.core.governance.core.runner.emit_governance_gate_cli_sync")
    def test_run_governance_check_and_persist_both(
        self, mock_emit, mock_persist, mock_persist_plan, mock_review, mock_planning, tmp_path
    ):
        """测试运行规划和评审门检查"""
        mock_planning.return_value = GuardReport(gate="planning", findings=[], metadata={})
        mock_review.return_value = GuardReport(gate="review", findings=[], metadata={})
        
        cfg = MockRuntimeConfig()
        
        planning_report, review_report, fail = run_governance_check_and_persist(
            str(tmp_path), cfg, "both"
        )
        
        assert planning_report is not None
        assert review_report is not None
        assert fail is False
        mock_planning.assert_called_once()
        mock_review.assert_called_once()

    @patch("sprintcycle.domain.core.governance.core.runner.run_planning_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.run_review_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_planning_report")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_report")
    @patch("sprintcycle.domain.core.governance.core.runner.emit_governance_gate_cli_sync")
    def test_run_governance_check_and_persist_block_on_planning_and_review(
        self, mock_emit, mock_persist, mock_persist_plan, mock_review, mock_planning, tmp_path
    ):
        """测试block_on=planning_and_review时规划门错误导致失败"""
        mock_planning.return_value = GuardReport(
            gate="planning",
            findings=[GuardFinding(rule_id="test", severity="error", message="test")],
            metadata={},
        )
        mock_review.return_value = None
        
        cfg = MockRuntimeConfig()
        cfg.governance_block_on = "planning_and_review"
        
        planning_report, review_report, fail = run_governance_check_and_persist(
            str(tmp_path), cfg, "planning"
        )
        
        assert fail is True

    @patch("sprintcycle.domain.core.governance.core.runner.run_planning_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.run_review_gate_sync")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_planning_report")
    @patch("sprintcycle.domain.core.governance.core.runner.persist_report")
    @patch("sprintcycle.domain.core.governance.core.runner.emit_governance_gate_cli_sync")
    def test_run_governance_check_and_persist_block_on_review_only(
        self, mock_emit, mock_persist, mock_persist_plan, mock_review, mock_planning, tmp_path
    ):
        """测试block_on=review_only时评审门错误导致失败"""
        mock_planning.return_value = None
        mock_review.return_value = GuardReport(
            gate="review",
            findings=[GuardFinding(rule_id="test", severity="error", message="test")],
            metadata={},
        )
        
        cfg = MockRuntimeConfig()
        cfg.governance_block_on = "review_only"
        
        planning_report, review_report, fail = run_governance_check_and_persist(
            str(tmp_path), cfg, "review"
        )
        
        assert fail is True


class TestGovernanceRunnerMethods:
    """测试GovernanceRunner内部方法"""

    def test_project_method(self, tmp_path):
        """测试_project方法"""
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        result = runner._project(str(tmp_path))
        
        assert result == tmp_path.resolve()

    @patch("sprintcycle.domain.core.governance.core.runner.load_merged_governance_data")
    def test_load_yaml_data(self, mock_load_data, tmp_path):
        """测试_load_yaml_data方法"""
        mock_load_data.return_value = {"test": "value"}
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        result = runner._load_yaml_data(tmp_path)
        
        assert result == {"test": "value"}
        mock_load_data.assert_called_once_with(tmp_path, cfg)

    @patch("sprintcycle.domain.core.governance.core.runner.create_observability_facade")
    def test_observability_facade(self, mock_create_facade, tmp_path):
        """测试_observability_facade方法"""
        mock_facade = MagicMock()
        mock_create_facade.return_value = mock_facade
        
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        result1 = runner._observability_facade(str(tmp_path))
        result2 = runner._observability_facade(str(tmp_path))
        
        assert result1 == mock_facade
        assert result2 == mock_facade
        mock_create_facade.assert_called_once()

    @pytest.mark.asyncio
    @patch("sprintcycle.domain.core.governance.core.runner.evaluate_hitl_policy")
    async def test_maybe_trigger_hitl_should_not_trigger(self, mock_evaluate_policy, tmp_path):
        """测试_maybe_trigger_hitl不触发HITL"""
        mock_policy = MagicMock()
        mock_policy.should_trigger = False
        mock_evaluate_policy.return_value = mock_policy
        
        cfg = MockRuntimeConfig()
        runner = GovernanceRunner(cfg)
        
        result = await runner._maybe_trigger_hitl(
            project_path=str(tmp_path),
            gate="test",
            title="Test",
            summary="Test summary",
            context={},
        )
        
        assert result == mock_policy
        mock_evaluate_policy.assert_called_once()


class TestEmitGovernanceGateCliSync:
    """测试CLI事件派发"""

    def test_emit_governance_gate_cli_sync_disabled(self, tmp_path):
        """测试禁用CLI事件派发"""
        cfg = MockRuntimeConfig()
        cfg.governance_cli_emit_events = False
        
        report = GuardReport(gate="planning", findings=[], metadata={})
        
        emit_governance_gate_cli_sync(str(tmp_path), cfg, "planning", report)

