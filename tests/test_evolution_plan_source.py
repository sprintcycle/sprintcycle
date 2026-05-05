"""
Tests for evolution plan sources

测试场景:
1. ManualReleasePlanSource - YAML 文件加载
2. DiagnosticReleasePlanSource - 诊断驱动计划生成
3. EvolutionReleasePlan 数据结构
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from sprintcycle.evolution.evolution_plan_source import (
    EvolutionReleasePlan,
    ManualReleasePlanSource,
    DiagnosticReleasePlanSource,
    EvolutionPlanSourceType,
)


class TestEvolutionReleasePlan:
    """EvolutionReleasePlan 测试"""

    def test_basic_creation(self):
        plan = EvolutionReleasePlan(
            name="Test ReleasePlan",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1", "Goal 2"],
            sprints=[{"name": "Sprint 1", "tasks": []}],
        )

        assert plan.name == "Test ReleasePlan"
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
            name="Test ReleasePlan",
            version="v1.0.0",
            path="/test/project",
            goals=["Goal 1"],
            sprints=[{"name": "Sprint 1", "tasks": []}],
            source_type=EvolutionPlanSourceType.MANUAL,
            confidence=0.9,
        )

        data = plan.to_dict()

        assert data["name"] == "Test ReleasePlan"
        assert data["version"] == "v1.0.0"
        assert data["source_type"] == "manual"
        assert data["confidence"] == 0.9
        assert data["total_tasks"] == 0


class TestManualReleasePlanSource:
    """ManualReleasePlanSource 测试类"""

    def test_init(self):
        source = ManualReleasePlanSource()
        assert source._plan_subdir == Path("release_plan")

        source = ManualReleasePlanSource("custom/release_plan")
        assert source._plan_subdir == Path("custom/release_plan")

    def test_get_source_type(self):
        source = ManualReleasePlanSource()
        assert source.get_source_type() == EvolutionPlanSourceType.MANUAL

    def test_generate_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = ManualReleasePlanSource()
            plans = source.generate(tmpdir)

            assert len(plans) == 0

    def test_generate_with_yaml(self):
        yaml_fixture = {
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
                yaml.dump(yaml_fixture, f)

            source = ManualReleasePlanSource()
            plans = source.generate(tmpdir)

            assert len(plans) == 1
            plan = plans[0]
            assert plan.name == "Test Project"
            assert plan.version == "v1.0.0"
            assert len(plan.goals) == 2
            assert len(plan.sprints) == 1
            assert len(plan.sprints[0]["tasks"]) == 2

    def test_generate_with_priority(self):
        yaml_fixture = {
            "project": {"name": "Test"},
            "sprints": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir) / "release_plan"
            plan_dir.mkdir()

            with open(plan_dir / "test.yaml", "w") as f:
                yaml.dump(yaml_fixture, f)

            source = ManualReleasePlanSource()
            plans = source.generate(tmpdir)

            assert plans[0].priority == 100
            assert plans[0].confidence == 1.0


class TestDiagnosticReleasePlanSource:
    """DiagnosticReleasePlanSource 测试类"""

    def test_init(self):
        source = DiagnosticReleasePlanSource()
        assert source._diagnostic is None
        assert source._generator is None
        assert source._max_plans == 5

        source = DiagnosticReleasePlanSource(max_plans=10)
        assert source._max_plans == 10

    def test_get_source_type(self):
        source = DiagnosticReleasePlanSource()
        assert source.get_source_type() == EvolutionPlanSourceType.DIAGNOSTIC

    def test_filter_plans(self):
        source = DiagnosticReleasePlanSource()

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
