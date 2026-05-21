"""
调度器单元测试
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.application.evolution.measurement import MeasurementResult
from sprintcycle.execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from sprintcycle.application.sprint_orchestrator import SprintOrchestrator, _measurement_run_metadata
from sprintcycle.application.release_plan.models import (
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)


class TestSprintOrchestrator:
    """Sprint 编排器测试"""

    def setup_method(self):
        """测试前准备（dry_run 避免真实 LLM / Aider 调用）"""
        self.orchestrator = SprintOrchestrator(config=RuntimeConfig(dry_run=True, quality_level="L1"))

    def test_orchestrator_initialization(self):
        """测试编排器初始化"""
        assert self.orchestrator is not None
    def test_execute_normal_release_plan(self):
        """测试执行普通 ReleasePlan"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            mode=ExecutionMode.NORMAL,
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    goals=["完成开发"],
                    tasks=[
                        SprintBacklogItem(description="实现功能 A", agent="coder"),
                        SprintBacklogItem(description="实现功能 B", agent="coder"),
                    ]
                ),
            ]
        )

        # 同步运行
        results = asyncio.run(self.orchestrator.execute_release_plan(plan))

        assert len(results) == 1
        assert results[0].sprint.name == "Sprint 1"
        assert len(results[0].task_results) == 2

    def test_execute_multiple_sprints(self):
        """测试执行多个 Sprint"""
        plan = ReleasePlan(
            project=ProductAnchor(name="test", path="/root/test"),
            mode=ExecutionMode.NORMAL,
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    tasks=[
                        SprintBacklogItem(description="任务 1", agent="coder"),
                    ]
                ),
                SprintDefinition(
                    name="Sprint 2",
                    tasks=[
                        SprintBacklogItem(description="任务 2", agent="coder"),
                    ]
                ),
            ]
        )

        results = asyncio.run(self.orchestrator.execute_release_plan(plan))

        assert len(results) == 2
        assert results[0].sprint.name == "Sprint 1"
        assert results[1].sprint.name == "Sprint 2"

    def test_execute_evolution_expands_to_sprints(self):
        """自进化模式经展开后与 SprintExecutor 单一路径一致。"""
        from sprintcycle.application.release_plan.models import EvolutionParams

        plan = ReleasePlan(
            project=ProductAnchor(name="evo", path="/root/test"),
            mode=ExecutionMode.EVOLUTION,
            evolution=EvolutionParams(
                targets=["src/x.py"],
                goals=["提升可读性"],
                constraints=["保持 API 兼容"],
            ),
            sprints=[],
        )
        results = asyncio.run(self.orchestrator.execute_release_plan(plan))
        assert len(results) == 1
        assert results[0].sprint.name == "进化: src/x.py"
        assert len(results[0].task_results) == 4
        agents = [tr.work_item.agent for tr in results[0].task_results]
        assert agents == ["architect", "coder", "tester", "regression_tester"]

    def test_get_summary(self):
        """测试获取摘要"""
        summary = self.orchestrator.get_summary()

        assert "callbacks" in summary
        assert isinstance(summary["callbacks"], list)

    @pytest.mark.asyncio
    async def test_post_sprint_measurement_injects_run_metadata(self, tmp_path):
        """Sprint 后测量写入 llm / 引擎元数据（F-3）。"""
        cfg = RuntimeConfig(
            dry_run=True,
            quality_level="L2",
            llm_provider="test-provider",
            llm_model="test-model",
            coding_engine="cursor",
        )
        orch = SprintOrchestrator(config=cfg, project_path=str(tmp_path))
        plan = ReleasePlan(
            project=ProductAnchor(name="p", path=str(tmp_path)),
            mode=ExecutionMode.NORMAL,
            sprints=[],
        )
        fixed = MeasurementResult(
            overall=1.0,
            correctness=1.0,
            details={"quality_level": "L2"},
        )
        with patch("sprintcycle.application.evolution.measurement.MeasurementProvider") as MP:
            inst = MagicMock()
            inst.measure_all.return_value = fixed
            inst.check_quality_gate.return_value = True
            MP.return_value = inst
            sp = SprintDefinition(
                name="S-A",
                tasks=[SprintBacklogItem(description="do thing", agent="coder")],
            )
            tr = TaskResult(
                work_item=sp.tasks[0],
                sprint_name=sp.name,
                status=ExecutionStatus.SUCCESS,
                output="ok",
            )
            sr = SprintResult(sprint=sp, status=ExecutionStatus.SUCCESS, task_results=[tr], duration=0.1)
            m = await orch._post_sprint_measurement(
                plan,
                sprint_index=0,
                sprint=sp,
                sprint_result=sr,
            )
        assert m is fixed
        rm = m.details.get("run_metadata")
        assert rm["llm_provider"] == "test-provider"
        assert rm["llm_model"] == "test-model"
        assert rm["coding_engine"] == "cursor"
        assert rm["quality_level"] == "L2"
        assert rm["dry_run"] is True
        assert "project_path" in rm
        assert len(rm.get("config_fingerprint", "")) == 16
        assert rm.get("release_plan_name") == "p"
        assert rm.get("sprint_name") == "S-A"
        assert rm.get("sprint_index") == 0
        assert len(rm.get("task_outcome_digest", "")) == 16
        assert len(rm.get("measurement_context_hash", "")) == 16
        assert rm.get("prompt_sources_schema") == 1
        assert len(rm.get("prompt_sources_aggregate_sha256", "")) == 64
        assert "execution.agents.coder_generation" in (rm.get("prompt_source_digests") or {})


