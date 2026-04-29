"""
SprintChain Phase 3 覆盖率扩展测试
目标: sprint_chain.py: 58% → 70%
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestSprintChainPhase3:
    """SprintChain Phase 3 测试类"""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """创建临时项目目录"""
        project = tmp_path / "test_project"
        project.mkdir()
        sprintcycle_dir = project / ".sprintcycle"
        sprintcycle_dir.mkdir()
        results_dir = sprintcycle_dir / "results"
        results_dir.mkdir()
        checkpoints_dir = sprintcycle_dir / "checkpoints"
        checkpoints_dir.mkdir()
        
        config = {
            "project": {"name": "TestProject"},
            "sprint_chain": [
                {
                    "id": "sprint_1",
                    "name": "Test Sprint",
                    "goals": ["Goal 1", "Goal 2"],
                    "status": "pending",
                    "tasks": []
                }
            ]
        }
        import yaml
        with open(sprintcycle_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
        
        return project
    
    @pytest.fixture
    def sprint_chain(self, temp_project):
        """创建 SprintChain 实例"""
        from sprintcycle.sprint_chain import SprintChain
        chain = SprintChain(str(temp_project), review_enabled=False)
        return chain
    
    def test_create_sprint_returns_dict(self, sprint_chain):
        """测试 create_sprint 返回正确格式"""
        sprint = sprint_chain.create_sprint("New Sprint", ["Goal A", "Goal B"])
        
        assert isinstance(sprint, dict)
        assert "id" in sprint
        assert "name" in sprint
        assert sprint["name"] == "New Sprint"
        assert sprint["goals"] == ["Goal A", "Goal B"]
        assert sprint["status"] == "pending"
        assert sprint["id"].startswith("sprint_")
    
    def test_run_task_with_mock_result(self, sprint_chain, temp_project):
        """测试 run_task 方法"""
        from sprintcycle.chorus import ExecutionResult
        
        mock_result = MagicMock(spec=ExecutionResult)
        mock_result.success = True
        mock_result.files_changed = {"modified": ["file1.py"]}
        mock_result.tool = "aider"
        mock_result.duration = 10.5
        mock_result.retries = 0
        mock_result.has_changes = True
        mock_result.change_summary = "Modified 1 file"
        mock_result.output = "test output"
        mock_result.needs_fix = False
        mock_result.split_suggestion = None
        mock_result.review = None
        
        with patch.object(sprint_chain.chorus, 'dispatch', return_value=mock_result):
            result = sprint_chain.run_task("Test task", files=["file1.py"])
            
            assert result.success is True
    
    def test_get_sprints_empty(self, sprint_chain):
        """测试 get_sprints 方法"""
        sprints = sprint_chain.get_sprints()
        assert isinstance(sprints, list)
        assert len(sprints) > 0
    
    def test_get_results_empty(self, sprint_chain):
        """测试 get_results 方法（无结果）"""
        results = sprint_chain.get_results()
        assert isinstance(results, list)
    
    def test_get_results_with_files(self, sprint_chain, temp_project):
        """测试 get_results 方法（有结果文件）"""
        results_dir = temp_project / ".sprintcycle" / "results"
        result_data = {
            "task": "Test task",
            "task_name": "test_task",
            "success": True,
            "files_changed": ["file1.py"],
            "tool": "aider",
            "duration": 10.0,
            "retries": 0,
            "timestamp": datetime.now().isoformat()
        }
        result_file = results_dir / "test_task_20260429_120000.json"
        with open(result_file, "w") as f:
            json.dump(result_data, f)
        
        results = sprint_chain.get_results()
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["task"] == "Test task"
    
    def test_get_kb_stats(self, sprint_chain):
        """测试 get_kb_stats 方法"""
        stats = sprint_chain.get_kb_stats()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "success_rate" in stats


class TestParseSprintFile:
    """测试 parse_sprint_file 方法"""
    
    def test_parse_sprint_file_basic(self, tmp_path):
        """测试基本 Markdown 格式解析"""
        from sprintcycle.sprint_chain import SprintChain
        
        test_file = tmp_path / "sprint.md"
        test_file.write_text("""
# Test Sprint

### Task 1: First Task
- Subtask 1.1
- Subtask 1.2

