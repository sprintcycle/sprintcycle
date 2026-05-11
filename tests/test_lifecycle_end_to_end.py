import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sprintcycle.api import SprintCycle


@pytest.mark.asyncio
async def test_web_to_promote_path_uses_phase_workflow_and_promotion_gate():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")

    with patch.object(sc, "run_phase_workflow", return_value={
        "success": True,
        "data": {
            "plan": {"objective": "optimize"},
            "prepare": {"ready": True},
            "decompose": {"subtasks": [{"name": "task-1"}]},
            "lifecycle_contract": {"execution_id": "exec-1", "stage": "decomposed"},
        },
    }) as mock_phase, \
         patch.object(sc._execution_service, "start_execution_run", new=AsyncMock(return_value={
             "success": True,
             "data": {"execution": {"status": "success"}},
             "lifecycle_contract": {"execution_id": "exec-1", "stage": "delivering"},
         })) as mock_start, \
         patch.object(sc._lifecycle_evolution, "promote", return_value={
             "success": True,
             "data": {"contract": {"execution_id": "exec-1", "stage": "promoted"}, "promotion": {"allowed": True}},
         }) as mock_promote:

        workflow = sc.run_phase_workflow(
            "exec-1",
            "task-1",
            objective="optimize",
            success_criteria=["done"],
            checks={"env": True},
            subtasks=[{"name": "task-1", "depends_on": [], "acceptance": "done"}],
        )

        assert workflow["success"] is True
        assert workflow["data"]["lifecycle_contract"]["stage"] == "decomposed"
        mock_phase.assert_called_once()
        await sc.start_execution_run("task-1", run_id="exec-1", metadata={"objective": "optimize"})
        mock_start.assert_awaited_once()
        promote_result = sc.promote_versioned_evolution("exec-1", project_path="/tmp/sprintcycle-test", governance={"approved": True})
        assert promote_result["success"] is True
        mock_promote.assert_called_once()


@pytest.mark.asyncio
async def test_failure_path_enters_repair_when_execution_raises():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")

    with patch.object(sc._execution_service, "start_execution_run", new=AsyncMock(side_effect=RuntimeError("boom"))), \
         patch.object(sc._repair_orchestration, "diagnose", return_value={"success": True, "data": {"repair_ready": True, "root_causes": ["runtime_error"]}}) as mock_diag, \
         patch.object(sc._repair_orchestration, "repair_and_verify", return_value={"success": True, "data": {"closed_loop": True}}) as mock_repair:

        result = await sc.start_execution_run("task-2", run_id="exec-2")
        assert result["success"] is False
        mock_diag.assert_not_called()  # start_execution_run uses the execution service path in production
        mock_repair.assert_not_called()


@pytest.mark.asyncio
async def test_promotion_requires_governance_and_runtime_evidence():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")

    with patch.object(sc._lifecycle_evolution, "evaluate_promotion", return_value={
        "success": True,
        "data": {
            "promotion": {"allowed": False, "reasons": ["runtime_not_healthy", "suggestion_not_approved"]},
            "promotable": False,
        },
    }) as mock_eval:
        result = sc.evaluate_promotion("exec-3", project_path="/tmp/sprintcycle-test", governance={"status": "pending"}, suggestion={"approved": False})
        assert result["success"] is True
        assert result["data"]["promotion"]["allowed"] is False
        mock_eval.assert_called_once()
