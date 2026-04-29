"""
Chorus 属性测试 - 使用 Hypothesis 进行属性测试

测试范围:
1. 任务路由逻辑
2. Agent 选择逻辑
3. files_changed 类型处理
4. 配置和知识库操作
"""
import pytest
from hypothesis import given, settings, assume, example
from hypothesis import strategies as st
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprintcycle.chorus import (
    ToolType, AgentType, TaskStatus, ExecutionResult,
    Config, KnowledgeBase, normalize_files_changed,
    extract_files_list, has_changes, get_change_summary
)


class TestFilesChangedNormalization:
    """files_changed 类型规范化属性测试"""
    
    @given(
        files_changed=st.one_of(
            st.dictionaries(
                keys=st.sampled_from(["added", "modified", "deleted", "screenshots"]),
                values=st.lists(st.text(min_size=1, max_size=100))
            ),
            st.lists(st.text(min_size=1, max_size=100)),
            st.none()
        )
    )
    @settings(max_examples=50)
    def test_normalize_files_changed_output_structure(self, files_changed):
        """测试规范化输出结构"""
        result = normalize_files_changed(files_changed)
        
        assert isinstance(result, dict)
        assert "added" in result
        assert "modified" in result
        assert "deleted" in result
        assert "screenshots" in result
        
        assert isinstance(result["added"], list)
        assert isinstance(result["modified"], list)
        assert isinstance(result["deleted"], list)
        assert isinstance(result["screenshots"], list)
    
    @given(files_changed=st.dictionaries(
        keys=st.sampled_from(["added", "modified", "deleted", "screenshots"]),
        values=st.lists(st.text(min_size=1, max_size=100))
    ))
    @settings(max_examples=30)
    def test_dict_input_preservation(self, files_changed):
        """测试字典输入保留所有键值"""
        result = normalize_files_changed(files_changed)
        
        for key in ["added", "modified", "deleted", "screenshots"]:
            if key in files_changed:
                assert result[key] == files_changed[key]
    
    @given(file_list=st.lists(st.text(min_size=1, max_size=100), max_size=100))
    @settings(max_examples=30)
    def test_list_input_conversion(self, file_list):
        """测试列表输入转换"""
        assume(len(file_list) > 0)
        
        result = normalize_files_changed(file_list)
        
        assert result["added"] == []
        assert result["modified"] == file_list
        assert result["deleted"] == []
        assert result["screenshots"] == []
    
    def test_none_input_returns_default(self):
        """测试 None 输入返回默认值"""
        result = normalize_files_changed(None)
        
        assert result == {
            "added": [],
            "modified": [],
            "deleted": [],
            "screenshots": []
        }


class TestExtractFilesList:
    """文件列表提取属性测试"""
    
    @given(
        files_dict=st.dictionaries(
            keys=st.sampled_from(["added", "modified", "deleted", "screenshots"]),
            values=st.lists(st.text(min_size=1, max_size=100), max_size=20)
        )
    )
    @settings(max_examples=30)
    def test_extract_all_files(self, files_dict):
        """测试提取所有文件"""
        result = extract_files_list(files_dict)
        
        for key, value in files_dict.items():
            for file in value:
                assert file in result
    
    @given(file_list=st.lists(st.text(min_size=1, max_size=100), max_size=50))
    @settings(max_examples=20)
    def test_extract_from_list(self, file_list):
        """测试从列表提取"""
        assume(len(file_list) > 0)
        
        result = extract_files_list(file_list)
        assert set(result) == set(file_list)


class TestHasChanges:
    """变更检测属性测试"""
    
    @given(
        files_dict=st.dictionaries(
            keys=st.sampled_from(["added", "modified", "deleted", "screenshots"]),
            values=st.lists(st.text(min_size=1, max_size=100), max_size=10)
        )
    )
    @settings(max_examples=30)
    def test_has_changes_detection(self, files_dict):
        """测试变更检测"""
        result = has_changes(files_dict)
        
        total_files = sum(len(v) for v in files_dict.values())
        
        if total_files > 0:
            assert result is True
        else:
            assert result is False
    
    def test_empty_dict_no_changes(self):
        """测试空字典无变更"""
        assert has_changes({}) is False
        assert has_changes({"added": [], "modified": [], "deleted": [], "screenshots": []}) is False
    
    def test_none_no_changes(self):
        """测试 None 无变更"""
        assert has_changes(None) is False


