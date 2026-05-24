"""
Tests for plan sources — 产出 ``ReleasePlan``。
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from sprintcycle.domain.evolution.evolution_plan_source import (
    DiagnosticReleasePlanSource,
    EvolutionPlanSourceType,
    ManualReleasePlanSource,
)
from sprintcycle.domain.generic.models.release_plan.builders import release_plan_from_diagnostic_slices
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
                "path": ".",
                "version": "v1.0.0",
            },
            "mode": "normal",
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
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(yaml_fixture, f)

            source = ManualReleasePlanSource()
            plans = source.generate(tmpdir)

            assert len(plans) == 1
            plan = plans[0]
            assert plan.project.name == "Test Project"
            assert plan.project.version == "v1.0.0"
            assert len(plan.sprints) == 1
            assert len(plan.sprints[0].tasks) == 2
            assert plan.metadata.get("diagnostic_priority") == 100

    def test_generate_metadata_priority(self):
        yaml_fixture = {
            "project": {"name": "Test", "path": ".", "version": "v1.0"},
            "mode": "normal",
            "sprints": [
                {
                    "name": "S1",
                    "goals": [],
                    "tasks": [{"description": "t", "agent": "coder"}],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir) / "release_plan"
            plan_dir.mkdir()

            with open(plan_dir / "test.yaml", "w", encoding="utf-8") as f:
                yaml.dump(yaml_fixture, f)

            source = ManualReleasePlanSource()
            plans = source.generate(tmpdir)

            assert plans[0].metadata.get("diagnostic_priority") == 100
            assert plans[0].metadata.get("diagnostic_confidence") == 1.0


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

        def one_task_sprint() -> list:
            return [
                {
                    "name": "S1",
                    "goals": [],
                    "tasks": [{"description": "x", "agent": "coder"}],
                }
            ]

        plans = [
            release_plan_from_diagnostic_slices(
                plan_name="P1",
                project_path="/test",
                sprint_dicts=one_task_sprint(),
                rule="r",
                confidence=0.9,
                expected_benefit=10.0,
                priority=1,
            ),
            release_plan_from_diagnostic_slices(
                plan_name="P2",
                project_path="/test",
                sprint_dicts=one_task_sprint(),
                rule="r",
                confidence=0.3,
                expected_benefit=5.0,
                priority=1,
            ),
            release_plan_from_diagnostic_slices(
                plan_name="P3",
                project_path="/test",
                sprint_dicts=one_task_sprint(),
                rule="r",
                confidence=0.6,
                expected_benefit=-1.0,
                priority=1,
            ),
            release_plan_from_diagnostic_slices(
                plan_name="P4",
                project_path="/test",
                sprint_dicts=one_task_sprint(),
                rule="r",
                confidence=0.7,
                expected_benefit=3.0,
                priority=1,
            ),
        ]

        filtered = source._filter_plans(plans)

        assert len(filtered) == 2
        assert filtered[0].project.name == "P1"
        assert filtered[1].project.name == "P4"


class TestEvolutionPlanSourceType:
    """EvolutionPlanSourceType 测试"""

    def test_values(self):
        assert EvolutionPlanSourceType.MANUAL.value == "manual"
        assert EvolutionPlanSourceType.DIAGNOSTIC.value == "diagnostic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
