from sprintcycle.hooks import HookContext, HookDefinition, HookPhase, HookPolicy, HookRegistry, HookResult


def test_before_hook_can_block_main_flow():
    registry = HookRegistry()
    calls = []

    def blocker(ctx: HookContext):
        calls.append(ctx.action)
        return HookResult(ok=False, blocked=True, message="blocked")

    registry.register(
        HookDefinition(
            name="block_execution_start",
            domain="execution",
            action="start",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_CLOSED,
            handler=blocker,
        )
    )

    ctx = HookContext(domain="execution", action="start", subject_id="task-1", execution_id="run-1")
    results = registry.emit(domain="execution", action="start", phase=HookPhase.BEFORE, context=ctx)

    assert calls == ["start"]
    assert len(results) == 1
    assert results[0].blocked is True
    assert results[0].ok is False
    assert results[0].message == "blocked"


def test_before_hook_can_mutate_context():
    registry = HookRegistry()

    def enrich(ctx: HookContext):
        return {
            "ok": True,
            "mutated_context": {
                "payload": {"extra": 1},
                "metadata": {"source": "hook"},
                "subject_id": "task-2",
                "trace_id": "trace-1",
            },
        }

    registry.register(
        HookDefinition(
            name="enrich_execution_start",
            domain="execution",
            action="start",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_OPEN,
            handler=enrich,
        )
    )

    ctx = HookContext(domain="execution", action="start", subject_id="task-1", execution_id="run-1", payload={"base": True})
    results = registry.emit(domain="execution", action="start", phase=HookPhase.BEFORE, context=ctx)

    assert len(results) == 1
    assert results[0].ok is True
    assert ctx.payload == {"base": True, "extra": 1}
    assert ctx.metadata == {"source": "hook"}
    assert ctx.subject_id == "task-1"
    assert ctx.trace_id == ""


def test_handler_exception_is_converted_to_failed_result():
    registry = HookRegistry()

    def boom(ctx: HookContext):
        raise RuntimeError("boom")

    registry.register(
        HookDefinition(
            name="boom_execution_start",
            domain="execution",
            action="start",
            phase=HookPhase.BEFORE,
            policy=HookPolicy.FAIL_CLOSED,
            handler=boom,
        )
    )

    ctx = HookContext(domain="execution", action="start", subject_id="task-1", execution_id="run-1")
    results = registry.emit(domain="execution", action="start", phase=HookPhase.BEFORE, context=ctx)

    assert len(results) == 1
    assert results[0].ok is False
    assert results[0].blocked is True
    assert "boom" in results[0].message


def test_domain_event_handlers_are_called():
    registry = HookRegistry()
    seen = []

    def capture(payload):
        seen.append(payload)

    registry.register_event_handler("execution.started", capture)
    registry.emit_domain_event("execution.started", {"run_id": "run-1", "status": "ok"})

    assert seen == [{"run_id": "run-1", "status": "ok"}]


def test_hook_event_map_is_consistent():
    from sprintcycle.hooks import HOOK_ACTIONS, HOOK_EVENTS, hook_action, hook_events

    for key, action in HOOK_ACTIONS.items():
        domain, name = key.split(".", 1)
        assert hook_action(domain, name) == action
        assert isinstance(hook_events(domain, name), tuple)
        assert all(isinstance(item, str) for item in HOOK_EVENTS.get(key, ()))


def test_event_handler_exception_is_swallowed():
    registry = HookRegistry()
    seen = []

    def bad(payload):
        raise RuntimeError("nope")

    def good(payload):
        seen.append(payload)

    registry.register_event_handler("execution.started", bad)
    registry.register_event_handler("execution.started", good)
    registry.emit_domain_event("execution.started", {"run_id": "run-1"})

    assert seen == [{"run_id": "run-1"}]
