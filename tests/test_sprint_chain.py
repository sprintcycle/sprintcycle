"""SprintCycle SprintChain 模块测试"""
import sys
import pytest
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/sprintcycle')

from sprintcycle.sprint_chain import SprintChain
from sprintcycle.chorus import ExecutionResult


class TestSprintChain:
    """测试 SprintChain 类"""
    
    def test_sprint_chain_init(self, tmp_path):
        """测试 SprintChain 初始化"""
        chain = SprintChain(str(tmp_path))
        assert chain.project_path == tmp_path
        assert chain.config is not None
        assert chain.kb is not None
        assert chain.chorus is not None
    
    def test_sprint_chain_with_review(self, tmp_path):
        """测试带审查功能的 SprintChain"""
        chain = SprintChain(str(tmp_path), review_enabled=False)
        assert chain.review_enabled == False
        assert chain.reviewer is None
    
    def test_get_sprints_empty(self, tmp_path):
        """测试空项目获取 sprints"""
        chain = SprintChain(str(tmp_path))
        sprints = chain.get_sprints()
        assert sprints == []
    
    def test_create_sprint(self, tmp_path):
        """测试创建 Sprint"""
        chain = SprintChain(str(tmp_path))
        sprint = chain.create_sprint("Sprint 1", ["目标1", "目标2"])
        
        assert sprint["name"] == "Sprint 1"
        assert sprint["goals"] == ["目标1", "目标2"]
        assert sprint["status"] == "pending"
        assert "id" in sprint
    
    def test_create_multiple_sprints(self, tmp_path):
        """测试创建多个 Sprint"""
        chain = SprintChain(str(tmp_path))
        
        sprint1 = chain.create_sprint("Sprint 1", ["目标1"])
        sprint2 = chain.create_sprint("Sprint 2", ["目标2"])
        
        sprints = chain.get_sprints()
        assert len(sprints) == 2
        assert sprints[0]["name"] == "Sprint 1"
        assert sprints[1]["name"] == "Sprint 2"
    
    def test_run_sprint_by_name_not_found(self, tmp_path):
        """测试执行不存在的 Sprint"""
        chain = SprintChain(str(tmp_path))
        result = chain.run_sprint_by_name("NonExistent")
        
        assert result["error"] == "Sprint not found"
        assert result["total"] == 0
        assert result["success"] == 0
    
    def test_run_sprint_by_name_found(self, tmp_path):
        """测试执行存在的 Sprint"""
        chain = SprintChain(str(tmp_path))
        chain.create_sprint("Test Sprint", ["测试目标"])
        
        # 注意：这里只是测试方法调用，不实际执行任务
        result = chain.run_sprint_by_name("Test Sprint")
        assert "sprint_name" in result
        assert result["total"] == 0  # Sprint 中没有任务
    
    def test_get_results_empty(self, tmp_path):
        """测试空结果列表"""
        chain = SprintChain(str(tmp_path))
        results = chain.get_results()
        assert results == []
    
    def test_get_kb_stats(self, tmp_path):
        """测试获取知识库统计"""
        chain = SprintChain(str(tmp_path))
        stats = chain.get_kb_stats()
        assert "total" in stats
        assert "success_rate" in stats
    
    def test_batch_size_default(self, tmp_path):
        """测试默认批处理大小"""
        chain = SprintChain(str(tmp_path))
        assert chain.BATCH_SIZE == 5


class TestSprintChainFileOperations:
    """测试 SprintChain 文件操作"""
    
    def test_config_persistence(self, tmp_path):
        """测试配置持久化"""
        chain1 = SprintChain(str(tmp_path))
        chain1.create_sprint("Persistent Sprint", ["目标"])
        
        # 创建新的 chain 实例
        chain2 = SprintChain(str(tmp_path))
        sprints = chain2.get_sprints()
        
        assert len(sprints) == 1
        assert sprints[0]["name"] == "Persistent Sprint"
    
    def test_results_directory_created(self, tmp_path):
        """测试结果目录创建"""
        chain = SprintChain(str(tmp_path))
        # 执行一个任务会创建结果目录
        assert chain.results_path == tmp_path / ".sprintcycle" / "results"


class TestSprintChainAutoPlan:
    """测试自动规划功能"""
    
    def test_parse_sprint_file_empty(self, tmp_path):
        """测试解析空的 Sprint 文件"""
        chain = SprintChain(str(tmp_path))
        test_file = tmp_path / "empty.md"
        test_file.write_text("")
        
        tasks = chain.parse_sprint_file(str(test_file))
        assert tasks == []
    
    def test_parse_sprint_file_markdown(self, tmp_path):
        """测试解析 Markdown 格式的 Sprint 文件"""
        chain = SprintChain(str(tmp_path))
        test_file = tmp_path / "sprint.md"
        test_file.write_text("""
### Task 1: 实现登录功能

- 子任务1
- 子任务2

### Task 2: 实现注册功能

- 子任务3
""")
        
        tasks = chain.parse_sprint_file(str(test_file))
        assert len(tasks) == 2
        assert tasks[0]["task"] == "实现登录功能"
        assert len(tasks[0]["subtasks"]) == 2
    
    def test_auto_plan_from_prd_not_found(self, tmp_path):
        """测试从不存在的 PRD 规划"""
        chain = SprintChain(str(tmp_path))
        result = chain.auto_plan_from_prd("/nonexistent/path/prd.md")
        assert result["error"] is not None
        assert result["sprints"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
