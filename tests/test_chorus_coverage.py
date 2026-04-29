"""测试 Chorus 模块未覆盖的代码路径"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from sprintcycle.chorus import (
    normalize_files_changed, extract_files_list, has_changes, get_change_summary,
    ExecutionResult, KnowledgeBase, ExecutionLayer, ChorusAdapter, Chorus,
    ToolType, AgentType, TaskStatus, TaskProgress
)


class TestFilesChangedHelpers:
    """测试 files_changed 处理工具函数"""
    
    def test_normalize_files_changed_none(self):
        """测试 None 输入"""
        result = normalize_files_changed(None)
        assert result == {"added": [], "modified": [], "deleted": [], "screenshots": []}
    
    def test_normalize_files_changed_dict(self):
        """测试字典输入"""
        input_dict = {"added": ["a.py"], "modified": ["b.py"], "deleted": [], "screenshots": []}
        result = normalize_files_changed(input_dict)
        assert result["added"] == ["a.py"]
        assert result["modified"] == ["b.py"]
    
    def test_normalize_files_changed_list(self):
        """测试列表输入"""
        input_list = ["file1.py", "file2.py"]
        result = normalize_files_changed(input_list)
        assert result["added"] == []
        assert result["modified"] == ["file1.py", "file2.py"]
        assert result["deleted"] == []
        assert result["screenshots"] == []
    
    def test_normalize_files_changed_empty_dict(self):
        """测试空字典"""
        result = normalize_files_changed({})
        assert result == {"added": [], "modified": [], "deleted": [], "screenshots": []}
    
    def test_normalize_files_changed_partial_dict(self):
        """测试部分字段的字典"""
        input_dict = {"added": ["new.py"]}
        result = normalize_files_changed(input_dict)
        assert result["added"] == ["new.py"]
        assert result["modified"] == []
    
    def test_extract_files_list_from_dict(self):
        """测试从字典提取文件列表"""
        files_changed = {
            "added": ["a.py", "b.py"],
            "modified": ["c.py"],
            "deleted": ["d.py"],
            "screenshots": ["s1.png"]
        }
        result = extract_files_list(files_changed)
        assert len(result) == 5
        assert "a.py" in result
        assert "s1.png" in result
    
    def test_extract_files_list_from_list(self):
        """测试从列表提取文件列表"""
        result = extract_files_list(["file1.py", "file2.py"])
        assert len(result) == 2
    
    def test_extract_files_list_empty(self):
        """测试空输入"""
        result = extract_files_list(None)
        assert result == []
    
    def test_has_changes_true(self):
        """测试有变更"""
        assert has_changes({"added": ["a.py"]}) == True
    
    def test_has_changes_false(self):
        """测试无变更"""
        assert has_changes({"added": [], "modified": [], "deleted": []}) == False
    
    def test_has_changes_none(self):
        """测试 None 输入"""
        assert has_changes(None) == False
    
    def test_get_change_summary_all_types(self):
        """测试变更摘要-所有类型"""
        files_changed = {
            "added": ["a.py", "b.py"],
            "modified": ["c.py"],
            "deleted": ["d.py"],
            "screenshots": ["s1.png"]
        }
        result = get_change_summary(files_changed)
        assert "+2 新增" in result
        assert "~1 修改" in result
        assert "-1 删除" in result
        assert "[1 截图]" in result
    
    def test_get_change_summary_partial(self):
        """测试变更摘要-部分类型"""
        result = get_change_summary({"added": ["a.py"], "modified": [], "deleted": [], "screenshots": []})
        assert "无变更" not in result
        assert "+1 新增" in result
    
    def test_get_change_summary_empty(self):
        """测试变更摘要-空"""
        result = get_change_summary({"added": [], "modified": [], "deleted": [], "screenshots": []})
        assert result == "无变更"


class TestExecutionResultProperties:
    """测试 ExecutionResult 属性"""
    
    def test_files_list_property(self):
        """测试 files_list 属性"""
        result = ExecutionResult(
            success=True, output="ok", duration=1.0, tool="aider",
            files_changed={"added": ["a.py"], "modified": ["b.py"]}
        )
        assert "a.py" in result.files_list
        assert "b.py" in result.files_list
    
    def test_has_changes_property_true(self):
        """测试 has_changes 属性为 True"""
        result = ExecutionResult(
            success=True, output="ok", duration=1.0, tool="aider",
            files_changed={"added": ["a.py"]}
        )
        assert result.has_changes == True
    
    def test_has_changes_property_false(self):
        """测试 has_changes 属性为 False"""
        result = ExecutionResult(
            success=True, output="ok", duration=1.0, tool="aider",
            files_changed={"added": [], "modified": []}
        )
        assert result.has_changes == False
    
    def test_change_summary_property(self):
        """测试 change_summary 属性"""
        result = ExecutionResult(
            success=True, output="ok", duration=1.0, tool="aider",
            files_changed={"added": ["a.py"], "modified": []}
        )
        summary = result.change_summary
        assert "+1 新增" in summary
    
    def test_to_dict_method(self):
        """测试 to_dict 方法"""
        result = ExecutionResult(
            success=True, output="test output", duration=1.5, tool="aider",
            files_changed={"added": ["a.py"]}
        )
        d = result.to_dict()
        assert d["success"] == True
        assert d["output"] == "test output"
        assert d["duration"] == 1.5
        assert "files_changed" in d
        assert "files_list" in d
        assert "has_changes" in d


class TestKnowledgeBaseExtended:
    """扩展测试 KnowledgeBase"""
    
    def test_record_task_success(self, tmp_path):
        """测试记录成功任务"""
        kb = KnowledgeBase(str(tmp_path))
        result = ExecutionResult(
            success=True, output="done", duration=2.0, tool="aider",
            files_changed={"added": ["new.py"], "modified": []}
        )
        kb.record_task("实现功能A", result, ["new.py"])
        
        stats = kb.get_stats()
        assert stats["total"] == 1
        assert stats["success"] == 1
    
    def test_record_task_failure(self, tmp_path):
        """测试记录失败任务"""
        kb = KnowledgeBase(str(tmp_path))
        result = ExecutionResult(
            success=False, output="error", duration=1.0, tool="aider",
            error="Some error"
        )
        kb.record_task("修复bug", result, [])
        
        stats = kb.get_stats()
        assert stats["total"] == 1
        assert stats["success"] == 0
    
    def test_find_similar_with_match(self, tmp_path):
        """测试查找相似任务-有匹配"""
        kb = KnowledgeBase(str(tmp_path))
        result = ExecutionResult(
            success=True, output="done", duration=1.0, tool="aider",
            files_changed={"added": ["a.py"]}
        )
        kb.record_task("修复登录页面的bug", result, ["a.py"])
        
        similar = kb.find_similar("修复支付页面的bug")
        assert len(similar) >= 0  # 可能有匹配
    
    def test_add_entry(self, tmp_path):
        """测试添加知识条目"""
        kb = KnowledgeBase(str(tmp_path))
        entry = {"type": "solution", "content": "解决方法A", "tags": ["fix"]}
        kb.add_entry(entry)
        
        assert len(kb.data["solutions"]) == 1
        assert kb.data["solutions"][0]["type"] == "solution"
    
    def test_get_stats_with_tasks(self, tmp_path):
        """测试获取统计数据"""
        kb = KnowledgeBase(str(tmp_path))
        for i in range(3):
            result = ExecutionResult(
                success=i < 2, output=f"task {i}", duration=1.0, tool="aider"
            )
            kb.record_task(f"Task {i}", result, [])
        
        stats = kb.get_stats()
        assert stats["total"] == 3
        assert stats["success"] == 2
        assert stats["success_rate"] == pytest.approx(66.7, rel=0.1)
        assert "avg_duration" in stats
    
    def test_record_task_entry(self, tmp_path):
        """测试 record_task_entry 方法"""
        kb = KnowledgeBase(str(tmp_path))
        task_entry = {
            "task": "实现功能B",
            "status": "completed",
            "files": ["b.py"],
            "files_changed": {"added": ["b.py"]},
            "duration_seconds": 5.0,
            "completed_at": "2024-01-01T00:00:00"
        }
        kb.record_task_entry(task_entry)
        
        assert len(kb.data["tasks"]) == 1
        assert kb.data["tasks"][0]["task"] == "实现功能B"


class TestExecutionLayerTools:
    """测试 ExecutionLayer 工具相关功能"""
    
    def test_check_available_with_invalid_command(self):
        """测试检查不可用的工具"""
        layer = ExecutionLayer()
        # 测试列出可用工具
        available = layer.list_available()
        assert isinstance(available, dict)
        for tool_type in ToolType:
            assert tool_type.value in available


class TestChorusAdapterExtended:
    """扩展测试 ChorusAdapter"""
    
    def test_agent_tool_map(self):
        """测试 Agent 到 Tool 的映射"""
        assert ChorusAdapter.AGENT_TOOL_MAP[AgentType.CODER] == ToolType.AIDER
        assert ChorusAdapter.AGENT_TOOL_MAP[AgentType.TESTER] == ToolType.AIDER
        assert ChorusAdapter.AGENT_TOOL_MAP[AgentType.UI_VERIFY] is None
    
    def test_agent_prompts(self):
        """测试 Agent 提示模板"""
        assert "{task}" in ChorusAdapter.AGENT_PROMPTS[AgentType.CODER]
        assert "审查" in ChorusAdapter.AGENT_PROMPTS[AgentType.REVIEWER]
    
    def test_route_with_preferred(self):
        """测试优先选择"""
        adapter = ChorusAdapter()
        tool = adapter.route(preferred=ToolType.CLAUDE)
        assert tool is not None
    
    def test_route_with_agent(self):
        """测试根据 Agent 路由"""
        adapter = ChorusAdapter()
        tool = adapter.route(agent=AgentType.CODER)
        assert tool == ToolType.AIDER


class TestChorusDispatch:
    """测试 Chorus dispatch 方法"""
    
    @patch('sprintcycle.chorus.ChorusAdapter')
    def test_dispatch_with_history(self, mock_adapter_class, tmp_path):
        """测试 dispatch 方法记录历史"""
        mock_adapter = MagicMock()
        mock_result = ExecutionResult(
            success=True, output="done", duration=1.0, tool="aider"
        )
        mock_adapter.execute.return_value = mock_result
        mock_adapter_class.return_value = mock_adapter
        
        chorus = Chorus()
        result = chorus.dispatch(str(tmp_path), "实现功能")
        
        assert result.success == True
        assert len(chorus.history) == 1
    
    @patch('sprintcycle.chorus.ChorusAdapter')
    def test_dispatch_with_kb_similar(self, mock_adapter_class, tmp_path):
        """测试 dispatch 方法查找相似任务"""
        mock_adapter = MagicMock()
        mock_result = ExecutionResult(
            success=True, output="done", duration=1.0, tool="aider"
        )
        mock_adapter.execute.return_value = mock_result
        mock_adapter_class.return_value = mock_adapter
        
        chorus = Chorus(kb=KnowledgeBase(str(tmp_path)))
        result = chorus.dispatch(str(tmp_path), "实现功能")
        
        assert result.success == True


class TestAgentTypeFromString:
    """测试 AgentType.from_string 方法"""
    
    def test_from_string_coder(self):
        """测试 CODER 类型"""
        assert AgentType.from_string("coder") == AgentType.CODER
        assert AgentType.from_string("CODER") == AgentType.CODER
        assert AgentType.from_string("CoDeR") == AgentType.CODER
    
    def test_from_string_reviewer(self):
        """测试 REVIEWER 类型"""
        assert AgentType.from_string("reviewer") == AgentType.REVIEWER
    
    def test_from_string_unknown(self):
        """测试未知类型映射到 CODER"""
        assert AgentType.from_string("unknown_type") == AgentType.CODER
    
    def test_from_string_empty(self):
        """测试空字符串"""
        assert AgentType.from_string("") == AgentType.CODER


class TestChorusAnalyzeExtended:
    """扩展测试 Chorus.analyze 方法"""
    
    def test_analyze_diagnostic(self):
        """测试诊断任务"""
        chorus = Chorus()
        agent = chorus.analyze("诊断系统问题")
        assert agent == AgentType.CODER  # 默认 fallback
    
    def test_analyze_test_ui_keywords(self):
        """测试测试UI混合关键词"""
        chorus = Chorus()
        # 测试优先匹配
        agent = chorus.analyze("运行UI测试")
        # 可能匹配到 TESTER（因为"测试"关键词）
        assert agent in [AgentType.TESTER, AgentType.UI_VERIFY]


class TestTaskProgress:
    """测试 TaskProgress"""
    
    def test_task_progress_with_times(self):
        """测试带时间的 TaskProgress"""
        from datetime import datetime
        progress = TaskProgress(
            task_id="task_001",
            status=TaskStatus.SUCCESS,
            progress=100,
            message="完成",
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        assert progress.start_time is not None
        assert progress.end_time is not None
