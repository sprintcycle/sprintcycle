"""扩展测试 Chorus 核心功能"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sprintcycle.chorus import Chorus, TaskStatus, AgentType


class TestChorusBasic:
    """测试 Chorus 基础功能"""
    
    @pytest.fixture
    def chorus(self):
        """创建 Chorus 实例"""
        return Chorus()
    
    def test_create_chorus(self, chorus):
        """测试创建 Chorus"""
        assert chorus is not None
    
    def test_version(self, chorus):
        """测试版本号"""
        assert hasattr(chorus, 'VERSION')
        assert chorus.VERSION == "v4.10"


class TestChorusTaskStatus:
    """测试任务状态枚举"""
    
    def test_all_status_values(self):
        """验证所有状态值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRYING.value == "retrying"


class TestChorusAgentType:
    """测试 Agent 类型枚举"""
    
    def test_all_agent_types(self):
        """验证所有 Agent 类型"""
        assert AgentType.CODER.value == "coder"
        assert AgentType.REVIEWER.value == "reviewer"
        assert AgentType.TESTER.value == "tester"
        assert AgentType.ARCHITECT.value == "architect"
        assert AgentType.UI_VERIFY.value == "ui_verify"


class TestChorusAnalyze:
    """测试任务分析功能"""
    
    @pytest.fixture
    def chorus(self):
        return Chorus()
    
    def test_analyze_coder_task(self, chorus):
        """分析 coder 任务"""
        agent = chorus.analyze("编写一个函数")
        assert agent == AgentType.CODER
    
    def test_analyze_review_task(self, chorus):
        """分析审查任务"""
        agent = chorus.analyze("审查代码")
        assert agent == AgentType.REVIEWER
    
    def test_analyze_test_task(self, chorus):
        """分析测试任务"""
        agent = chorus.analyze("编写测试用例")
        assert agent == AgentType.TESTER
    
    def test_analyze_ui_verify_task(self, chorus):
        """分析 UI 验证任务"""
        agent = chorus.analyze("验证 UI 交互")
        assert agent == AgentType.UI_VERIFY
    
    def test_analyze_design_task(self, chorus):
        """分析设计任务"""
        agent = chorus.analyze("架构设计")
        assert agent == AgentType.ARCHITECT


class TestChorusHistory:
    """测试历史记录"""
    
    @pytest.fixture
    def chorus(self):
        return Chorus()
    
    def test_history_initialized(self, chorus):
        """测试历史记录初始化"""
        assert hasattr(chorus, 'history')
        assert isinstance(chorus.history, list)
        assert len(chorus.history) == 0


class TestChorusAdapter:
    """测试 ChorusAdapter"""
    
    @pytest.fixture
    def chorus(self):
        return Chorus()
    
    def test_adapter_exists(self, chorus):
        """测试 adapter 存在"""
        assert hasattr(chorus, 'adapter')
