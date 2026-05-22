"""End-to-end lifecycle tests for SprintCycle."""

import pytest
from unittest.mock import AsyncMock, patch

from sprintcycle.application.services.lifecycle_contracts import validate_lifecycle_evidence


@pytest.mark.asyncio
async def test_promotion_rejected_when_stage_history_is_missing():
    """Test promotion is rejected when stage history is incomplete."""
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
            "runtime": {"linked": True, "healthy": True, "present": True},
            "suggestion": {"approved": True, "present": True},
            "governing": {"approved": True},
            "governance": {"approved": True, "present": True},
            "promotion": {"evidence": True, "completion_score": 100.0},
            "evolution": {"versioned": True, "version_id": "version-8", "present": True},
        },
    }

    errors = validate_lifecycle_evidence(contract)
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_evidence_validator_rejects_incomplete_stage_schema():
    """Test evidence validator rejects incomplete stage schemas."""
    incomplete_contract = {
        "execution_id": "exec-11",
        "stage": "promotion_ready",
        "evidence": {
            "contract": {"normalized": True},
            "stages": {},
            "runtime": {"linked": True, "healthy": True},
            "suggestion": {"approved": True},
            "governing": {"approved": True},
            "governance": {"approved": True},
        },
    }

    errors = validate_lifecycle_evidence(incomplete_contract)
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_promotion_rejected_when_evidence_is_incomplete():
    """Test promotion is rejected when evidence is incomplete."""
    incomplete_contract = {
        "execution_id": "exec-12",
        "task_id": "exec-12",
        "project_path": "/tmp/sprintcycle-test",
        "stage": "promotion_ready",
        "status": "pending",
        "evidence": {
            "contract": {"normalized": True},
            "stages": {
                "plan": {"present": True},
            },
        },
    }

    errors = validate_lifecycle_evidence(incomplete_contract)
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_promotion_rejected_when_versioning_evidence_is_missing():
    """Test promotion is rejected when versioning evidence is missing."""
    contract = {
        "execution_id": "exec-9",
        "task_id": "exec-9",
        "project_path": "/tmp/sprintcycle-test",
        "stage": "promotion_ready",
        "status": "pending",
        "validation_refs": {"ok": True, "normalized": True, "trace_present": True},
        "evidence": {
            "contract": {"normalized": True},
            "stages": {
                "plan": {"present": True},
                "prepare": {"present": True},
                "decompose": {"present": True},
                "execute": {"present": True},
                "observe": {"present": True},
                "diagnose": {"present": True},
                "deliver": {"present": True},
                "repair": {"present": True},
                "verify": {"present": True},
            },
            "runtime": {"linked": True, "healthy": True, "present": True},
            "suggestion": {"approved": True, "present": True},
            "governing": {"approved": True},
            "governance": {"approved": True, "present": True},
            "promotion": {"evidence": True, "completion_score": 100.0},
        },
    }

    errors = validate_lifecycle_evidence(contract)
    assert len(errors) > 0
