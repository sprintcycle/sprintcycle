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
    PipelineConfig,
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


class TestEvolutionPipeline:
    """EvolutionPipeline测试类"""
    
    def test_init_default(self):
        """测试默认初始化"""
        pipeline = EvolutionPipeline(project_path="/test/project")
        
        assert pipeline.project_path == "/test/project"
        assert pipeline._config.max_cycles == 1
        assert pipeline._prd_source is None
        assert len(pipeline.genes) == 0
        assert len(pipeline.history) == 0
    
    def test_init_with_config(self):
        """测试带配置初始化"""
        config = PipelineConfig(
            max_cycles=3,
            max_tasks_per_sprint=10,
            dry_run=True,
        )
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            config=config,
        )
        
        assert pipeline._config.max_cycles == 3
        assert pipeline._config.max_tasks_per_sprint == 10
        assert pipeline._config.dry_run is True
    
    def test_init_with_mock_executor(self):
        """测试带Mock执行器初始化"""
        mock_executor = Mock()
        mock_executor.execute = Mock(return_value={"success": True})
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            executor=mock_executor,
        )
        
        assert pipeline._executor is mock_executor
    
    def test_init_with_fitness_func(self):
        """测试带Fitness函数初始化"""
        def mock_fitness(path: str) -> float:
            return 0.8
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            fitness_func=mock_fitness,
        )
        
        assert pipeline._fitness_func is mock_fitness
    
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
        
        assert result.status == PipelineStatus.IDLE
        assert result.total_prds == 0
        mock_source.generate.assert_called_once_with("/test/project")
    
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
            config=PipelineConfig(dry_run=True),
        )
        
        result = pipeline.run()
        
        assert result.status == PipelineStatus.SUCCESS
        assert result.total_prds == 1
        assert result.successful_prds == 1
        assert result.failed_prds == 0
    
    def test_run_with_mock_executor_success(self):
        """测试使用Mock执行器成功场景"""
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
        
        mock_source = Mock(spec=PRDSource)
        mock_source.generate = Mock(return_value=[prd])
        
        mock_executor = Mock()
        mock_executor.execute = Mock(return_value={"success": True})
        
        def mock_fitness(path: str) -> float:
            return 0.75
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            prd_source=mock_source,
            executor=mock_executor,
            fitness_func=mock_fitness,
        )
        
        result = pipeline.run()
        
        assert result.status == PipelineStatus.SUCCESS
        assert result.successful_prds == 1
        mock_executor.execute.assert_called()
    
    def test_run_with_mock_executor_failure(self):
        """测试使用Mock执行器失败场景"""
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
        
        mock_source = Mock(spec=PRDSource)
        mock_source.generate = Mock(return_value=[prd])
        
        mock_executor = Mock()
        mock_executor.execute = Mock(return_value={"success": False, "error": "Task failed"})
        
        rollback_mock = Mock()
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            prd_source=mock_source,
            executor=mock_executor,
            rollback_func=rollback_mock,
        )
        
        result = pipeline.run()
        
        assert result.status == PipelineStatus.FAILED
        assert result.failed_prds == 1
        rollback_mock.assert_called()
    
    def test_gene_saving(self):
        """测试基因保存"""
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
        
        mock_source = Mock(spec=PRDSource)
        mock_source.generate = Mock(return_value=[prd])
        
        mock_executor = Mock()
        mock_executor.execute = Mock(return_value={"success": True})
        
        def mock_fitness(path: str) -> float:
            return 0.7
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            prd_source=mock_source,
            executor=mock_executor,
            fitness_func=mock_fitness,
        )
        
        result = pipeline.run()
        
        assert len(pipeline.genes) == 1
        gene = pipeline.genes[0]
        assert gene.metadata["prd_name"] == "Test PRD"
        assert gene.fitness_scores["overall"] == 0.7
    
    def test_history_tracking(self):
        """测试历史追踪"""
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            sprints=[{
                "name": "Sprint 1",
                "goals": [],
                "tasks": [],
            }],
            source_type=PRDSourceType.MANUAL,
        )
        
        mock_source = Mock(spec=PRDSource)
        mock_source.generate = Mock(return_value=[prd])
        
        pipeline = EvolutionPipeline(
            project_path="/test/project",
            prd_source=mock_source,
            config=PipelineConfig(dry_run=True),
        )
        
        result = pipeline.run()
        
        assert len(pipeline.history) == 1
        history_item = pipeline.history[0]
        assert isinstance(history_item, PRDExecutionResult)
        assert history_item.prd.name == "Test PRD"
    
    def test_pipeline_result_to_dict(self):
        """测试PipelineResult序列化"""
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            total_prds=2,
            successful_prds=2,
            failed_prds=0,
            total_duration=10.5,
        )
        
        data = result.to_dict()
        
        assert data["status"] == "success"
        assert data["total_prds"] == 2
        assert data["successful_prds"] == 2
        assert data["total_duration"] == 10.5
        assert data["success"] is True


class TestPipelineConfig:
    """PipelineConfig测试类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = PipelineConfig()
        
        assert config.max_cycles == 1
        assert config.max_tasks_per_sprint == 20
        assert config.task_timeout == 600
        assert config.rollback_on_failure is True
        assert config.save_genes is True
        assert config.dry_run is False
    
    def test_custom_values(self):
        """测试自定义值"""
        config = PipelineConfig(
            max_cycles=5,
            max_tasks_per_sprint=50,
            task_timeout=1200,
            rollback_on_failure=False,
            dry_run=True,
        )
        
        assert config.max_cycles == 5
        assert config.max_tasks_per_sprint == 50
        assert config.task_timeout == 1200
        assert config.rollback_on_failure is False
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
