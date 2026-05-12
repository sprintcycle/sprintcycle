import pytest
from unittest.mock import AsyncMock, patch

from sprintcycle.api import SprintCycle
from sprintcycle.services.lifecycle_contracts import validate_lifecycle_evidence


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

    with patch.object(sc._execution_service, "start_execution_run", new=AsyncMock(side_effect=RuntimeError("boom"))):
        result = await sc.start_execution_run("task-2", run_id="exec-2")
        assert result["success"] is False


@pytest.mark.asyncio
async def test_lifecycle_evolution_contract_contains_standard_evidence():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")
    result = sc.promote_versioned_evolution("exec-5", project_path="/tmp/sprintcycle-test", governance={"approved": True}, suggestion={"approved": True})

    assert result["success"] is True
    contract = result["data"]["contract"]
    assert contract["evidence"]["contract"]["normalized"] is True
    assert contract["evidence"]["stages"]["repair"]["closed_loop"] is True
    assert contract["evidence"]["stages"]["verify"]["closed_loop"] is True
    assert contract["evidence"]["governing"]["approved"] is True
    assert contract["evidence"]["governance"]["approved"] is True


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


@pytest.mark.asyncio
async def test_promotion_rejected_when_stage_history_is_missing():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")
    contract = {
        "execution_id": "exec-8",
        "task_id": "exec-8",
        "project_path": "/tmp/sprintcycle-test",
        "stage": "promotion_ready",
        "status": "pending",
        "validation_refs": {"ok": True, "normalized": True, "trace_present": True},
        "evidence": {
            "contract": {"normalized": True},
            "stages": {
                "plan": {"objective": "opt", "present": True},
                "prepare": {"ready": True, "checks": {}, "blockers": [], "present": True},
                "decompose": {"subtasks": [], "present": True},
                "execute": {"trace": {"events": [1]}, "present": True},
                "observe": {"trace": {"events": [1]}, "diagnostics": {}, "present": True},
                "diagnose": {"root_causes": [], "repair_ready": False, "confidence": 0.0, "recommendations": [], "present": True},
                "deliver": {"outputs": {}, "runtime_linkage": {}, "present": True},
                "repair": {"attempted": True, "closed_loop": True, "verify_result": {}, "present": True},
                "verify": {"closed_loop": True, "verify_result": {}, "present": True},
            },
            "runtime": {"linked": True, "healthy": True},
            "suggestion": {"approved": True},
            "governing": {"approved": True},
            "governance": {"approved": True},
            "promotion": {"evidence": True, "completion_score": 100.0},
            "evolution": {"versioned": True, "version_id": "version-8"},
        },
    }

    policy_result = sc._lifecycle_evolution.promotion_policy.evaluate(contract, runtime={"healthy": True}, governance={"approved": True})
    assert policy_result["allowed"] is False
    assert "missing_stage_history" in policy_result["reasons"]


@pytest.mark.asyncio
async def test_full_web_lifecycle_orchestrates_to_decomposition():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")

    result = sc.orchestrate_web_request(
        execution_id="exec-0",
        task_id="task-0",
        objective="optimize",
        success_criteria=["done"],
        checks={"env": True},
        subtasks=[{"name": "task-a", "depends_on": [], "acceptance": "done"}],
    )

    assert result["success"] is True
    contract = result["data"]["lifecycle_contract"]
    assert contract["stage"] == "decomposed"
    assert contract["evidence"]["contract"]["normalized"] is True
    assert contract["evidence"]["stages"]["plan"]["present"] is True
    assert contract["evidence"]["stages"]["prepare"]["present"] is True
    assert contract["evidence"]["stages"]["decompose"]["present"] is True


@pytest.mark.asyncio
async def test_promotion_rejected_when_versioning_evidence_is_missing():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")
    contract = {
        "execution_id": "exec-9",
        "task_id": "exec-9",
        "project_path": "/tmp/sprintcycle-test",
        "stage": "promotion_ready",
        "status": "pending",
        "stage_history": [{"from": "governing", "to": "promotion_ready", "at": "now", "reason": "gate"}],
        "validation_refs": {"ok": True, "normalized": True, "trace_present": True},
        "evidence": {
            "contract": {"normalized": True},
            "stages": {
                "plan": {"objective": "opt", "present": True},
                "prepare": {"ready": True, "checks": {}, "blockers": [], "present": True},
                "decompose": {"subtasks": [], "present": True},
                "execute": {"trace": {"events": [1]}, "present": True},
                "observe": {"trace": {"events": [1]}, "diagnostics": {}, "present": True},
                "diagnose": {"root_causes": [], "repair_ready": False, "confidence": 0.0, "recommendations": [], "present": True},
                "deliver": {"outputs": {}, "runtime_linkage": {}, "present": True},
                "repair": {"attempted": True, "closed_loop": True, "verify_result": {}, "present": True},
                "verify": {"closed_loop": True, "verify_result": {}, "present": True},
            },
            "runtime": {"linked": True, "healthy": True},
            "suggestion": {"approved": True},
            "governing": {"approved": True},
            "governance": {"approved": True},
            "promotion": {"evidence": True, "completion_score": 100.0},
            "evolution": {"versioned": False, "version_id": "version-9"},
        },
    }

    policy_result = sc._lifecycle_evolution.promotion_policy.evaluate(contract, runtime={"healthy": True}, governance={"approved": True})
    assert policy_result["allowed"] is False
    assert any(reason.startswith("evidence_invalid:") for reason in policy_result["reasons"])