### Task 2: Second Task
- Subtask 2.1
""")
        
        chain = SprintChain(str(tmp_path))
        tasks = chain.parse_sprint_file(str(test_file))
        
        assert len(tasks) == 2
        assert tasks[0]["task"] == "First Task"
        assert "Subtask 1.1" in tasks[0]["subtasks"]
        assert tasks[1]["task"] == "Second Task"
    
    def test_parse_sprint_file_empty(self, tmp_path):
        """测试空文件解析"""
        from sprintcycle.sprint_chain import SprintChain
        
        test_file = tmp_path / "empty.md"
        test_file.write_text("# Empty File\n")
        
        chain = SprintChain(str(tmp_path))
        tasks = chain.parse_sprint_file(str(test_file))
        
        assert isinstance(tasks, list)
    
    def test_parse_sprint_file_no_tasks(self, tmp_path):
        """测试无任务文件"""
        from sprintcycle.sprint_chain import SprintChain
        
        test_file = tmp_path / "no_tasks.md"
        test_file.write_text("# Just a title\n\nNo tasks here")
        
        chain = SprintChain(str(tmp_path))
        tasks = chain.parse_sprint_file(str(test_file))
        
        assert isinstance(tasks, list)


class TestAutoPlanFromPRD:
    """测试 auto_plan_from_prd 方法"""
    
    def test_auto_plan_yaml_format(self, tmp_path):
        """测试 YAML 格式 PRD 解析"""
        from sprintcycle.sprint_chain import SprintChain
        
        prd_file = tmp_path / "prd.yaml"
        prd_file.write_text("""
# Test PRD
project:
  name: Test Project

sprints:
  - name: Sprint 1
    goals:
      - Goal 1
      - Goal 2
    tasks:
      - task: Task 1
        agent: coder
      - task: Task 2
        agent: tester
""")
        
        chain = SprintChain(str(tmp_path))
        result = chain.auto_plan_from_prd(str(prd_file))
        
        assert "sprints" in result
        assert result["error"] is None
        assert len(result["sprints"]) == 1
        assert result["sprints"][0]["name"] == "Sprint 1"
        assert len(result["sprints"][0]["tasks"]) == 2
    
    def test_auto_plan_file_not_found(self, tmp_path):
        """测试文件不存在"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        result = chain.auto_plan_from_prd("/nonexistent/prd.yaml")
        
        assert "error" in result
        assert "不存在" in result["error"]
    
    def test_auto_plan_read_error(self, tmp_path):
        """测试文件读取错误"""
        from sprintcycle.sprint_chain import SprintChain
        
        prd_file = tmp_path / "prd.md"
        chain = SprintChain(str(tmp_path))
        result = chain.auto_plan_from_prd(str(prd_file))
        
        assert "error" in result
    
    def test_auto_plan_markdown_format(self, tmp_path):
        """测试 Markdown 格式 PRD 解析"""
        from sprintcycle.sprint_chain import SprintChain
        
        prd_file = tmp_path / "prd.md"
        prd_file.write_text("""
# Test PRD

## 开发优先级

### Sprint 1: First Sprint
- Task 1 for coder
- Task 2 for tester
- 文件: src/main.py
""")
        
        chain = SprintChain(str(tmp_path))
        result = chain.auto_plan_from_prd(str(prd_file))
        
        assert "sprints" in result
    
    def test_auto_plan_no_section(self, tmp_path):
        """测试无开发优先级章节"""
        from sprintcycle.sprint_chain import SprintChain
        
        prd_file = tmp_path / "prd.md"
        prd_file.write_text("# Just a Title\n\nNo development section")
        
        chain = SprintChain(str(tmp_path))
        result = chain.auto_plan_from_prd(str(prd_file))
        
        assert "error" in result


