from sprintcycle.infrastructure.integrations.langgraph.compiler import compile_intent_graph, compile_sprint_graph


def test_compile_intent_graph_returns_runtime_metadata():
    runtime = compile_intent_graph()

    assert runtime.graph_name == "sprintcycle-intent"
    assert runtime.entrypoint == "intent_understand"
    assert runtime.finish_point == "intent_finalize"
    assert "intent_understand" in runtime.nodes
    assert any(edge["condition"] == "retry" for edge in runtime.edges)


def test_compile_sprint_graph_returns_runtime_metadata():
    runtime = compile_sprint_graph()

    assert runtime.graph_name == "sprintcycle-sprint"
    assert runtime.entrypoint == "sprint_prepare"
    assert runtime.finish_point == "sprint_finalize"
    assert "sprint_prepare" in runtime.nodes
    assert any(edge["condition"] == "retry" for edge in runtime.edges)