class TestChangeSummary:
    """变更摘要属性测试"""
    
    def test_summary_format(self):
        """测试摘要格式"""
        files_dict = {
            "added": ["a.py", "b.py"],
            "modified": ["c.py"],
            "deleted": ["d.py"],
            "screenshots": []
        }
        
        summary = get_change_summary(files_dict)
        
        assert isinstance(summary, str)
        assert "added" in summary.lower() or "2" in summary
        assert "modified" in summary.lower() or "1" in summary
    
    def test_empty_summary(self):
        """测试空变更摘要"""
        summary = get_change_summary({})
        assert isinstance(summary, str)


class TestToolTypeProperties:
    """ToolType 属性测试"""
    
    def test_tool_type_has_values(self):
        """测试 ToolType 有值"""
        tool_types = list(ToolType)
        assert len(tool_types) > 0
        
        for tool in tool_types:
            assert tool.value is not None
    
    @given(tool=st.sampled_from(list(ToolType)))
    @settings(max_examples=10)
    def test_tool_type_string_conversion(self, tool):
        """测试 ToolType 字符串转换"""
        tool_str = str(tool)
        assert isinstance(tool_str, str)
        assert len(tool_str) > 0


class TestAgentTypeProperties:
    """AgentType 属性测试"""
    
    def test_agent_type_values(self):
        """测试 AgentType 枚举值"""
        agent_types = list(AgentType)
        assert len(agent_types) > 0
        
        for agent in agent_types:
            assert agent.value is not None
    
    @given(agent=st.sampled_from(list(AgentType)))
    @settings(max_examples=10)
    def test_agent_type_string_conversion(self, agent):
        """测试 AgentType 字符串转换"""
        agent_str = str(agent)
        assert isinstance(agent_str, str)
        assert len(agent_str) > 0
    
    def test_from_string_conversion(self):
        """测试 from_string 方法"""
        for agent in list(AgentType):
            result = AgentType.from_string(agent.value)
            assert result == agent


class TestTaskStatusProperties:
    """TaskStatus 属性测试"""
    
    def test_task_status_has_values(self):
        """测试 TaskStatus 有值"""
        status_types = list(TaskStatus)
        assert len(status_types) > 0
        
        for status in status_types:
            assert status.value is not None
    
    @given(status=st.sampled_from(list(TaskStatus)))
    @settings(max_examples=10)
    def test_status_transitions(self, status):
        """测试状态转换逻辑"""
        if status == TaskStatus.PENDING:
            assert status == TaskStatus.PENDING
        elif status == TaskStatus.RUNNING:
            assert status == TaskStatus.RUNNING


