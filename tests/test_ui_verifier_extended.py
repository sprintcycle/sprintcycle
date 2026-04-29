"""扩展UI验证器测试 - 针对 ui_verifier.py 低覆盖率模块"""
import pytest
from sprintcycle.ui_verifier import (
    InteractionIssue,
    UIVerificationResult,
    UIVerifier,
    verify_ui_interactions,
)


class TestInteractionIssue:
    """交互问题测试"""
    
    def test_issue_basic(self):
        """测试基本问题"""
        issue = InteractionIssue(
            page="/test",
            element="button",
            issue_type="animation",
            description="Missing animation",
            severity="medium"
        )
        assert issue.page == "/test"
        assert issue.element == "button"
        assert issue.issue_type == "animation"
    
    def test_issue_full(self):
        """测试完整问题"""
        issue = InteractionIssue(
            page="/form",
            element="submit",
            issue_type="feedback",
            description="No visual feedback",
            severity="high",
            screenshot="/path/to/screenshot.png",
            fix_suggestion="Add onClick handler"
        )
        assert issue.severity == "high"
        assert issue.screenshot == "/path/to/screenshot.png"
        assert issue.fix_suggestion == "Add onClick handler"


class TestUIVerificationResult:
    """UI验证结果测试"""
    
    def test_result_success(self):
        """测试成功结果"""
        result = UIVerificationResult(
            total_checks=10,
            passed=10,
            failed=0,
            issues=[],
            screenshots=[],
            score=100.0
        )
        assert result.passed == 10
        assert result.score == 100.0
    
    def test_result_with_issues(self):
        """测试带问题的结果"""
        issues = [
            InteractionIssue(
                page="/test",
                element="btn",
                issue_type="animation",
                description="Missing",
                severity="medium"
            )
        ]
        result = UIVerificationResult(
            total_checks=10,
            passed=9,
            failed=1,
            issues=issues,
            screenshots=[],
            score=90.0
        )
        assert result.failed == 1
        assert len(result.issues) == 1


class TestUIVerifier:
    """UI验证器测试"""
    
    def test_verifier_initialization(self):
        """测试验证器初始化"""
        verifier = UIVerifier()
        assert verifier is not None
        assert verifier.base_url == "http://localhost:3000"
    
    def test_verifier_custom_url(self):
        """测试自定义URL验证器"""
        verifier = UIVerifier(base_url="http://custom:8080")
        assert verifier.base_url == "http://custom:8080"
    
    def test_interaction_checks_exist(self):
        """测试交互检查项存在"""
        verifier = UIVerifier()
        assert "animation" in verifier.INTERACTION_CHECKS
        assert "feedback" in verifier.INTERACTION_CHECKS
        assert "transition" in verifier.INTERACTION_CHECKS
    
    def test_verify_page_interactions(self):
        """测试页面交互验证"""
        verifier = UIVerifier()
        import inspect
        assert inspect.iscoroutinefunction(verifier.verify_page_interactions)
    
    def test_run_full_verification(self):
        """测试完整验证方法"""
        verifier = UIVerifier()
        import inspect
        assert inspect.iscoroutinefunction(verifier.run_full_verification)
    
    def test_generate_fix_prd(self):
        """测试生成修复PRD"""
        verifier = UIVerifier()
        issues = [
            InteractionIssue(
                page="/test",
                element="btn",
                issue_type="animation",
                description="Missing",
                severity="medium"
            )
        ]
        prd = verifier.generate_fix_prd(issues)
        assert prd is not None
        assert isinstance(prd, dict)
    
    def test_generate_fix_prd_empty(self):
        """测试生成空PRD"""
        verifier = UIVerifier()
        prd = verifier.generate_fix_prd([])
        assert prd is not None


class TestVerifyUiInteractions:
    """UI交互验证函数测试"""
    
    def test_verify_ui_interactions_exists(self):
        """测试验证函数存在"""
        import inspect
        assert inspect.iscoroutinefunction(verify_ui_interactions)
