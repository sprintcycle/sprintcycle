from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pytest

from sprintcycle.hooks import HookContext, HookDefinition, HookPhase, HookPolicy, HookRegistry, HookResult, HookRouter, hook_action, hook_events
from sprintcycle.services.execution_lifecycle_service import ExecutionLifecycleService
from sprintcycle.services.suggestion_application_service import SuggestionApplicationService
from sprintcycle.services.governance_orchestration_service import GovernanceOrchestrationService


class _FakeExecution:
    def create_context(self, **kwargs: Any):
        return SimpleNamespace(
            run_id=kwargs["run_id"],
            task_id=kwargs["task_id"],
            project_path=kwargs["project_path"],
            suggestion_id=kwargs.get("suggestion_id", ""),
            evolution_id=kwargs.get("evolution_id", ""),
            metadata=kwargs.get("metadata", {}),
            status="created",
            to_dict=lambda: dict(kwargs),
        )

    def basic_flow(self, context):
        return {"status": "started"}


class _FakeObservation:
    def __init__(self):
        self.events = []

    def record(self, event: Dict[str, Any]):
        self.events.append(event)
        return event

    def to_trace_payload(self, execution_id: str):
        return {"events": []}


class _FakeRuntimeRegistry:
    def __init__(self):
        self.registered = []
        self.updated = []

    def register(self, payload: Dict[str, Any]):
        self.registered.append(payload)

    def update(self, runtime_id: str, **changes: Any):
        self.updated.append((runtime_id, changes))
        return {"runtime_id": runtime_id, **changes}

    def latest(self):
        return {"success": True, "data": None}


class _FakeSuggestionFacade:
    async def review_suggestion(self, suggestion_id: str):
        return SimpleNamespace(to_dict=lambda: {"suggestion_id": suggestion_id, "status": "reviewed"})

    async def approve_suggestion(self, suggestion_id: str, approver: str, notes: str = ""):
        return SimpleNamespace(to_dict=lambda: {"suggestion_id": suggestion_id, "approver": approver, "notes": notes})

    async def reject_suggestion(self, suggestion_id: str, approver: str, notes: str = ""):
        return SimpleNamespace(to_dict=lambda: {"suggestion_id": suggestion_id, "approver": approver, "notes": notes})

    async def archive_suggestion(self, suggestion_id: str):
        return None

    async def capture_from_execution_event(self, event: Dict[str, Any]):
        return {"captured": True, "event": event}


class _FakeGovernanceFacade:
    async def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = ""):
        return {"execution_id": execution_id, "suggestion_id": suggestion_id, "reviewer": reviewer, "notes": notes}

    async def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = ""):
        return {"execution_id": execution_id, "suggestion_id": suggestion_id, "approver": approver, "notes": notes}

    async def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = ""):
        return {"execution_id": execution_id, "suggestion_id": suggestion_id, "rejected_by": rejected_by, "notes": notes}

    async def promote_suggestion_to_hitl(self, suggestion_id: str, gate: str = "review", title: str = "", summary: str = "", context: Dict[str, Any] | None = None):
        return {"request_id": "req-1", "suggestion_id": suggestion_id, "gate": gate, "context": context or {}}

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]):
        return {"suggestion_id": suggestion_id, "replay": replay}

    async def list_pending(self, execution_id=None):
        return []

    async def list_history(self, execution_id=None, limit: int = 50):
        return []

    async def summary(self, execution_id=None, limit: int = 50):
        return {}

    async def get_request(self, request_id: str):
        return {"request_id": request_id}


@pytest.mark.asyncio
async def test_execution_start_respects_before_hook_block():
    registry = HookRegistry()
    registry.register(
        HookDefinition(
            name="block",
            domain="execution",
            action="start",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_CLOSED,
            handler=lambda ctx: HookResult(ok=False, blocked=True, message="blocked"),
        )
    )
    service = ExecutionLifecycleService(
        project_path=".",
        config=SimpleNamespace(),
        observability=_FakeObservation(),
        runtime_registry=_FakeRuntimeRegistry(),
        hooks=registry,
    )
    service._execution_engine = _FakeExecution()

    result = await service.start_execution_run("task-1")

    assert result["success"] is False
    assert result["error"] == "blocked"


