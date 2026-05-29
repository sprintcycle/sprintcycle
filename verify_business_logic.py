#!/usr/bin/env python3
"""Verify that all core business logic is preserved after the refactoring."""

import sys
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecyclePhase,
    LifecycleSubstage,
    LifecycleStatus,
    create_lifecycle,
)
from sprintcycle.domain.core.lifecycle.values import StageEvidence
from sprintcycle.domain.core.lifecycle.state_machine import LifecycleStateMachine


def verify_lifecycle_creation():
    """Verify lifecycle creation works correctly."""
    print("📋 Verifying lifecycle creation...")
    lifecycle = create_lifecycle(
        execution_id="test-exec-001",
        task_id="test-task-001",
        project_path="/test/project"
    )
    
    assert lifecycle.execution_id == "test-exec-001"
    assert lifecycle.task_id == "test-task-001"
    assert lifecycle.project_path == "/test/project"
    assert lifecycle.phase == LifecyclePhase.INITIALIZING
    assert lifecycle.substage == LifecycleSubstage.NEW
    assert lifecycle.status == LifecycleStatus.PENDING
    print("✅ Lifecycle creation verified")


def verify_normal_workflow():
    """Verify the normal workflow from start to success."""
    print("\n📋 Verifying normal workflow...")
    lifecycle = create_lifecycle("test-exec-002", "test-task-002", "/test/project")
    
    # Initializing phase transitions
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.NORMALIZED, reason="normalized")
    assert lifecycle.phase == LifecyclePhase.INITIALIZING
    assert lifecycle.substage == LifecycleSubstage.NORMALIZED
    assert lifecycle.status == LifecycleStatus.RUNNING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PLANNED, reason="planned")
    assert lifecycle.phase == LifecyclePhase.INITIALIZING
    assert lifecycle.substage == LifecycleSubstage.PLANNED
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.DECOMPOSED, reason="decomposed")
    assert lifecycle.phase == LifecyclePhase.INITIALIZING
    assert lifecycle.substage == LifecycleSubstage.DECOMPOSED
    
    # Executing phase
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.RUNNING, reason="running")
    assert lifecycle.phase == LifecyclePhase.EXECUTING
    assert lifecycle.substage == LifecycleSubstage.RUNNING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.OBSERVING, reason="observing")
    assert lifecycle.phase == LifecyclePhase.EXECUTING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.DELIVERING, reason="delivering")
    assert lifecycle.phase == LifecyclePhase.DELIVERING
    assert lifecycle.substage == LifecycleSubstage.DELIVERING
    
    # Delivering phase
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.RUNTIME_LINKED, reason="runtime_linked")
    assert lifecycle.phase == LifecyclePhase.DELIVERING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.GOVERNING, reason="governing")
    assert lifecycle.phase == LifecyclePhase.GOVERNING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PROMOTION_READY, reason="promotion_ready")
    assert lifecycle.phase == LifecyclePhase.GOVERNING
    
    # Success terminal state
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PROMOTED, reason="promoted")
    assert lifecycle.phase == LifecyclePhase.TERMINAL
    assert lifecycle.substage == LifecycleSubstage.PROMOTED
    assert lifecycle.status == LifecycleStatus.PROMOTED
    print("✅ Normal workflow verified")


def verify_failure_and_recovery():
    """Verify failure and recovery logic works correctly."""
    print("\n📋 Verifying failure and recovery workflow...")
    lifecycle = create_lifecycle("test-exec-003", "test-task-003", "/test/project")
    
    # Go through normal transitions to running
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.NORMALIZED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PLANNED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.DECOMPOSED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.RUNNING)
    
    # Trigger failure
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.FAILED, reason="test failure")
    assert lifecycle.phase == LifecyclePhase.TERMINAL
    assert lifecycle.substage == LifecycleSubstage.FAILED
    assert lifecycle.status == LifecycleStatus.FAILED
    
    # Trigger recovery
    lifecycle = lifecycle.trigger_recovery(failure_kind="test_error", reason="test recovery")
    assert lifecycle.phase == LifecyclePhase.EXECUTING
    assert lifecycle.substage == LifecycleSubstage.REPAIRING
    
    # Complete recovery workflow
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.VERIFYING, reason="verifying")
    assert lifecycle.phase == LifecyclePhase.EXECUTING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.OBSERVING, reason="observing")
    assert lifecycle.phase == LifecyclePhase.EXECUTING
    
    # Return to delivering
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.DELIVERING, reason="back to delivering")
    assert lifecycle.phase == LifecyclePhase.DELIVERING
    assert lifecycle.substage == LifecycleSubstage.DELIVERING
    assert lifecycle.status == LifecycleStatus.RUNNING
    print("✅ Failure and recovery workflow verified")


