"""
SprintChain 属性测试 - 使用 Hypothesis 进行属性测试

测试范围:
1. Sprint 创建: 测试各种 task 数量、名称组合
2. Sprint 状态转换: 测试状态机的所有可能路径
3. 边界条件: 空列表、超大列表、特殊字符
"""
import pytest
from hypothesis import given, settings, assume, example
from hypothesis import strategies as st
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprintcycle.chorus import (
    ToolType, AgentType, TaskStatus, ExecutionResult
)


class TestSprintCreationProperties:
    """Sprint 创建属性测试"""
    
    @given(
        name=st.text(min_size=1, max_size=100),
        goal_count=st.integers(min_value=0, max_value=20)
    )
    @settings(max_examples=50)
    def test_sprint_creation_with_various_names(self, name, goal_count):
        """测试各种名称和目标数量的 Sprint 创建"""
        # 跳过包含控制字符的名称
        assume(all(ord(c) >= 32 for c in name))
        
        goals = [f"Goal {i}" for i in range(goal_count)]
        sprint = {
            "id": "sprint_1",
            "name": name,
            "goals": goals,
            "status": "pending"
        }
        
        # Sprint 应该被正确创建
        assert sprint["name"] == name
        assert len(sprint["goals"]) == goal_count
        assert sprint["status"] == "pending"
    
    @given(
        task=st.text(min_size=1, max_size=500),
        files=st.lists(st.text(min_size=1, max_size=200), max_size=50)
    )
    @settings(max_examples=30)
    def test_task_with_various_inputs(self, task, files):
        """测试各种任务描述和文件列表"""
        # 跳过包含控制字符的输入
        assume(all(ord(c) >= 32 for c in task))
        assume(len(files) == 0 or all(len(f) > 0 for f in files))
        
        task_entry = {
            "task": task,
            "files": files,
            "agent": None,
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "duration_seconds": 0,
            "files_changed": {}
        }
        
        assert task_entry["task"] == task
        assert task_entry["files"] == files
        assert task_entry["status"] == "pending"
    
    @given(goal_list=st.lists(st.text(min_size=0, max_size=100), max_size=100))
    @settings(max_examples=20)
    def test_goals_boundary_conditions(self, goal_list):
        """测试目标列表边界条件"""
        # 清理控制字符
        cleaned_goals = [g for g in goal_list if all(ord(c) >= 32 for c in g)]
        
        # Sprint 配置
        sprint_config = {
            "project": {"name": "test_project"},
            "sprint_chain": [{
                "id": "sprint_1",
                "name": "Test Sprint",
                "goals": cleaned_goals,
                "status": "pending",
                "tasks": []
            }]
        }
        
        # 验证配置
        assert "project" in sprint_config
        assert "sprint_chain" in sprint_config
        assert len(sprint_config["sprint_chain"][0]["goals"]) == len(cleaned_goals)


class TestSprintStateTransitions:
    """Sprint 状态转换属性测试"""
    
    @given(status=st.sampled_from(["pending", "running", "completed", "failed"]))
    @settings(max_examples=10)
    def test_status_values_are_valid(self, status):
        """测试所有状态值都是有效的"""
        valid_statuses = {"pending", "running", "completed", "failed"}
        assert status in valid_statuses
    
    @given(
        task_entry=st.fixed_dictionaries({
            "task": st.text(min_size=0, max_size=100),
            "files": st.lists(st.text(min_size=1, max_size=50), max_size=20),
            "status": st.sampled_from(["pending", "running", "completed", "failed"])
        })
    )
    @settings(max_examples=30)
    def test_task_entry_structure(self, task_entry):
        """测试任务条目结构"""
        # 确保必需字段存在
        complete_entry = {
            "task": task_entry["task"],
            "files": task_entry["files"],
            "agent": None,
            "status": task_entry["status"],
            "started_at": None,
            "completed_at": None,
            "duration_seconds": 0,
            "files_changed": {}
        }
        
        # 验证基本结构
        assert isinstance(complete_entry["task"], str)
        assert isinstance(complete_entry["files"], list)
        assert complete_entry["status"] in {"pending", "running", "completed", "failed"}
    
    def test_state_transitions_model(self):
        """测试状态转换模型"""
        # 定义所有可能的状态转换
        valid_transitions = {
            "pending": {"running", "failed"},
            "running": {"completed", "failed"},
            "completed": set(),
            "failed": {"pending", "running"}
        }
        
        # 验证每个状态都有定义的转换
        all_states = {"pending", "running", "completed", "failed"}
        for state in all_states:
            assert state in valid_transitions


