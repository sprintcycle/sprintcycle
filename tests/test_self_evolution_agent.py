#!/usr/bin/env python3
"""
SprintCycle SelfEvolutionAgent 测试

测试自进化 Agent 的核心功能
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 测试导入
try:
    from sprintcycle.agents.self_evolution_agent import (
        SelfEvolutionAgent,
        EvolutionPhase,
        EvolutionMode,
        EvolutionSnapshot,
        EvolutionResult
    )
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)


class TestSelfEvolutionAgent:
    """SelfEvolutionAgent 测试类"""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """创建临时项目"""
        project = tmp_path / "test_project"
        project.mkdir()
        
        # 创建 sprintcycle 目录
        sprintcycle_dir = project / "sprintcycle"
        sprintcycle_dir.mkdir()
        (sprintcycle_dir / "__init__.py").write_text('__version__ = "0.7.7"')
        
        # 创建 tests 目录
        tests_dir = project / "tests"
        tests_dir.mkdir()
        
        # 创建 .sprintcycle 目录
        (project / ".sprintcycle").mkdir()
        
        return project
    
    @pytest.fixture
    def agent(self, temp_project):
        """创建 SelfEvolutionAgent 实例"""
        return SelfEvolutionAgent(
            project_path=str(temp_project),
            data_dir=str(temp_project / ".sprintcycle" / "evolution"),
            dry_run=True
        )
    
    def test_agent_init(self, agent):
        """测试 Agent 初始化"""
        assert agent is not None
        assert agent.name == "SelfEvolutionAgent"
        assert agent.dry_run == True
        assert agent.current_phase == EvolutionPhase.ANALYSIS
    
    def test_agent_capabilities(self, agent):
        """测试 Agent 能力"""
        capabilities = [c.value for c in agent.capabilities]
        assert "coding" in capabilities
        assert "testing" in capabilities
        assert "optimization" in capabilities
    
    def test_get_evolution_status(self, agent):
        """测试获取进化状态"""
        status = agent.get_evolution_status()
        
        assert "current_phase" in status
        assert "snapshots_count" in status
        assert status["current_phase"] == "analysis"
        assert status["dry_run"] == True
    
    def test_evolve_incremental(self, agent):
        """测试增量进化"""
        result = agent.evolve(mode="incremental")
        
        assert result is not None
        assert isinstance(result, EvolutionResult)
        assert len(result.snapshots) >= 3  # 至少3个快照
    
    def test_evolve_full(self, agent):
        """测试全量进化"""
        result = agent.evolve(mode="full")
        
        assert result.success == True
        assert len(result.snapshots) >= 3
    
    def test_evolve_targeted(self, agent):
        """测试针对性进化"""
        result = agent.evolve(
            mode="targeted",
            target_modules=["server.py", "cache.py"]
        )
        
        assert result is not None
        assert isinstance(result, EvolutionResult)
    
    def test_analysis_phase(self, agent):
        """测试分析阶段"""
        snapshot = agent._analyze_framework()
        
        assert snapshot.phase == "analysis"
        assert snapshot.status == "complete"
        assert len(snapshot.findings) >= 3  # 结构、覆盖率、依赖
    
    def test_structure_analysis(self, agent):
        """测试结构分析"""
        analysis = agent._analyze_structure()
        
        assert "total_files" in analysis
        assert "total_lines" in analysis
        assert analysis["total_files"] > 0
    
    def test_coverage_analysis(self, agent):
        """测试覆盖率分析"""
        analysis = agent._analyze_coverage()
        
        assert "total_coverage" in analysis
        assert "target" in analysis
        assert "gap" in analysis
        assert analysis["target"] == 80.0
    
    def test_plan_phase(self, agent):
        """测试规划阶段"""
        analysis_snapshot = agent._analyze_framework()
        plan = agent._plan_evolution(analysis_snapshot, EvolutionMode.INCREMENTAL)
        
        assert plan.phase == "planning"
        assert plan.status == "complete"
    
    def test_execution_phase_dry_run(self, agent):
        """测试执行阶段(干运行)"""
        plan_snapshot = EvolutionSnapshot(
            phase="planning",
            mode="incremental",
            status="complete",
            recommendations=[
                {
                    "priority": "P1",
                    "action": "improve_coverage",
                    "target": "60% → 80%",
                    "details": {"gap": 20}
                }
            ]
        )
        
        exec_snapshot = agent._execute_evolution(plan_snapshot, max_iterations=1)
        
        assert exec_snapshot.phase == "execution"
        assert exec_snapshot.status == "dry_run"
    
    def test_validation_phase(self, agent):
        """测试验证阶段"""
        validation = agent._validate_evolution()
        
        assert validation.phase == "validation"
        assert validation.status in ["passed", "failed"]
    
    def test_snapshot_save(self, agent, temp_project):
        """测试快照保存"""
        snapshot = EvolutionSnapshot(
            phase="test",
            mode="test",
            status="complete"
        )
        
        agent._save_snapshot(snapshot)
        
        snapshot_dir = temp_project / ".sprintcycle" / "evolution"
        assert snapshot_dir.exists()
        assert len(list(snapshot_dir.glob("snapshot_*.json"))) > 0
    
    def test_history_load(self, agent, temp_project):
        """测试历史加载"""
        # 创建一些历史数据
        history_file = temp_project / ".sprintcycle" / "evolution" / "evolution_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps([{"test": "data"}]))
        
        # 重新初始化 agent
        agent2 = SelfEvolutionAgent(
            project_path=str(temp_project),
            data_dir=str(temp_project / ".sprintcycle" / "evolution"),
            dry_run=True
        )
        
        assert len(agent2.history) > 0
    
    def test_calculate_metrics(self, agent):
        """测试指标计算"""
        snapshot = EvolutionSnapshot(
            phase="test",
            mode="test",
            status="complete",
            changes_made=["change1", "change2"],
            recommendations=[{"rec": 1}]
        )
        agent.snapshots.append(snapshot)
        
        metrics = agent._calculate_metrics(duration=10.5)
        
        assert "total_duration_seconds" in metrics
        assert "snapshots_count" in metrics
        assert metrics["total_duration_seconds"] == 10.5
    
    def test_evolution_result_to_dict(self):
        """测试 EvolutionResult 序列化"""
        result = EvolutionResult(
            success=True,
            snapshots=[
                EvolutionSnapshot(
                    phase="test",
                    mode="test",
                    status="complete"
                )
            ],
            metrics={"score": 4.0},
            recommendations=["recommend1"]
        )
        
        dict_result = result.to_dict()
        
        assert dict_result["success"] == True
        assert len(dict_result["snapshots"]) == 1
        assert dict_result["metrics"]["score"] == 4.0
    
    def test_evolution_snapshot_to_dict(self):
        """测试 EvolutionSnapshot 序列化"""
        snapshot = EvolutionSnapshot(
            phase="test",
            mode="test",
            status="complete",
            findings=[{"category": "test"}],
            changes_made=["change1"]
        )
        
        dict_snapshot = snapshot.to_dict()
        
        assert dict_snapshot["phase"] == "test"
        assert len(dict_snapshot["findings"]) == 1
    
    def test_evolution_snapshot_from_dict(self):
        """测试 EvolutionSnapshot 反序列化"""
        data = {
            "phase": "test",
            "mode": "test",
            "status": "complete",
            "findings": [],
            "recommendations": [],
            "changes_made": [],
            "duration_seconds": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        snapshot = EvolutionSnapshot.from_dict(data)
        
        assert snapshot.phase == "test"
        assert snapshot.status == "complete"


class TestEvolutionPhase:
    """EvolutionPhase 枚举测试"""
    
    def test_phase_values(self):
        """测试阶段值"""
        assert EvolutionPhase.ANALYSIS.value == "analysis"
        assert EvolutionPhase.PLANNING.value == "planning"
        assert EvolutionPhase.EXECUTION.value == "execution"
        assert EvolutionPhase.VALIDATION.value == "validation"
        assert EvolutionPhase.COMPLETE.value == "complete"


class TestEvolutionMode:
    """EvolutionMode 枚举测试"""
    
    def test_mode_values(self):
        """测试模式值"""
        assert EvolutionMode.INCREMENTAL.value == "incremental"
        assert EvolutionMode.FULL.value == "full"
        assert EvolutionMode.TARGETED.value == "targeted"


class TestImportErrors:
    """导入错误测试"""
    
    def test_import_error_handling(self):
        """测试导入错误处理"""
        # 如果导入失败，应该返回 False
        if not IMPORTS_OK:
            assert IMPORT_ERROR is not None
        else:
            assert IMPORTS_OK == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