def verify_state_machine():
    """Verify state machine rules are preserved."""
    print("\n📋 Verifying state machine rules...")
    machine = LifecycleStateMachine()
    
    # Check valid transitions exist
    assert machine.can_transition("new", "normalized")
    assert machine.can_transition("normalized", "planned")
    assert machine.can_transition("planned", "decomposed")
    assert machine.can_transition("decomposed", "running")
    assert machine.can_transition("running", "observing")
    assert machine.can_transition("observing", "delivering")
    assert machine.can_transition("failed", "repairing")
    assert machine.can_transition("repairing", "verifying")
    assert machine.can_transition("verifying", "observing")
    
    # Check terminal states can't transition
    assert machine.can_transition("promoted", "normalized") is False
    assert machine.can_transition("cancelled", "running") is False
    
    # Check recovery targets
    assert machine.get_recovery_target("failed") == "repairing"
    assert machine.get_recovery_target("running") == "repairing"
    print("✅ State machine rules verified")


def verify_serialization():
    """Verify lifecycle serialization and deserialization work."""
    print("\n📋 Verifying lifecycle serialization...")
    lifecycle = create_lifecycle("test-exec-004", "test-task-004", "/test/project")
    
    # Add some state
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.NORMALIZED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PLANNED)
    lifecycle = lifecycle.add_stage_evidence(StageEvidence(
        stage="planned",
        present=True,
        evidence={"test": "data"}
    ))
    
    # Serialize and deserialize
    data = lifecycle.to_dict()
    restored = LifecycleRoot.from_dict(data)
    
    assert restored.execution_id == lifecycle.execution_id
    assert restored.phase == lifecycle.phase
    assert restored.substage == lifecycle.substage
    assert restored.status == lifecycle.status
    print("✅ Serialization verified")


def verify_governance_flow():
    """Verify governance flow through substage transitions."""
    print("\n📋 Verifying governance flow...")
    lifecycle = create_lifecycle("test-exec-005", "test-task-005", "/test/project")
    
    # Normal flow to delivering phase
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.NORMALIZED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PLANNED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.DECOMPOSED)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.RUNNING)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.OBSERVING)
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.DELIVERING)
    
    # Delivering phase flow
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.RUNTIME_LINKED)
    assert lifecycle.phase == LifecyclePhase.DELIVERING
    assert lifecycle.substage == LifecycleSubstage.RUNTIME_LINKED
    
    # Governance phase flow
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.GOVERNING)
    assert lifecycle.phase == LifecyclePhase.GOVERNING
    assert lifecycle.substage == LifecycleSubstage.GOVERNING
    
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PROMOTION_READY)
    assert lifecycle.phase == LifecyclePhase.GOVERNING
    assert lifecycle.substage == LifecycleSubstage.PROMOTION_READY
    
    # Complete
    lifecycle = lifecycle.transition_to_substage(LifecycleSubstage.PROMOTED)
    assert lifecycle.phase == LifecyclePhase.TERMINAL
    assert lifecycle.substage == LifecycleSubstage.PROMOTED
    print("✅ Governance flow verified")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("🔍 SprintCycle Business Logic Verification")
    print("=" * 60)
    
    try:
        verify_lifecycle_creation()
        verify_normal_workflow()
        verify_failure_and_recovery()
        verify_state_machine()
        verify_serialization()
        verify_governance_flow()
        
        print("\n" + "=" * 60)
        print("🎉 All business logic verified! No functionality lost.")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