@pytest.mark.asyncio
async def test_promote_versioned_evolution_builds_versioned_contract():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")
    result = sc.promote_versioned_evolution("exec-4", project_path="/tmp/sprintcycle-test", governance={"approved": True}, suggestion={"approved": True})

    assert result["success"] is True
    contract = result["data"]["contract"]
    assert contract["stage"] == "promoted"
    assert contract["evidence"]["evolution"]["versioned"] is True
    assert contract["validation_refs"]["versioned_evolution"] is True
    assert result["data"]["version"]["versioned"] is True


@pytest.mark.asyncio
async def test_evidence_validator_rejects_incomplete_stage_schema():
    incomplete_contract = {
        "evidence": {
            "contract": {"normalized": True},
            "stages": {"prepare": {"ready": True}},
            "runtime": {"linked": True, "healthy": True},
            "governance": {"approved": True},
            "promotion": {"evidence": True, "completion_score": 100.0},
            "evolution": {"versioned": True, "version_id": "version-x"},
        }
    }

    errors = validate_lifecycle_evidence(incomplete_contract)
    assert errors
    assert any("evidence.stages.plan" in error for error in errors)
    assert any("evidence.stages.decompose" in error for error in errors)


@pytest.mark.asyncio
async def test_promotion_rejected_when_evidence_is_incomplete():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")
    contract = {
        "execution_id": "exec-6",
        "task_id": "exec-6",
        "project_path": "/tmp/sprintcycle-test",
        "stage": "promotion_ready",
        "status": "pending",
        "stage_history": [{"from": "governing", "to": "promotion_ready", "at": "now", "reason": "gate"}],
        "validation_refs": {"ok": True},
        "evidence": {
            "contract": {"normalized": True},
            "stages": {
                "plan": {"present": True},
                "prepare": {"ready": True, "checks": {}, "blockers": [], "present": True},
                "decompose": {"subtasks": [], "present": True},
                "execute": {"trace": {}, "present": True},
                "observe": {"trace": {}, "diagnostics": {}, "present": True},
                "diagnose": {"root_causes": [], "repair_ready": False, "confidence": 0.0, "recommendations": [], "present": True},
                "deliver": {"outputs": {}, "runtime_linkage": {}, "present": True},
                "repair": {"attempted": True, "closed_loop": False, "verify_result": {}, "present": True},
                "verify": {"closed_loop": False, "verify_result": {}, "present": True},
            },
            "runtime": {"linked": True, "healthy": True},
            "suggestion": {"approved": True},
            "governance": {"approved": True},
            "promotion": {"evidence": True, "completion_score": 100.0},
            "evolution": {"versioned": False, "version_id": "version-6"},
        },
    }

    policy_result = sc._lifecycle_evolution.promotion_policy.evaluate(contract, runtime={"healthy": True}, governance={"approved": True})
    assert policy_result["allowed"] is False
    assert any(reason.startswith("evidence_invalid:") for reason in policy_result["reasons"])


@pytest.mark.asyncio
async def test_recovery_path_closes_loop_before_promotion():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")

    observation = sc.diagnose_repair_observe("exec-recover", repair_plan={"steps": ["fix-1"]})
    assert observation["success"] is True
    lifecycle_contract = observation["data"]["lifecycle_contract"]
    assert lifecycle_contract["stage"] in {"observing", "diagnosed", "repairing", "verifying", "failed"}
    assert lifecycle_contract["recovery_refs"]["closed_loop"] is True
    assert lifecycle_contract["recovery_refs"]["repair"]
    assert lifecycle_contract["recovery_refs"]["verify"]


@pytest.mark.asyncio
async def test_promotion_rejected_when_runtime_is_not_healthy():
    sc = SprintCycle(project_path="/tmp/sprintcycle-test")
    result = sc._lifecycle_evolution.promotion_policy.evaluate(
        {
            "execution_id": "exec-7",
            "task_id": "exec-7",
            "project_path": "/tmp/sprintcycle-test",
            "stage": "promotion_ready",
            "status": "pending",
            "stage_history": [{"from": "governing", "to": "promotion_ready", "at": "now", "reason": "gate"}],
            "validation_refs": {"ok": True, "normalized": True, "trace_present": True, "versioned_evolution": True},
            "evidence": {
                "contract": {"normalized": True},
                "stages": {
                    "plan": {"objective": "opt", "present": True},
                    "prepare": {"ready": True, "checks": {}, "blockers": [], "present": True},
                    "decompose": {"subtasks": [], "present": True},
                    "execute": {"trace": {"events": [1]}, "present": True},
                    "observe": {"trace": {"events": [1]}, "diagnostics": {}, "present": True},
                    "diagnose": {"root_causes": [], "repair_ready": False, "confidence": 0.0, "recommendations": [], "present": True},
                    "deliver": {"outputs": {}, "runtime_linkage": {}, "present": True},
                    "repair": {"attempted": True, "closed_loop": True, "verify_result": {}, "present": True},
                    "verify": {"closed_loop": True, "verify_result": {}, "present": True},
                },
                "runtime": {"linked": True, "healthy": False},
                "suggestion": {"approved": True},
                "governing": {"approved": True},
                "promotion": {"evidence": True, "completion_score": 100.0},
                "evolution": {"versioned": True, "version_id": "version-7"},
            },
        },
        runtime={"healthy": False},
        governance={"approved": True},
    )
    assert result["allowed"] is False
    assert "runtime_not_healthy" in result["reasons"]
