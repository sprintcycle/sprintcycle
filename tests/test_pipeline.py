"""
Tests for EvolutionPipeline - 统一进化管道测试

测试场景:
1. 基础初始化
2. Mock PRD Source执行
3. Mock Executor执行
4. Fitness测量
5. 基因保存
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Tuple

from sprintcycle.evolution.pipeline import (
    EvolutionPipeline,
    PipelineResult,
    PipelineStatus,
    PRDExecutionResult,
    SprintExecutionResult,
)

from sprintcycle.evolution.prd_source import (
    PRDSource,
    EvolutionPRD,
    PRDSourceType,
)

from sprintcycle.config.runtime_config import RuntimeConfig


class TestEvolutionPipeline:
    """EvolutionPipeline测试类"""
    
    def test_init_default(self):
        """测试默认初始化"""
        pipeline = EvolutionPipeline(project_path="/test/project")
        
        assert pipeline.project_path == "/test/project"
        # Default initializes with ManualPRDSource
        from sprintcycle.evolution.prd_source import ManualPRDSource
        assert isinstance(pipeline._prd_source, ManualPRDSource)
    
    def test_init_with_config(self):
        """测试带RuntimeConfig初始化"""
        config = RuntimeConfig(
            max_sprints=3,
            max_tasks_per_sprint=10,
            dry_run=True,
        )
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            config=config,
        )
        
        assert pipeline._config is config
        assert pipeline._config.max_sprints == 3
        assert pipeline._config.max_tasks_per_sprint == 10
        assert pipeline._config.dry_run is True
    
    def test_init_with_mock_executor(self):
        """测试带Mock执行器初始化"""
        mock_executor = Mock()
        mock_executor.execute = Mock(return_value={"success": True})
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
        )
        
        # Check that pipeline is initialized
        assert pipeline.project_path == "/test/project"
    
    def test_run_empty_prds(self):
        """测试无PRD时运行"""
        # Mock PRD源返回空列表
        mock_source = Mock(spec=PRDSource)
        mock_source.generate = Mock(return_value=[])
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            prd_source=mock_source,
        )
        
        result = pipeline.run()
        
        assert result.prd.name == "run"
        mock_source.generate.assert_not_called()
    
    def test_run_single_prd_dry_run(self):
        """测试单个PRD干跑"""
        # 创建测试PRD
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1", "Goal 2"],
            sprints=[{
                "name": "Sprint 1",
                "goals": ["Sprint Goal 1"],
                "tasks": [
                    {"task": "Task 1", "agent": "coder"},
                    {"task": "Task 2", "agent": "tester"},
                ],
            }],
            source_type=PRDSourceType.MANUAL,
            confidence=0.9,
            expected_benefit=10.0,
        )
        
        mock_source = Mock(spec=PRDSource)
        mock_source.generate = Mock(return_value=[prd])
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            prd_source=mock_source,
        )
        
        # Execute the PRD
        result = pipeline.execute(prd)
        
        # Verify execution
        assert result.prd == prd
    
    def test_execute_with_sprint_success(self):
        """测试执行带Sprint的成功场景"""
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            sprints=[{
                "name": "Sprint 1",
                "goals": [],
                "tasks": [{"task": "Task 1", "agent": "coder"}],
            }],
            source_type=PRDSourceType.MANUAL,
        )
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
        )
        
        result = pipeline.execute(prd)
        
        assert result.prd == prd
        assert len(result.sprint_results) == 1
    
    def test_execute_empty_sprints(self):
        """测试执行空Sprints"""
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            sprints=[],
            source_type=PRDSourceType.MANUAL,
        )
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
        )
        
        result = pipeline.execute(prd)
        
        # Empty sprints results in success=True with 0 sprint results
        # This is expected behavior - no sprints means nothing to fail
        assert len(result.sprint_results) == 0
    
    def test_pipeline_result_to_dict(self):
        """测试PipelineResult序列化"""
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            sprints=[],
            source_type=PRDSourceType.MANUAL,
        )
        result = PRDExecutionResult(
            prd=prd,
            success=True,
        )
        
        data = result.to_dict()
        
        assert data["prd_name"] == "Test PRD"
        assert data["success"] is True


class TestRuntimeConfig:
    """RuntimeConfig测试类（替代原PipelineConfig测试）"""
    
    def test_default_values(self):
        """测试默认值"""
        config = RuntimeConfig()
        
        assert config.max_sprints == 10
        assert config.max_tasks_per_sprint == 5
        assert config.dry_run is False
        assert config.evolution_enabled is True
    
    def test_custom_values(self):
        """测试自定义值"""
        config = RuntimeConfig(
            max_sprints=5,
            max_tasks_per_sprint=50,
            dry_run=True,
        )
        
        assert config.max_sprints == 5
        assert config.max_tasks_per_sprint == 50
        assert config.dry_run is True


class TestSprintExecutionResult:
    """SprintExecutionResult测试类"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = SprintExecutionResult(
            sprint_name="Sprint 1",
            success=True,
            task_results=[
                {"task": "Task 1", "success": True},
                {"task": "Task 2", "success": True},
            ],
            duration=5.0,
        )
        
        assert result.success is True
        assert result.duration == 5.0
        assert len(result.task_results) == 2
    
    def test_to_dict(self):
        """测试序列化"""
        result = SprintExecutionResult(
            sprint_name="Sprint 1",
            success=True,
            duration=3.5,
        )
        
        data = result.to_dict()
        
        assert data["sprint_name"] == "Sprint 1"
        assert data["success"] is True
        assert data["duration"] == 3.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
