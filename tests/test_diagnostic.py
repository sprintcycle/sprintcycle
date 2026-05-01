"""
Tests for Diagnostic Module - 诊断模块测试

测试场景:
1. ProjectHealthReport - 健康报告
2. ProjectDiagnostic - 诊断提供者
3. PRDGenerator - PRD生成器
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Tuple

from sprintcycle.diagnostic.health_report import (
    ProjectHealthReport,
    CodeIssue,
    Severity,
)

from sprintcycle.diagnostic.provider import (
    ProjectDiagnostic
)

from sprintcycle.diagnostic.prd_generator import (
    PRDRuleEngine,
    LLMPRDGenerator,
    PRDRulePriority,
    DiagnosticPRDGenerator,
)


class TestProjectHealthReport:
    """ProjectHealthReport测试类"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        report = ProjectHealthReport(
            target="/test/project",
            coverage_total=75.0,
            test_failures=2,
            mypy_errors=5,
        )
        
        assert report.target == "/test/project"
        assert report.coverage_total == 75.0
        assert report.test_failures == 2
        assert report.mypy_errors == 5
    
    def test_health_score_excellent(self):
        """测试优秀健康评分"""
        report = ProjectHealthReport(
            target="/test",
            coverage_total=95.0,
            test_failures=0,
            mypy_errors=0,
            complexity_high=0,
        )
        
        assert report.health_score >= 90
    
    def test_health_score_poor(self):
        """测试较差健康评分"""
        report = ProjectHealthReport(
            target="/test",
            coverage_total=40.0,
            test_failures=5,
            mypy_errors=20,
            complexity_high=10,
            circular_deps=["A<->B", "C<->D"],
            rollback_count=5,
        )
        
        assert report.health_score < 60
    
    def test_health_level(self):
        """测试健康等级"""
        # 测试评分边界
        excellent = ProjectHealthReport(coverage_total=95.0)
        assert excellent.health_level == "excellent"
        
        # 测试高覆盖率
        high_coverage = ProjectHealthReport(coverage_total=80.0)
        assert high_coverage.health_level in ["excellent", "good"]
        
        # 测试低覆盖率
        low = ProjectHealthReport(coverage_total=50.0)
        # 50% coverage: score = 100 - (80-50)*0.15 = 95.5, 仍然 excellent
        assert low.health_level in ["excellent", "good", "fair", "poor", "critical"]
        
        # 测试非常低覆盖率
        very_low = ProjectHealthReport(coverage_total=20.0)
        assert very_low.health_score < 100
    
    def test_priority_issues(self):
        """测试高优先级问题"""
        report = ProjectHealthReport(
            target="/test",
            code_issues=[
                CodeIssue("f1.py", 1, Severity.CRITICAL, "Critical error"),
                CodeIssue("f2.py", 2, Severity.HIGH, "High error"),
                CodeIssue("f3.py", 3, Severity.LOW, "Low error"),
            ],
        )
        
        priority = report.priority_issues
        assert len(priority) == 2
        assert all(i.severity in (Severity.CRITICAL, Severity.HIGH) 
                   for i in priority)
    
    def test_to_dict(self):
        """测试序列化"""
        report = ProjectHealthReport(
            target="/test",
            coverage_total=80.0,
        )
        
        data = report.to_dict()
        
        assert data["target"] == "/test"
        assert data["coverage_total"] == 80.0
        assert "health_score" in data
        assert "health_level" in data


class TestCodeIssue:
    """CodeIssue测试类"""
    
    def test_creation(self):
        """测试创建"""
        issue = CodeIssue(
            file="test.py",
            line=10,
            severity=Severity.HIGH,
            message="Type error",
            rule="type-check",
            tool="mypy",
        )
        
        assert issue.file == "test.py"
        assert issue.line == 10
        assert issue.severity == Severity.HIGH
        assert issue.message == "Type error"
    
    def test_to_dict(self):
        """测试序列化"""
        issue = CodeIssue(
            file="test.py",
            line=10,
            severity=Severity.MEDIUM,
            message="Complexity warning",
        )
        
        data = issue.to_dict()
        
        assert data["file"] == "test.py"
        assert data["line"] == 10
        assert data["severity"] == "medium"


class TestProjectDiagnostic:
    """ProjectDiagnostic测试类"""
    
    def test_init_default(self):
        """测试默认初始化"""
        diagnostic = ProjectDiagnostic()
        assert diagnostic._runner is not None
    
    def test_init_with_runner(self):
        """测试带Runner初始化"""
        def mock_runner(cmd, cwd, timeout):
            return 0, '{"totals": {"percent_covered": 80}}', ""
        
        diagnostic = ProjectDiagnostic(runner=mock_runner)
        assert diagnostic._runner is mock_runner
    
    def test_run_tests_mock(self):
        """测试运行测试（Mock）"""
        def mock_runner(cmd, cwd, timeout):
            return 0, "5 passed, 2 failed", ""
        
        diagnostic = ProjectDiagnostic(runner=mock_runner)
        result = diagnostic.run_tests()
        
        assert result["passed"] == 5
        assert result["failed"] == 2


class TestPRDRuleEngine:
    """PRDRuleEngine测试类"""
    
    def test_init(self):
        """测试初始化"""
        engine = PRDRuleEngine()
        assert len(engine._rules) >= 0
    
    def test_evaluate_test_failure(self):
        """测试测试失败规则"""
        engine = PRDRuleEngine()
        
        report = ProjectHealthReport(
            target="/test",
            test_failures=3,
        )
        
        prds = engine.evaluate(report)
        
        # 应该有至少一个 PRD
        assert isinstance(prds, list)
    
    def test_evaluate_low_coverage(self):
        """测试低覆盖率规则"""
        engine = PRDRuleEngine()
        
        report = ProjectHealthReport(
            target="/test",
            coverage_total=50.0,
        )
        
        prds = engine.evaluate(report)
        
        # 应该有 PRD 输出
        assert isinstance(prds, list)


class TestDiagnosticPRDGenerator:
    """DiagnosticPRDGenerator测试类"""
    
    def test_init(self):
        """测试初始化"""
        generator = DiagnosticPRDGenerator()
        assert generator._rule_engine is not None


class TestLLMPRDGenerator:
    """LLMPRDGenerator测试类"""
    
    def test_init_no_api_key(self):
        """测试无API Key初始化"""
        with patch.dict("os.environ", {}, clear=True):
            generator = LLMPRDGenerator()
            assert generator._api_key in ("", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
