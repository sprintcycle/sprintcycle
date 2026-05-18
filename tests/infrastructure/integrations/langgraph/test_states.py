from sprintcycle.infrastructure.integrations.langgraph.states import IntentState, SprintState


def test_state_types_accept_expected_keys():
    intent_state: IntentState = {
        "intent": "build feature",
        "context": {},
        "attempt": 1,
        "timeline": [],
    }
    sprint_state: SprintState = {
        "sprint": {"name": "sprint-1"},
        "context": {},
        "attempt": 1,
        "timeline": [],
    }

    assert intent_state["intent"] == "build feature"
    assert sprint_state["sprint"]["name"] == "sprint-1"
