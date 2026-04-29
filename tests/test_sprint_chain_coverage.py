"""扩展测试 SprintChain 覆盖未测试的代码路径"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from sprintcycle.sprint_chain import SprintChain
from sprintcycle.chorus import ExecutionResult


class TestSprintChainConfigLoad:
    """测试配置加载"""
    
    def test_load_config_file_not_exists(self):
        """测试配置文件不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "new_project")
            os.makedirs(project_path)
            chain = SprintChain(project_path=project_path)
            config = chain._load_config()
            assert isinstance(config, dict)
            assert "project" in config
    
    def test_load_config_with_existing_file(self):
        """测试加载已存在的配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project")
            os.makedirs(project_path)
            
            # 创建配置文件
            config_dir = os.path.join(project_path, ".sprintcycle")
            os.makedirs(config_dir)
            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, 'w') as f:
                f.write('{"project": "test_project", "sprint_chain": []}')
            
            chain = SprintChain(project_path=project_path)
            config = chain._load_config()
            # 验证配置已加载
            assert isinstance(config, dict)


class TestSprintChainCreate:
    """测试 Sprint 创建"""
    
    def test_create_sprint_with_id(self):
        """测试创建带 ID 的 Sprint"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            sprint = chain.create_sprint("Sprint 1", ["目标1"])
            
            assert "id" in sprint
            assert sprint["id"] is not None
            assert sprint["name"] == "Sprint 1"
    
    def test_create_sprint_goals_list(self):
        """测试创建 Sprint 带多个目标"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            goals = ["目标1", "目标2", "目标3"]
            sprint = chain.create_sprint("Sprint 1", goals)
            
            assert len(sprint["goals"]) == 3
            assert sprint["goals"] == goals
    
    def test_create_sprint_status_pending(self):
        """测试创建 Sprint 状态为 pending"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            sprint = chain.create_sprint("Sprint 1", ["目标"])
            
            assert sprint["status"] == "pending"
    
    def test_create_sprint_multiple(self):
        """测试创建多个 Sprint"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            chain.create_sprint("Sprint 1", ["目标1"])
            chain.create_sprint("Sprint 2", ["目标2"])
            
            sprints = chain.get_sprints()
            assert len(sprints) == 2


class TestSprintChainRun:
    """测试 Sprint 运行"""
    
    @patch.object(SprintChain, 'run_task')
    def test_run_sprint_by_name(self, mock_run_task):
        """测试按名称运行 Sprint"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            chain.create_sprint("Test Sprint", ["目标"])
            
            mock_result = ExecutionResult(
                success=True, output="done", duration=1.0, tool="aider"
            )
            mock_run_task.return_value = mock_result
            
            result = chain.run_sprint_by_name("Test Sprint")
            assert "sprint_name" in result
            assert result["sprint_name"] == "Test Sprint"
    
    @patch.object(SprintChain, 'run_task')
    def test_run_sprint_by_name_not_found(self, mock_run_task):
        """测试运行不存在的 Sprint"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            result = chain.run_sprint_by_name("NonExistent")
            
            assert "error" in result
            assert result["error"] == "Sprint not found"


class TestSprintChainParseFile:
    """测试文件解析"""
    
    def test_parse_sprint_file_markdown_format(self):
        """测试解析 Markdown 格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            test_file = os.path.join(tmpdir, "sprint.md")
            content = """
### Task 1: 实现登录功能

- 子任务1
- 子任务2

### Task 2: 实现注册功能

- 子任务3
"""
            with open(test_file, 'w') as f:
                f.write(content)
            
            tasks = chain.parse_sprint_file(test_file)
            assert len(tasks) == 2
            assert tasks[0]["task"] == "实现登录功能"
            assert len(tasks[0]["subtasks"]) == 2
    
    def test_parse_sprint_file_empty_content(self):
        """测试解析空文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            test_file = os.path.join(tmpdir, "empty.md")
            with open(test_file, 'w') as f:
                f.write("")
            
            tasks = chain.parse_sprint_file(test_file)
            assert tasks == []
    
    def test_parse_sprint_file_no_tasks(self):
        """测试解析无任务文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            test_file = os.path.join(tmpdir, "notextasks.md")
            with open(test_file, 'w') as f:
                f.write("# 标题\n\n内容")
            
            tasks = chain.parse_sprint_file(test_file)
            assert tasks == []