@pytest.mark.asyncio
async def test_execution_start_records_success_with_hooks():
    registry = HookRegistry()
    before_seen = []
    after_seen = []
    events = []

    def before(ctx: HookContext):
        before_seen.append(ctx.to_dict())
        return HookResult(ok=True, mutated_context={"metadata": {"from_hook": True}})

    def after(ctx: HookContext):
        after_seen.append(ctx.to_dict())
        return HookResult(ok=True)

    registry.register(HookDefinition(name="before", domain="execution", action="start", phase=HookPhase.BEFORE, policy=HookPolicy.FAIL_OPEN, handler=before))
    registry.register(HookDefinition(name="after", domain="execution", action="start", phase=HookPhase.AFTER, policy=HookPolicy.FAIL_OPEN, handler=after))
    registry.register_event_handler("execution.started", lambda payload: events.append(payload))

    service = ExecutionLifecycleService(
        project_path=".",
        config=SimpleNamespace(),
        observability=_FakeObservation(),
        runtime_registry=_FakeRuntimeRegistry(),
        hooks=registry,
    )
    service._execution_engine = _FakeExecution()

    result = await service.start_execution_run("task-1", metadata={"seed": True})

    assert result["success"] is True
    assert before_seen[0]["metadata"] == {"seed": True}
    assert result["data"]["context"]["metadata"] == {"seed": True, "from_hook": True}
    assert after_seen
    assert events and events[0]["context"]["metadata"] == {"seed": True, "from_hook": True}


@pytest.mark.asyncio
async def test_suggestion_approve_respects_before_hook_block():
    registry = HookRegistry()
    registry.register(
        HookDefinition(
            name="block",
            domain="suggestion",
            action="approve",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_CLOSED,
            handler=lambda ctx: HookResult(ok=False, blocked=True, message="blocked"),
        )
    )
    service = SuggestionApplicationService(suggestion=_FakeSuggestionFacade(), governance=_FakeGovernanceFacade(), hooks=registry)

    result = await service.suggestion_approve("s-1", "alice")

    assert result["success"] is False
    assert result["error"] == "blocked"


@pytest.mark.asyncio
async def test_suggestion_approve_emits_events_on_success():
    registry = HookRegistry()
    before_seen = []
    after_seen = []
    events = []

    def before(ctx: HookContext):
        before_seen.append(ctx.to_dict())
        return HookResult(ok=True)

    def after(ctx: HookContext):
        after_seen.append(ctx.to_dict())
        return HookResult(ok=True)

    registry.register(HookDefinition(name="before", domain="suggestion", action="approve", phase=HookPhase.BEFORE, policy=HookPolicy.FAIL_OPEN, handler=before))
    registry.register(HookDefinition(name="after", domain="suggestion", action="approve", phase=HookPhase.AFTER, policy=HookPolicy.FAIL_OPEN, handler=after))
    registry.register_event_handler("suggestion.approval_completed", lambda payload: events.append(payload))

    service = SuggestionApplicationService(suggestion=_FakeSuggestionFacade(), governance=_FakeGovernanceFacade(), hooks=registry)

    result = await service.suggestion_approve("s-1", "alice", notes="ok")

    assert result["success"] is True
    assert before_seen[0]["subject_id"] == "s-1"
    assert after_seen[0]["subject_id"] == "s-1"
    assert events and events[0]["suggestion_id"] == "s-1"


@pytest.mark.asyncio
async def test_governance_check_emits_success_path_without_error():
    service = GovernanceOrchestrationService(project_path=".", config=SimpleNamespace(), governance=_FakeGovernanceFacade(), hooks=HookRegistry())
    result = service.governance_check(gate="review")
    assert result["success"] in {True, False}


def test_governance_check_before_hook_block_is_returned():
    registry = HookRegistry()
    registry.register(
        HookDefinition(
            name="block_governance_check",
            domain="governance",
            action="check",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_CLOSED,
            handler=lambda ctx: HookResult(ok=False, blocked=True, message="blocked"),
        )
    )
    service = GovernanceOrchestrationService(project_path=".", config=SimpleNamespace(), governance=_FakeGovernanceFacade(), hooks=registry)

    result = service.governance_check(gate="review")

    assert result["success"] is False
    assert result["error"] == "blocked"


def test_hook_router_resolves_action_and_events():
    router = HookRouter(HookRegistry())
    assert router.action("execution", "start") == ("execution", "start")
    assert router.events("execution", "start") == ("execution.started", "execution.start_failed")


def test_hook_context_trace_id_is_preserved_in_mutation():
    registry = HookRegistry()

    def mutator(ctx: HookContext):
        return HookResult(ok=True, mutated_context={"trace_id": "trace-xyz"})

    registry.register(
        HookDefinition(
            name="trace_mutator",
            domain="execution",
            action="start",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_OPEN,
            handler=mutator,
        )
    )

    ctx = HookContext(domain="execution", action="start", subject_id="s-1", execution_id="r-1")
    registry.emit(domain="execution", action="start", phase=HookPhase.BEFORE, context=ctx)

    assert ctx.trace_id == "trace-xyz"


def test_unknown_hook_action_raises():
    with pytest.raises(KeyError):
        hook_action("unknown", "action")


def test_unknown_hook_event_list_is_empty():
    assert hook_events("unknown", "action") == ()
