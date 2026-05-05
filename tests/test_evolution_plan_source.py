"""
Tests for evolution plan sources

测试场景:
1. ManualPRDSource - YAML 文件加载
2. DiagnosticPRDSource - 诊断驱动计划生成
3. EvolutionReleasePlan 数据结构
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from sprintcycle.evolution.evolution_plan_source import (
    EvolutionReleasePlan,
    ManualPRDSource,
    DiagnosticPRDSource,
    EvolutionPlanSourceType,
)


class TestEvolutionReleasePlan:
    """EvolutionReleasePlan 测试"""

    def test_basic_creation(self):
        plan = EvolutionReleasePlan(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1", "Goal 2"],
            sprints=[{"name": "Sprint 1", "tasks": []}],
        )

        assert plan.name == "Test PRD"
        assert plan.version == "v1.0.0"
        assert len(plan.goals) == 2
        assert len(plan.sprints) == 1

    def test_total_tasks(self):
        plan = EvolutionReleasePlan(
            name="Test",
            version="v1.0",
            path="/test",
            sprints=[
                {"name": "S1", "tasks": [{"description": "T1"}, {"description": "T2"}]},
                {"name": "S2", "tasks": [{"description": "T3"}]},
            ],
        )

        assert plan.total_tasks == 3

    def test_metadata(self):
        plan = EvolutionReleasePlan(
            name="Test",
            version="v1.0",
            path="/test",
            metadata={"key": "value"},
            confidence=0.8,
            expected_benefit=10.0,
            priority=5,
        )

        assert plan.confidence == 0.8
        assert plan.expected_benefit == 10.0
        assert plan.priority == 5
        assert plan.metadata["key"] == "value"

    def test_to_dict(self):
        plan = EvolutionReleasePlan(
            name="Test PRD",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1"],
            sprints=[{"name": "Sprint 1", "tasks": []}],
            source_type=EvolutionPlanSourceType.MANUAL,
            confidence=0.9,
        )

        data = plan.to_dict()

        assert data["name"] == "Test PRD"
        assert data["version"] == "v1.0.0"
        assert data["source_type"] == "manual"
        assert data["confidence"] == 0.9
        assert data["total_tasks"] == 0


class TestManualPRDSource:
    """ManualPRDSource 测试类"""

    def test_init(self):
        source = ManualPRDSource()
        assert source._plan_subdir == Path("release_plan")

        source = ManualPRDSource("custom/release_plan")
        assert source._plan_subdir == Path("custom/release_plan")

    def test_get_source_type(self):
        source = ManualPRDSource()
        assert source.get_source_type() == EvolutionPlanSourceType.MANUAL

    def test_generate_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = ManualPRDSource()
            plans = source.generate(tmpdir)

            assert len(plans) == 0

    def test_generate_with_yaml(self):
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
                        {"description": "Task 1", "agent": "coder"},
                        {"description": "Task 2", "agent": "tester"},
                    ],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir) / "release_plan"
            plan_dir.mkdir()

            yaml_file = plan_dir / "test.yaml"
            with open(yaml_file, "w") as f:
                yaml.dump(prd_content, f)

            source = ManualPRDSource()
            plans = source.generate(tmpdir)

            assert len(plans) == 1
            plan = plans[0]
            assert plan.name == "Test Project"
            assert plan.version == "v1.0.0"
            assert len(plan.goals) == 2
            assert len(plan.sprints) == 1
            assert len(plan.sprints[0]["tasks"]) == 2

    def test_generate_with_priority(self):
        prd_content = {
            "project": {"name": "Test"},
            "sprints": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir) / "release_plan"
            plan_dir.mkdir()

            with open(plan_dir / "test.yaml", "w") as f:
                yaml.dump(prd_content, f)

            source = ManualPRDSource()
            plans = source.generate(tmpdir)

            assert plans[0].priority == 100
            assert plans[0].confidence == 1.0


class TestDiagnosticPRDSource:
    """DiagnosticPRDSource 测试类"""

    def test_init(self):
        source = DiagnosticPRDSource()
        assert source._diagnostic is None
        assert source._generator is None
        assert source._max_prds == 5

        source = DiagnosticPRDSource(max_prds=10)
        assert source._max_prds == 10

    def test_get_source_type(self):
        source = DiagnosticPRDSource()
        assert source.get_source_type() == EvolutionPlanSourceType.DIAGNOSTIC

    def test_filter_plans(self):
        source = DiagnosticPRDSource()

        plans = [
            EvolutionReleasePlan("P1", "v1", "/test", confidence=0.9, expected_benefit=10),
            EvolutionReleasePlan("P2", "v1", "/test", confidence=0.3, expected_benefit=5),
            EvolutionReleasePlan("P3", "v1", "/test", confidence=0.6, expected_benefit=-1),
            EvolutionReleasePlan("P4", "v1", "/test", confidence=0.7, expected_benefit=3),
        ]

        filtered = source._filter_plans(plans)

        assert len(filtered) == 2
        assert filtered[0].name == "P1"
        assert filtered[1].name == "P4"


class TestEvolutionPlanSourceType:
    """EvolutionPlanSourceType 测试"""

    def test_values(self):
        assert EvolutionPlanSourceType.MANUAL.value == "manual"
        assert EvolutionPlanSourceType.DIAGNOSTIC.value == "diagnostic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
