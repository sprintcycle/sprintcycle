import pytest

from sprintcycle.infrastructure.integrations.langgraph.intent_nodes import intent_evaluate, intent_finalize, sprint_split, should_retry
from sprintcycle.infrastructure.integrations.langgraph.sprint_nodes import sprint_finalize, sprint_prepare, should_retry_sprint


@pytest.mark.asyncio
async def test_intent_nodes_produce_structured_routing_state():
    state = {
        "intent": "deliver a release",
        "context": {},
        "attempt": 1,
        "sprint_results": [{"final_sprint_result": {"status": "failed"}}],
    }
    state = sprint_split(state)
    state = intent_evaluate(state)
    final_state = intent_finalize(state)

    assert state["evaluation"]["action"] in {"retry", "finalize"}
    assert final_state["final_result"]["sprint_count"] >= 1
    assert should_retry(state) in {"intent_understand", "finalize"}


@pytest.mark.asyncio
async def test_sprint_nodes_prepare_and_finalize_state():
    state = {
        "sprint": {"name": "sprint-1"},
        "context": {},
        "attempt": 1,
    }
    prepared = await sprint_prepare(state)
    finalized = await sprint_finalize({**prepared, "sprint_result": {"status": "success"}})

    assert prepared["sprint_context"]["sprint_name"] == "sprint-1"
    assert finalized["final_sprint_result"]["status"] == "success"
    assert should_retry_sprint({"repair_decision": {"action": "retry"}}) == "sprint_execute"
