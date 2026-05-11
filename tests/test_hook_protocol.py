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


def test_domain_event_handlers_are_called():
    registry = HookRegistry()
    seen = []

    def capture(payload):
        seen.append(payload)

    registry.register_event_handler("execution.started", capture)
    registry.emit_domain_event("execution.started", {"run_id": "run-1", "status": "ok"})

    assert seen == [{"run_id": "run-1", "status": "ok"}]
