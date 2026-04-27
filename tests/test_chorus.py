"""SprintCycle Chorus 模块测试"""
import sys
import pytest
from pathlib import Path

# 确保 /root/sprintcycle 在路径中
_root = Path("/root/sprintcycle")
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# 现在导入
from sprintcycle.chorus import (
    Config, ToolType, AgentType, TaskStatus, 
    ExecutionResult, TaskProgress, KnowledgeBase,
    ExecutionLayer, ChorusAdapter, Chorus
)


class TestAgentType:
    """测试 AgentType 枚举"""
    
    def test_agent_type_enum_values(self):
        """测试 AgentType 枚举值"""
        assert AgentType.CODER.value == "coder"
        assert AgentType.REVIEWER.value == "reviewer"
        assert AgentType.ARCHITECT.value == "architect"
        assert AgentType.TESTER.value == "tester"
        assert AgentType.DIAGNOSTIC.value == "diagnostic"
        assert AgentType.UI_VERIFY.value == "ui_verify"
    
    def test_agent_type_count(self):
        """测试 AgentType 枚举数量"""
        assert len(AgentType) == 6


class TestToolType:
    """测试 ToolType 枚举"""
    
    def test_tool_type_values(self):
        """测试 ToolType 枚举值"""
        assert ToolType.CURSOR.value == "cursor"
        assert ToolType.CLAUDE.value == "claude"
        assert ToolType.AIDER.value == "aider"


class TestTaskStatus:
    """测试 TaskStatus 枚举"""
    
    def test_task_status_values(self):
        """测试 TaskStatus 枚举值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRYING.value == "retrying"


class TestExecutionResult:
    """测试 ExecutionResult 数据类"""
    
    def test_execution_result_creation(self):
        """测试 ExecutionResult 创建"""
        result = ExecutionResult(
            success=True,
            output="test output",
            duration=1.5,
            tool="aider"
        )
        assert result.success == True
        assert result.output == "test output"
        assert result.duration == 1.5
        assert result.tool == "aider"
        assert result.retries == 0
        assert result.files_changed == {"added": [], "modified": [], "deleted": [], "screenshots": []}
    
    def test_execution_result_with_files(self):
        """测试带文件变更的 ExecutionResult"""
        files_changed = {
            "added": ["new_file.py"],
            "modified": ["existing.py"],
            "deleted": [],
            "screenshots": []
        }
        result = ExecutionResult(
            success=True,
            output="",
            duration=2.0,
            tool="aider",
            files_changed=files_changed
        )
        assert result.files_changed["added"] == ["new_file.py"]
        assert result.files_changed["modified"] == ["existing.py"]


class TestTaskProgress:
    """测试 TaskProgress 数据类"""
    
    def test_task_progress_creation(self):
        """测试 TaskProgress 创建"""
        progress = TaskProgress(
            task_id="task_001",
            status=TaskStatus.RUNNING,
            progress=50,
            message="处理中"
        )
        assert progress.task_id == "task_001"
        assert progress.status == TaskStatus.RUNNING
        assert progress.progress == 50
        assert progress.message == "处理中"


class TestKnowledgeBase:
    """测试 KnowledgeBase 类"""
    
    def test_knowledge_base_init(self, tmp_path):
        """测试 KnowledgeBase 初始化"""
        kb = KnowledgeBase(str(tmp_path))
        assert kb.path == tmp_path / ".sprintcycle" / "knowledge.json"
        assert "tasks" in kb.data
        assert "patterns" in kb.data
        assert "solutions" in kb.data
    
    def test_get_stats_empty(self, tmp_path):
        """测试空知识库的统计"""
        kb = KnowledgeBase(str(tmp_path))
        stats = kb.get_stats()
        assert stats["total"] == 0
        assert stats["success_rate"] == 0
    
    def test_find_similar_no_history(self, tmp_path):
        """测试无历史记录时查找相似任务"""
        kb = KnowledgeBase(str(tmp_path))
        results = kb.find_similar("修复bug")
        assert results == []


class TestExecutionLayer:
    """测试 ExecutionLayer 类"""
    
    def test_execution_layer_init(self):
        """测试 ExecutionLayer 初始化"""
        layer = ExecutionLayer()
        assert layer.config is not None
        assert isinstance(layer.config, dict)
    
    def test_list_available(self):
        """测试列出可用工具"""
        layer = ExecutionLayer()
        available = layer.list_available()
        assert isinstance(available, dict)
        assert "cursor" in available
        assert "claude" in available
        assert "aider" in available


class TestChorusAdapter:
    """测试 ChorusAdapter 类"""
    
    def test_chorus_adapter_init(self):
        """测试 ChorusAdapter 初始化"""
        adapter = ChorusAdapter()
        assert adapter.executor is not None
        assert adapter.available is not None
    
    def test_route_default(self):
        """测试默认路由"""
        adapter = ChorusAdapter()
        tool = adapter.route()
        assert tool in [ToolType.AIDER, ToolType.CLAUDE, ToolType.CURSOR]


class TestChorus:
    """测试 Chorus 类"""
    
    def test_chorus_init(self):
        """测试 Chorus 初始化"""
        chorus = Chorus()
        assert chorus.adapter is not None
        assert chorus.kb is None
        assert chorus.history == []
    
    def test_analyze_coder_task(self):
        """测试分析编码任务"""
        chorus = Chorus()
        agent = chorus.analyze("修复登录页面的bug")
        assert agent == AgentType.CODER
    
    def test_analyze_review_task(self):
        """测试分析审查任务"""
        chorus = Chorus()
        agent = chorus.analyze("审查代码")
        assert agent == AgentType.REVIEWER
        
        agent = chorus.analyze("review the code")
        assert agent == AgentType.REVIEWER
        
        agent = chorus.analyze("代码审查")
        assert agent == AgentType.REVIEWER
    
    def test_analyze_architect_task(self):
        """测试分析架构任务"""
        chorus = Chorus()
        agent = chorus.analyze("设计系统架构")
        assert agent == AgentType.ARCHITECT
        
        agent = chorus.analyze("提供技术方案")
        assert agent == AgentType.ARCHITECT
    
    def test_analyze_tester_task(self):
        """测试分析测试任务"""
        chorus = Chorus()
        agent = chorus.analyze("运行单元测试")
        assert agent == AgentType.TESTER
        
        agent = chorus.analyze("编写集成测试")
        assert agent == AgentType.TESTER
    
    def test_analyze_ui_verify_task(self):
        """测试分析 UI 验证任务"""
        chorus = Chorus()
        agent = chorus.analyze("验证登录页面UI")
        assert agent == AgentType.UI_VERIFY
        
        agent = chorus.analyze("界面交互检查")
        assert agent == AgentType.UI_VERIFY


class TestConfig:
    """测试 Config 类"""
    
    def test_config_load(self):
        """测试配置加载"""
        config = Config.load()
        assert isinstance(config, dict)
        assert "aider" in config
        assert "claude" in config
        assert "cursor" in config
    
    def test_default_config_structure(self):
        """测试默认配置结构"""
        config = Config.DEFAULT_CONFIG
        assert "aider" in config
        assert config["aider"]["command"] == "/root/aider-venv/bin/aider"
        assert config["aider"]["model"] == "deepseek/deepseek-chat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
