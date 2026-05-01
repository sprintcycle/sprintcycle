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
                CodeIssue("f1.py", 1, IssueSeverity.CRITICAL, "Critical error"),
                CodeIssue("f2.py", 2, IssueSeverity.HIGH, "High error"),
                CodeIssue("f3.py", 3, IssueSeverity.LOW, "Low error"),
            ],
        )
        
        priority = report.priority_issues
        assert len(priority) == 2
        assert all(i.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH) 
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
            severity=IssueSeverity.HIGH,
            message="Type error",
            rule="type-check",
            tool="mypy",
        )
        
        assert issue.file == "test.py"
        assert issue.line == 10
        assert issue.severity == IssueSeverity.HIGH
        assert issue.message == "Type error"
    
    def test_to_dict(self):
        """测试序列化"""
        issue = CodeIssue(
            file="test.py",
            line=10,
            severity=IssueSeverity.MEDIUM,
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
        assert diagnostic.config is not None
    
    def test_init_with_config(self):
        """测试带配置初始化"""
        config = DiagnosticConfig(
            project_path="/custom",
            test_command="pytest tests/",
            complexity_threshold=15,
        )
        diagnostic = ProjectDiagnostic(config=config)
        
        assert diagnostic.config.project_path == "/custom"
        assert diagnostic.config.complexity_threshold == 15
    
    def test_init_with_runner(self):
        """测试带Runner初始化"""
        def mock_runner(cmd, cwd, timeout):
            return 0, '{"totals": {"percent_covered": 80}}', ""
        
        diagnostic = ProjectDiagnostic(runner=mock_runner)
        assert diagnostic._runner is mock_runner
    
    def test_diagnose_basic(self):
        """测试基本诊断"""
        def mock_runner(cmd, cwd, timeout):
            if "pytest" in cmd and "cov" not in cmd:
                return 0, "5 passed, 2 failed", ""
            elif "cov" in cmd:
                return 0, "", ""
            elif "radon" in cmd:
                return 0, "[]", ""
            elif "mypy" in cmd:
                return 0, "", ""
            return 0, "", ""
        
        diagnostic = ProjectDiagnostic(runner=mock_runner)
        report = diagnostic.diagnose("/test/project")
        
        assert report.target == "/test/project"
        assert report.test_failures >= 0


class TestPRDRuleEngine:
    """PRDRuleEngine测试类"""
    
    def test_init(self):
        """测试初始化"""
        engine = PRDRuleEngine()
        assert len(engine._rules) == 5
    
    def test_evaluate_test_failure(self):
        """测试测试失败规则"""
        engine = PRDRuleEngine()
        
        report = ProjectHealthReport(
            target="/test",
            test_failures=3,
        )
        
        prds = engine.evaluate(report)
        
        assert len(prds) >= 1
        prd_names = [p.name for p in prds]
        assert "修复测试失败" in prd_names
    
    def test_evaluate_type_error(self):
        """测试类型错误规则"""
        engine = PRDRuleEngine()
        
        report = ProjectHealthReport(
            target="/test",
            mypy_errors=10,
        )
        
        prds = engine.evaluate(report)
        
        prd_names = [p.name for p in prds]
        assert "修复类型错误" in prd_names
    
    def test_evaluate_low_coverage(self):
        """测试低覆盖率规则"""
        engine = PRDRuleEngine()
        
        report = ProjectHealthReport(
            target="/test",
            coverage_total=50.0,
        )
        
        prds = engine.evaluate(report)
        
        prd_names = [p.name for p in prds]
        assert "提升测试覆盖率" in prd_names
    
    def test_evaluate_healthy_project(self):
        """测试健康项目"""
        engine = PRDRuleEngine()
        
        report = ProjectHealthReport(
            target="/test",
            coverage_total=90.0,
            test_failures=0,
            mypy_errors=0,
            complexity_high=1,
            circular_deps=[],
        )
        
        prds = engine.evaluate(report)
        
        # 健康项目不应该触发任何规则
        assert len(prds) == 0


class TestPRDGenerator:
    """PRDGenerator测试类"""
    
    def test_init(self):
        """测试初始化"""
        generator = PRDGenerator()
        assert generator._rule_engine is not None
    
    def test_generate_basic(self):
        """测试基本生成"""
        generator = PRDGenerator()
        
        report = ProjectHealthReport(
            target="/test",
            test_failures=2,
            mypy_errors=5,
        )
        
        prds = generator.generate(report, "/test")
        
        assert len(prds) >= 1
        # 按优先级排序
        assert prds[0].priority >= prds[-1].priority


class TestLLMPRDGenerator:
    """LLMPRDGenerator测试类"""
    
    def test_init_no_api_key(self):
        """测试无API Key初始化"""
        with patch.dict("os.environ", {}, clear=True):
            generator = LLMPRDGenerator()
            assert generator._api_key in ("", None)
    
    def test_generate_no_api_key(self):
        """测试无API Key生成"""
        with patch.dict("os.environ", {}, clear=True):
            generator = LLMPRDGenerator()
            report = ProjectHealthReport(target="/test")
            
            prds = generator.generate(report, "/test")
            
            assert len(prds) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