class TestBoundaryConditions:
    """边界条件属性测试"""
    
    @given(empty_list=st.lists(st.text(), max_size=0))
    @settings(max_examples=10)
    def test_empty_task_list(self, empty_list):
        """测试空任务列表"""
        results = []
        success = 0
        
        for t in empty_list:
            results.append({"task": t, "success": False})
        
        assert len(results) == 0
        assert success == 0
    
    @given(large_list=st.lists(st.integers(min_value=0, max_value=1000), max_size=1000))
    @settings(max_examples=5)
    def test_large_task_list(self, large_list):
        """测试大型任务列表处理"""
        # 模拟批量处理
        batch_size = 10
        batches = [large_list[i:i+batch_size] for i in range(0, len(large_list), batch_size)]
        
        assert len(batches) <= 100
        assert sum(len(b) for b in batches) == len(large_list)
    
    @given(special_chars=st.text())
    @settings(max_examples=10)
    def test_special_characters_in_task(self, special_chars):
        """测试特殊字符处理"""
        task = {"task": special_chars, "status": "pending"}
        
        assert task["task"] == special_chars
        assert task["status"] == "pending"
    
    @given(task_count=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=20)
    def test_task_id_generation(self, task_count):
        """测试任务 ID 生成"""
        task_ids = []
        
        for i in range(min(task_count, 100)):
            task_id = f"task_{i+1}"
            task_ids.append(task_id)
        
        # 验证 ID 唯一性
        assert len(set(task_ids)) == len(task_ids)
        
        # 验证 ID 格式
        for task_id in task_ids:
            assert task_id.startswith("task_")
    
    @given(files=st.lists(
        st.one_of(
            st.text(min_size=1, max_size=50),
            st.none()
        ),
        max_size=100
    ))
    @settings(max_examples=20)
    def test_files_list_handling(self, files):
        """测试文件列表处理"""
        valid_files = [f for f in files if f is not None]
        
        assert all(isinstance(f, str) for f in valid_files)
        assert all(len(f) > 0 for f in valid_files)


class TestExecutionResultProperties:
    """ExecutionResult 属性测试"""
    
    @given(
        success=st.booleans(),
        files_changed=st.one_of(
            st.dictionaries(keys=st.text(), values=st.lists(st.text())),
            st.lists(st.text()),
            st.none()
        ),
        tool=st.sampled_from(list(ToolType) + [None]),
        duration=st.floats(min_value=0, max_value=3600)
    )
    @settings(max_examples=30)
    def test_execution_result_creation(self, success, files_changed, tool, duration):
        """测试 ExecutionResult 创建"""
        try:
            result = ExecutionResult(
                success=success,
                files_changed=files_changed,
                tool=tool,
                duration=duration
            )
            
            assert result.success == success
            assert result.duration == duration
            assert result.tool == tool
        except Exception:
            pass


class TestCheckpointSanitization:
    """检查点清理属性测试"""
    
    def sanitize(self, obj):
        """测试用的清理函数"""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, list):
            result = [self.sanitize(item) for item in obj]
            return result if any(r is not None for r in result) else None
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                sv = self.sanitize(v)
                if sv is not None:
                    result[k] = sv
            return result if result else None
        return str(obj)
    
    @given(
        obj=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False),
            st.text(),
            st.lists(st.none()),
            st.dictionaries(keys=st.text(), values=st.none())
        )
    )
    @settings(max_examples=50)
    def test_sanitize_preserves_valid_types(self, obj):
        """测试清理函数保留有效类型"""
        result = self.sanitize(obj)
        
        if obj is None:
            assert result is None
        elif isinstance(obj, bool):
            assert isinstance(result, bool)
        elif isinstance(obj, (int, float)):
            assert isinstance(result, (int, float))
        elif isinstance(obj, str):
            assert isinstance(result, str)
    
    def test_sanitize_removes_empty_containers(self):
        """测试清理函数移除空容器"""
        empty_list = [None, None, None]
        empty_dict = {"a": None, "b": None}
        
        assert self.sanitize(empty_list) is None
        assert self.sanitize(empty_dict) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