class TestCheckpointSaving:
    """测试检查点保存功能"""
    
    def test_save_checkpoint(self, tmp_path):
        """测试 _save_checkpoint 方法"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        
        tasks = [
            {
                "task": "Test task",
                "status": "completed",
                "duration_seconds": 10.0,
                "files_changed": {"modified": ["file.py"]}
            }
        ]
        
        chain._save_checkpoint("TestSprint", tasks)
        
        checkpoint_file = tmp_path / ".sprintcycle" / "checkpoints" / "TestSprint.json"
        assert checkpoint_file.exists()
        
        with open(checkpoint_file) as f:
            data = json.load(f)
            assert data["sprint_name"] == "TestSprint"
            assert "timestamp" in data
            assert len(data["tasks"]) == 1
    
    def test_save_checkpoint_with_enum(self, tmp_path):
        """测试包含枚举类型的检查点保存"""
        from sprintcycle.sprint_chain import SprintChain
        from sprintcycle.chorus import TaskStatus
        
        chain = SprintChain(str(tmp_path))
        
        tasks = [
            {
                "task": "Test",
                "status": TaskStatus.SUCCESS,
                "duration": 5.0
            }
        ]
        
        chain._save_checkpoint("EnumSprint", tasks)
        
        checkpoint_file = tmp_path / ".sprintcycle" / "checkpoints" / "EnumSprint.json"
        assert checkpoint_file.exists()


class TestRunAllSprints:
    """测试 run_all_sprints 方法"""
    
    def test_run_all_sprints_empty(self, tmp_path):
        """测试无 Sprint 时的行为"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        results = chain.run_all_sprints()
        
        assert isinstance(results, list)
    
    def test_run_all_sprints_with_completed(self, tmp_path):
        """测试跳过已完成的 Sprint"""
        from sprintcycle.sprint_chain import SprintChain
        import yaml
        
        config = {
            "project": {"name": "Test"},
            "sprint_chain": [
                {
                    "name": "Completed Sprint",
                    "status": "completed",
                    "tasks": []
                }
            ]
        }
        
        sprintcycle_dir = tmp_path / ".sprintcycle"
        sprintcycle_dir.mkdir()
        with open(sprintcycle_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
        
        chain = SprintChain(str(tmp_path))
        results = chain.run_all_sprints()
        
        assert isinstance(results, list)


class TestRunSprintByName:
    """测试 run_sprint_by_name 方法"""
    
    def test_run_sprint_by_name_found(self, tmp_path):
        """测试找到 Sprint"""
        from sprintcycle.sprint_chain import SprintChain
        from sprintcycle.chorus import ExecutionResult
        import yaml
        
        config = {
            "project": {"name": "Test"},
            "sprint_chain": [
                {
                    "name": "Find Me",
                    "goals": [],
                    "status": "pending",
                    "tasks": [
                        {"task": "Task 1", "files": []}
                    ]
                }
            ]
        }
        
        sprintcycle_dir = tmp_path / ".sprintcycle"
        sprintcycle_dir.mkdir()
        with open(sprintcycle_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
        
        chain = SprintChain(str(tmp_path))
        
        mock_result = MagicMock(spec=ExecutionResult)
        mock_result.success = True
        mock_result.files_changed = {}
        mock_result.tool = "aider"
        mock_result.duration = 5.0
        mock_result.retries = 0
        mock_result.has_changes = False
        mock_result.change_summary = ""
        mock_result.output = None
        mock_result.needs_fix = False
        mock_result.split_suggestion = None
        mock_result.review = None
        
        with patch.object(chain.chorus, 'dispatch', return_value=mock_result):
            result = chain.run_sprint_by_name("Find Me")
            
            assert result["sprint_name"] == "Find Me"
            assert result["total"] == 1
    
    def test_run_sprint_by_name_not_found(self, tmp_path):
        """测试未找到 Sprint"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        result = chain.run_sprint_by_name("NonExistent")
        
        assert "error" in result
        assert result["error"] == "Sprint not found"
        assert result["total"] == 0


class TestSanitizeFunction:
    """测试 sanitize 函数"""
    
    def test_sanitize_none(self, tmp_path):
        """测试 None 值"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        chain._save_checkpoint("Test", [{"key": None}])
    
    def test_sanitize_primitives(self, tmp_path):
        """测试基本类型"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        tasks = [
            {"str": "test", "int": 42, "float": 3.14, "bool": True}
        ]
        chain._save_checkpoint("Test", tasks)
        
        checkpoint_file = tmp_path / ".sprintcycle" / "checkpoints" / "Test.json"
        with open(checkpoint_file) as f:
            data = json.load(f)
            assert data["tasks"][0]["str"] == "test"
            assert data["tasks"][0]["int"] == 42
    
    def test_sanitize_nested(self, tmp_path):
        """测试嵌套结构"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        tasks = [
            {"outer": {"inner": "value", "list": [1, 2, 3]}}
        ]
        chain._save_checkpoint("Test", tasks)
    
    def test_sanitize_mixed_empty(self, tmp_path):
        """测试混合空值"""
        from sprintcycle.sprint_chain import SprintChain
        
        chain = SprintChain(str(tmp_path))
        tasks = [
            {"a": 1, "b": None, "c": ""},
            {"x": None, "y": []}
        ]
        chain._save_checkpoint("Test", tasks)
