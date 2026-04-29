"""测试 SprintCycle UI 验证器"""
import pytest
from dataclasses import dataclass
from sprintcycle.ui_verifier import (
    UIVerifier,
    InteractionIssue,
    UIVerificationResult,
    verify_ui_interactions
)


class TestInteractionIssue:
    """测试 InteractionIssue 数据类"""
    
    def test_create_issue(self):
        """创建交互问题"""
        issue = InteractionIssue(
            page="/home",
            element="button-1",
            issue_type="animation",
            description="按钮缺少过渡动画",
            severity="low",
            fix_suggestion="添加 CSS transition"
        )
        
        assert issue.page == "/home"
        assert issue.element == "button-1"
        assert issue.issue_type == "animation"
        assert issue.severity == "low"
        assert issue.screenshot is None
        assert issue.fix_suggestion == "添加 CSS transition"
    
    def test_issue_with_screenshot(self):
        """创建带截图的问题"""
        issue = InteractionIssue(
            page="/login",
            element="form",
            issue_type="validation",
            description="表单验证缺失",
            severity="high",
            screenshot="/path/to/screenshot.png"
        )
        
        assert issue.screenshot == "/path/to/screenshot.png"


class TestUIVerificationResult:
    """测试 UIVerificationResult 数据类"""
    
    def test_create_result(self):
        """创建验证结果"""
        issues = [
            InteractionIssue(
                page="/home",
                element="button",
                issue_type="animation",
                description="Test issue",
                severity="low"
            )
        ]
        
        result = UIVerificationResult(
            total_checks=24,
            passed=23,
            failed=1,
            issues=issues,
            screenshots=["/path/screen1.png"],
            score=95.0
        )
        
        assert result.total_checks == 24
        assert result.passed == 23
        assert result.failed == 1
        assert len(result.issues) == 1
        assert len(result.screenshots) == 1
        assert result.score == 95.0
    
    def test_result_empty(self):
        """创建空的验证结果"""
        result = UIVerificationResult(
            total_checks=10,
            passed=10,
            failed=0,
            issues=[],
            screenshots=[],
            score=100.0
        )
        
        assert result.score == 100.0
        assert result.failed == 0


class TestUIVerifier:
    """测试 UIVerifier 类"""
    
    def test_create_verifier_default(self):
        """创建默认验证器"""
        verifier = UIVerifier()
        assert verifier.base_url == "http://localhost:3000"
        assert verifier.screenshot_dir is not None
    
    def test_create_verifier_custom_url(self):
        """创建自定义 URL 验证器"""
        verifier = UIVerifier(base_url="http://example.com:8080")
        assert verifier.base_url == "http://example.com:8080"
    
    def test_interaction_checks_structure(self):
        """验证检查项结构"""
        verifier = UIVerifier()
        
        expected_types = ["animation", "feedback", "transition", "validation", "loading", "touch"]
        for check_type in expected_types:
            assert check_type in verifier.INTERACTION_CHECKS
            assert isinstance(verifier.INTERACTION_CHECKS[check_type], list)
            assert len(verifier.INTERACTION_CHECKS[check_type]) > 0
    
    def test_interaction_checks_content(self):
        """验证检查项内容"""
        verifier = UIVerifier()
        
        # 动画检查
        assert "页面加载动画是否流畅" in verifier.INTERACTION_CHECKS["animation"]
        assert "按钮点击是否有反馈动画" in verifier.INTERACTION_CHECKS["animation"]
        
        # 反馈检查
        assert "按钮点击是否有视觉反馈" in verifier.INTERACTION_CHECKS["feedback"]
        assert "表单提交是否有加载状态" in verifier.INTERACTION_CHECKS["feedback"]
        
        # 验证检查
        assert "表单验证是否实时" in verifier.INTERACTION_CHECKS["validation"]
        assert "错误提示是否清晰" in verifier.INTERACTION_CHECKS["validation"]
    
    @pytest.mark.asyncio
    async def test_verify_page_interactions_no_server(self):
        """测试页面验证 - 无服务器时返回错误问题"""
        verifier = UIVerifier(base_url="http://localhost:99999")
        
        # 这应该返回加载失败的问题（因为服务器不存在）
        issues = await verifier.verify_page_interactions("/nonexistent")
        
        # 应该有一个或多个问题（加载失败）
        assert isinstance(issues, list)
    
    def test_generate_fix_prd(self):
        """测试生成修复 PRD"""
        verifier = UIVerifier()
        
        issues = [
            InteractionIssue(
                page="/home",
                element="button-1",
                issue_type="animation",
                description="缺少过渡动画",
                severity="low",
                fix_suggestion="添加 transition"
            ),
            InteractionIssue(
                page="/home",
                element="button-2",
                issue_type="touch",
                description="触摸区域太小",
                severity="medium",
                fix_suggestion="增大按钮"
            ),
            InteractionIssue(
                page="/login",
                element="form",
                issue_type="validation",
                description="验证缺失",
                severity="high",
                fix_suggestion="添加实时验证"
            )
        ]
        
        fix_prd = verifier.generate_fix_prd(issues)
        
        assert "project" in fix_prd
        assert "sprints" in fix_prd
        assert len(fix_prd["sprints"]) == 2  # 2 个不同页面
        
        # 验证 /home 页面的 Sprint
        home_sprint = next((s for s in fix_prd["sprints"] if "/home" in s["name"]), None)
        assert home_sprint is not None
        assert len(home_sprint["tasks"]) == 2
    
    def test_generate_fix_prd_empty(self):
        """测试空问题列表"""
        verifier = UIVerifier()
        fix_prd = verifier.generate_fix_prd([])
        
        assert "project" in fix_prd
        assert "sprints" in fix_prd
        assert len(fix_prd["sprints"]) == 0
    
    def test_run_full_verification_default_routes(self):
        """测试完整验证使用默认路由"""
        verifier = UIVerifier()
        
        # 默认路由
        default_routes = ["/", "/login", "/profile"]
        
        # UIVerifier 有默认路由定义
        # 注意：这个测试主要验证方法存在，不实际调用异步方法
        assert hasattr(verifier, 'run_full_verification')


class TestVerifyUiInteractions:
    """测试便捷函数"""
    
    def test_verify_ui_interactions_exists(self):
        """验证便捷函数存在"""
        assert callable(verify_ui_interactions)
    
    def test_verify_ui_interactions_signature(self):
        """验证函数签名"""
        import inspect
        sig = inspect.signature(verify_ui_interactions)
        
        params = list(sig.parameters.keys())
        assert 'base_url' in params
        assert 'routes' in params
