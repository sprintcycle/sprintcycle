"""Targeted tests for API layering refactor services (no full SprintCycle import chain)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from sprintcycle.application.services.web_lifecycle_orchestration_service import (
    WebLifecycleOrchestrationService,
)


@pytest.fixture
def web_lifecycle() -> WebLifecycleOrchestrationService:
    return WebLifecycleOrchestrationService(
        project_path="/tmp/sc-test",
        start_execution_run=MagicMock(),
        runtime_lifecycle=lambda runtime_id="": {"success": True, "data": {"runtime": {}}},
        observability_trace=lambda run_id: {"success": True, "data": {}},
        evaluate_sprint_contract=lambda payload: {
            "data": {"score_card": {"passed": True}},
        },
    )


def test_normalize_lifecycle_request_returns_request_and_contract(
    web_lifecycle: WebLifecycleOrchestrationService,
) -> None:
    result = web_lifecycle.normalize_lifecycle_request(
        execution_id="exec-1",
        task_id="task-1",
    )
    assert "request" in result
    assert "contract" in result
    assert result["request"]["execution_id"] == "exec-1"
    assert result["contract"]["execution_id"] == "exec-1"


@pytest.mark.asyncio
async def test_orchestrate_web_request_without_execute(web_lifecycle: WebLifecycleOrchestrationService) -> None:
    result = await web_lifecycle.orchestrate_web_request(
        execution_id="exec-2",
        task_id="task-2",
        execute=False,
    )
    assert result["success"] is True
    data = result["contract"]
    assert data["validation_refs"]["normalized"] is True


def test_coerce_execution_contract_preserves_identity(web_lifecycle: WebLifecycleOrchestrationService) -> None:
    coerced = web_lifecycle.coerce_execution_contract(
        {"execution_id": "e3", "task_id": "t3", "project_path": "/tmp/sc-test"}
    )
    assert coerced["execution_id"] == "e3"
    assert coerced["task_id"] == "t3"
    assert coerced["validation_refs"]["has_identity"] is True