def test_measurement_context_hash_depends_on_task_outcomes():
    cfg = RuntimeConfig(dry_run=True, quality_level="L2")
    sp = SprintDefinition(name="S", tasks=[SprintBacklogItem(description="a", agent="coder")])
    tr_ok = TaskResult(work_item=sp.tasks[0], sprint_name="S", status=ExecutionStatus.SUCCESS)
    tr_fail = TaskResult(work_item=sp.tasks[0], sprint_name="S", status=ExecutionStatus.FAILED, error="x")
    sr1 = SprintResult(sprint=sp, status=ExecutionStatus.SUCCESS, task_results=[tr_ok], duration=1.0)
    sr2 = SprintResult(sprint=sp, status=ExecutionStatus.FAILED, task_results=[tr_fail], duration=1.0)
    m1 = _measurement_run_metadata(cfg, sprint_index=0, sprint=sp, sprint_result=sr1)
    m2 = _measurement_run_metadata(cfg, sprint_index=0, sprint=sp, sprint_result=sr2)
    assert m1["task_outcome_digest"] != m2["task_outcome_digest"]
    assert m1["measurement_context_hash"] != m2["measurement_context_hash"]


def test_measurement_run_metadata_evolution_env(monkeypatch):
    monkeypatch.setenv("EVOLUTION_LLM_MODEL", "evo-test-model")
    monkeypatch.setenv("EVOLUTION_LLM_PROVIDER", "evo-prov")
    rm = _measurement_run_metadata(
        RuntimeConfig(llm_model="m", llm_provider="p", coding_engine="aider", dry_run=True)
    )
    assert rm.get("evolution_llm_model_env") == "evo-test-model"
    assert rm.get("evolution_llm_provider_env") == "evo-prov"


def test_measurement_run_metadata_ci_matrix_and_incremental():
    cfg = RuntimeConfig(
        dry_run=True,
        quality_level="L2",
        governance_ci_matrix_tags="py311, ubuntu",
        test_command_incremental="pytest tests/ -q --lf",
    )
    rm = _measurement_run_metadata(cfg)
    assert rm.get("test_command_incremental") == "pytest tests/ -q --lf"
    assert sorted(rm.get("ci_matrix_tags", [])) == ["py311", "ubuntu"]


class TestTaskResult:
    """任务结果测试"""

    def test_task_result_creation(self):
        """测试创建任务结果"""
        task = SprintBacklogItem(description="测试任务", agent="coder")
        result = TaskResult(
            work_item=task,
            sprint_name="Sprint 1",
            status=ExecutionStatus.SUCCESS,
            output="完成",
            duration=10.5,
        )

        assert result.work_item.description == "测试任务"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.duration == 10.5

    def test_task_result_to_dict(self):
        """测试任务结果序列化"""
        task = SprintBacklogItem(description="测试任务", agent="coder", target="src/main.py")
        result = TaskResult(
            work_item=task,
            sprint_name="Sprint 1",
            status=ExecutionStatus.SUCCESS,
        )

        result_dict = result.to_dict()

        assert "description" in result_dict
        assert "agent" in result_dict
        assert result_dict["status"] == "success"


class TestSprintResult:
    """Sprint 结果测试"""

    def test_sprint_result_calculations(self):
        """测试 Sprint 结果计算"""
        sprint = SprintDefinition(
            name="Sprint 1",
            tasks=[
                SprintBacklogItem(description="任务1", agent="coder"),
                SprintBacklogItem(description="任务2", agent="coder"),
                SprintBacklogItem(description="任务3", agent="coder"),
            ]
        )

        results = [
            TaskResult(
                work_item=sprint.tasks[0],
                sprint_name="Sprint 1",
                status=ExecutionStatus.SUCCESS,
            ),
            TaskResult(
                work_item=sprint.tasks[1],
                sprint_name="Sprint 1",
                status=ExecutionStatus.SUCCESS,
            ),
            TaskResult(
                work_item=sprint.tasks[2],
                sprint_name="Sprint 1",
                status=ExecutionStatus.FAILED,
            ),
        ]

        sprint_result = SprintResult(
            sprint=sprint,
            status=ExecutionStatus.SUCCESS,
            task_results=results,
            duration=30.0,
        )

        assert sprint_result.success_count == 2
        assert sprint_result.failed_count == 1
        assert sprint_result.success_rate == pytest.approx(2/3)

    def test_sprint_result_empty(self):
        """测试空 Sprint 结果"""
        sprint = SprintDefinition(name="Sprint 1", tasks=[])
        sprint_result = SprintResult(
            sprint=sprint,
            status=ExecutionStatus.SKIPPED,
            task_results=[],
        )

        assert sprint_result.success_count == 0
        assert sprint_result.success_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