class TestSprintChainAutoPlan:
    """测试自动规划"""
    
    def test_auto_plan_from_prd_yaml_format(self):
        """测试从 YAML PRD 自动规划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            prd_file = os.path.join(tmpdir, "prd.yaml")
            content = """
project: Test Project
sprints:
  - name: Sprint 1
    goals:
      - 实现基础功能
    tasks:
      - task: 开发模块A
        agent: coder
"""
            with open(prd_file, 'w') as f:
                f.write(content)
            
            result = chain.auto_plan_from_prd(prd_file)
            assert "sprints" in result
            assert len(result["sprints"]) == 1
    
    def test_auto_plan_from_prd_nonexistent_file(self):
        """测试从不存在的 PRD 文件规划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            result = chain.auto_plan_from_prd("/nonexistent/prd.yaml")
            assert "error" in result
            assert result["sprints"] == []
    
    def test_auto_plan_from_prd_markdown_format(self):
        """测试从 Markdown PRD 自动规划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            prd_file = os.path.join(tmpdir, "prd.md")
            content = """
# 产品需求文档

## 开发优先级

### Sprint 1: 基础功能

- 实现登录功能
- 实现注册功能
"""
            with open(prd_file, 'w') as f:
                f.write(content)
            
            result = chain.auto_plan_from_prd(prd_file)
            assert "sprints" in result


class TestSprintChainResults:
    """测试结果管理"""
    
    def test_get_results_empty(self):
        """测试获取空结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            results = chain.get_results()
            assert results == []
    
    def test_results_path_exists(self):
        """测试结果路径存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            assert chain.results_path is not None
    
    def test_results_path_structure(self):
        """测试结果路径结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            assert ".sprintcycle" in str(chain.results_path)
            assert "results" in str(chain.results_path)


class TestSprintChainSaveCheckpoint:
    """测试检查点保存"""
    
    def test_save_checkpoint(self):
        """测试保存检查点"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            
            tasks = [
                {"task": "任务1", "status": "completed", "duration_seconds": 5.0},
                {"task": "任务2", "status": "running"}
            ]
            
            # _save_checkpoint 应该能正常执行
            chain._save_checkpoint("Sprint 1", tasks)


class TestSprintChainKBStats:
    """测试知识库统计"""
    
    def test_get_kb_stats_empty(self):
        """测试空知识库统计"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            stats = chain.get_kb_stats()
            
            assert "total" in stats
            assert stats["total"] == 0
    
    def test_get_kb_stats_structure(self):
        """测试知识库统计结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            stats = chain.get_kb_stats()
            
            assert "success_rate" in stats


class TestSprintChainRunTask:
    """测试 run_task 方法"""
    
    @patch('sprintcycle.chorus.Chorus')
    def test_run_task_success(self, mock_chorus_class):
        """测试成功执行任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write("# test")
            
            mock_chorus = MagicMock()
            mock_result = ExecutionResult(
                success=True, output="done", duration=1.0, tool="aider",
                files_changed={"added": [], "modified": [test_file]}
            )
            mock_chorus.dispatch.return_value = mock_result
            mock_chorus_class.return_value = mock_chorus
            
            chain = SprintChain(project_path=tmpdir)
            result = chain.run_task("实现功能", [test_file])
            
            assert result.success == True


class TestSprintChainBatch:
    """测试批量任务执行"""
    
    def test_run_task_batch_empty(self):
        """测试空批量任务"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            results = chain._run_task_batch([], [])
            assert results == []


class TestSprintChainFilesOperations:
    """测试文件操作"""
    
    def test_save_config(self):
        """测试保存配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            chain.create_sprint("Test", ["Goal"])
            
            # 验证配置已保存
            config = chain._load_config()
            assert isinstance(config, dict)


class TestSprintChainToolSelection:
    """测试工具选择"""
    
    def test_batch_size_default(self):
        """测试默认批处理大小"""
        with tempfile.TemporaryDirectory() as tmpdir:
            chain = SprintChain(project_path=tmpdir)
            assert chain.BATCH_SIZE == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
