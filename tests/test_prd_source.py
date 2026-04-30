"""
Tests for PRD Source - PRD来源测试

测试场景:
1. ManualPRDSource - YAML文件加载
2. DiagnosticPRDSource - 诊断驱动PRD生成
3. EvolutionPRD数据结构
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from sprintcycle.evolution.prd_source import (
    PRDSource,
    EvolutionPRD,
    ManualPRDSource,
    DiagnosticPRDSource,
    PRDSourceType,
)


class TestEvolutionPRD:
    """EvolutionPRD测试类"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1", "Goal 2"],
            sprints=[{"name": "Sprint 1", "tasks": []}],
        )
        
        assert prd.name == "Test PRD"
        assert prd.version == "v1.0.0"
        assert len(prd.goals) == 2
        assert len(prd.sprints) == 1
    
    def test_total_tasks(self):
        """测试任务计数"""
        prd = EvolutionPRD(
            name="Test",
            version="v1.0",
            path="/test",
            sprints=[
                {"name": "S1", "tasks": [{"task": "T1"}, {"task": "T2"}]},
                {"name": "S2", "tasks": [{"task": "T3"}]},
            ],
        )
        
        assert prd.total_tasks == 3
    
    def test_metadata(self):
        """测试元数据"""
        prd = EvolutionPRD(
            name="Test",
            version="v1.0",
            path="/test",
            metadata={"key": "value"},
            confidence=0.8,
            expected_benefit=10.0,
            priority=5,
        )
        
        assert prd.confidence == 0.8
        assert prd.expected_benefit == 10.0
        assert prd.priority == 5
        assert prd.metadata["key"] == "value"
    
    def test_to_dict(self):
        """测试序列化"""
        prd = EvolutionPRD(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1"],
            sprints=[{"name": "Sprint 1", "tasks": []}],
            source_type=PRDSourceType.MANUAL,
            confidence=0.9,
        )
        
        data = prd.to_dict()
        
        assert data["name"] == "Test PRD"
        assert data["version"] == "v1.0.0"
        assert data["source_type"] == "manual"
        assert data["confidence"] == 0.9
        assert data["total_tasks"] == 0


class TestManualPRDSource:
    """ManualPRDSource测试类"""
    
    def test_init(self):
        """测试初始化"""
        source = ManualPRDSource()
        assert source._prd_dir == Path("prd")
        
        source = ManualPRDSource("custom/prd")
        assert source._prd_dir == Path("custom/prd")
    
    def test_get_source_type(self):
        """测试来源类型"""
        source = ManualPRDSource()
        assert source.get_source_type() == PRDSourceType.MANUAL
    
    def test_generate_empty_dir(self):
        """测试空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = ManualPRDSource()
            prds = source.generate(tmpdir)
            
            assert len(prds) == 0
    
    def test_generate_with_yaml(self):
        """测试加载YAML文件"""
        prd_content = {
            "project": {
                "name": "Test Project",
                "version": "v1.0.0",
            },
            "sprints": [
                {
                    "name": "Sprint 1",
                    "goals": ["Goal 1", "Goal 2"],
                    "tasks": [
                        {"task": "Task 1", "agent": "coder"},
                        {"task": "Task 2", "agent": "tester"},
                    ],
                },
            ],
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建prd目录和文件
            prd_dir = Path(tmpdir) / "prd"
            prd_dir.mkdir()
            
            yaml_file = prd_dir / "test.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(prd_content, f)
            
            source = ManualPRDSource()
            prds = source.generate(tmpdir)
            
            assert len(prds) == 1
            prd = prds[0]
            assert prd.name == "Test Project"
            assert prd.version == "v1.0.0"
            assert len(prd.goals) == 2
            assert len(prd.sprints) == 1
            assert len(prd.sprints[0]["tasks"]) == 2
    
    def test_generate_with_priority(self):
        """测试优先级设置"""
        prd_content = {
            "project": {"name": "Test"},
            "sprints": [],
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_dir = Path(tmpdir) / "prd"
            prd_dir.mkdir()
            
            with open(prd_dir / "test.yaml", "w") as f:
                yaml.dump(prd_content, f)
            
            source = ManualPRDSource()
            prds = source.generate(tmpdir)
            
            # ManualPRD应该有最高优先级
            assert prds[0].priority == 100
            assert prds[0].confidence == 1.0


class TestDiagnosticPRDSource:
    """DiagnosticPRDSource测试类"""
    
    def test_init(self):
        """测试初始化"""
        source = DiagnosticPRDSource()
        assert source._diagnostic is None
        assert source._generator is None
        assert source._max_prds == 5
        
        source = DiagnosticPRDSource(max_prds=10)
        assert source._max_prds == 10
    
    def test_get_source_type(self):
        """测试来源类型"""
        source = DiagnosticPRDSource()
        assert source.get_source_type() == PRDSourceType.DIAGNOSTIC
    
    def test_filter_prds(self):
        """测试PRD过滤"""
        source = DiagnosticPRDSource()
        
        prds = [
            EvolutionPRD("P1", "v1", "/test", confidence=0.9, expected_benefit=10),
            EvolutionPRD("P2", "v1", "/test", confidence=0.3, expected_benefit=5),  # 过滤
            EvolutionPRD("P3", "v1", "/test", confidence=0.6, expected_benefit=-1),  # 过滤
            EvolutionPRD("P4", "v1", "/test", confidence=0.7, expected_benefit=3),
        ]
        
        filtered = source._filter_prds(prds)
        
        assert len(filtered) == 2
        assert filtered[0].name == "P1"
        assert filtered[1].name == "P4"


class TestPRDSourceType:
    """PRDSourceType测试类"""
    
    def test_values(self):
        """测试枚举值"""
        assert PRDSourceType.MANUAL.value == "manual"
        assert PRDSourceType.DIAGNOSTIC.value == "diagnostic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