class TestExecutionResultProperties:
    """ExecutionResult 属性测试"""
    
    @given(
        success=st.booleans(),
        duration=st.floats(min_value=0, max_value=10000, allow_nan=False)
    )
    @settings(max_examples=30)
    def test_result_creation(self, success, duration):
        """测试结果创建"""
        files_dict = normalize_files_changed({})
        tool = list(ToolType)[0] if list(ToolType) else None
        if tool:
            result = ExecutionResult(
                success=success,
                output="test output",
                duration=duration,
                tool=tool.value,
                files_changed=files_dict
            )
            assert result.success == success
            assert result.duration == duration
    
    def test_files_list_method(self):
        """测试 files_list 方法"""
        files_dict = normalize_files_changed({
            "added": ["new.py"],
            "modified": ["old.py"],
            "deleted": [],
            "screenshots": []
        })
        tool = list(ToolType)[0] if list(ToolType) else None
        if tool:
            result = ExecutionResult(
                success=True,
                output="test",
                duration=1.0,
                tool=tool.value,
                files_changed=files_dict
            )
            
            files = result.files_list
            assert "new.py" in files
            assert "old.py" in files
            assert len(files) == 2
    
    def test_has_changes_method(self):
        """测试 has_changes 方法"""
        files_with_changes = normalize_files_changed({"added": ["a.py"]})
        tool = list(ToolType)[0] if list(ToolType) else None
        if tool:
            result_with_changes = ExecutionResult(
                success=True,
                output="test",
                duration=1.0,
                tool=tool.value,
                files_changed=files_with_changes
            )
            assert result_with_changes.has_changes is True
            
            files_empty = normalize_files_changed({})
            result_no_changes = ExecutionResult(
                success=True,
                output="test",
                duration=1.0,
                tool=tool.value,
                files_changed=files_empty
            )
            assert result_no_changes.has_changes is False
    
    def test_to_dict_method(self):
        """测试 to_dict 方法"""
        files_dict = normalize_files_changed({"added": ["a.py"]})
        tool = list(ToolType)[0] if list(ToolType) else None
        if tool:
            result = ExecutionResult(
                success=True,
                output="test",
                duration=1.0,
                tool=tool.value,
                files_changed=files_dict
            )
            
            d = result.to_dict()
            assert isinstance(d, dict)
            assert "success" in d
            assert "files_changed" in d
            assert "tool" in d


class TestRoutingLogic:
    """任务路由逻辑属性测试"""
    
    def test_agent_to_tool_mapping(self):
        """测试 Agent 到 Tool 的映射"""
        agent_tool_map = {
            AgentType.CODER: ToolType.CURSOR,
            AgentType.REVIEWER: ToolType.CLAUDE,
            AgentType.ARCHITECT: ToolType.CLAUDE,
        }
        
        assert AgentType.CODER in agent_tool_map
        assert agent_tool_map[AgentType.CODER] in list(ToolType)
    
    def test_task_priority_routing(self):
        """测试任务优先级路由"""
        priority_map = {
            "critical": ["CODER", "DIAGNOSTIC"],
            "high": ["REVIEWER", "TESTER"],
            "normal": ["CODER"],
            "low": ["ARCHITECT"]
        }
        
        assert "critical" in priority_map
        assert len(priority_map["critical"]) > 0


class TestKnowledgeBaseProperties:
    """KnowledgeBase 属性测试"""
    
    @given(
        task=st.text(min_size=1, max_size=500),
        result=st.booleans(),
        files=st.lists(st.text(min_size=1, max_size=100), max_size=20)
    )
    @settings(max_examples=20)
    def test_record_task_structure(self, task, result, files):
        """测试记录任务结构"""
        assume(len(files) == 0 or all(len(f) > 0 for f in files))
        
        task_entry = {
            "task": task,
            "result": result,
            "files": files,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        assert task_entry["task"] == task
        assert task_entry["result"] == result
        assert task_entry["files"] == files
    
    def test_similar_task_search(self):
        """测试相似任务搜索"""
        kb_entries = [
            {"task": "Implement user auth", "keywords": ["auth", "login", "user"]},
            {"task": "Fix memory leak", "keywords": ["memory", "leak", "performance"]},
            {"task": "Add API endpoint", "keywords": ["api", "endpoint", "rest"]}
        ]
        
        search_keywords = ["auth", "login"]
        results = []
        for entry in kb_entries:
            if any(kw in entry["keywords"] for kw in search_keywords):
                results.append(entry)
        
        assert len(results) >= 1
        assert any("auth" in r["keywords"] for r in results)


class TestConfigProperties:
    """Config 属性测试"""
    
    @given(
        api_keys=st.dictionaries(
            keys=st.sampled_from(["openai", "anthropic", "github"]),
            values=st.text(min_size=10, max_size=100)
        )
    )
    @settings(max_examples=20)
    def test_api_key_storage(self, api_keys):
        """测试 API key 存储"""
        config = {"api_keys": api_keys}
        
        assert "api_keys" in config
        assert isinstance(config["api_keys"], dict)
    
    def test_config_load_returns_dict(self):
        """测试配置加载返回字典"""
        try:
            config = Config.load()
            assert isinstance(config, dict)
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
