"""Sprint-level LangGraph runtime wrapper."""

from __future__ import annotations

from typing import Any, Dict

from .compiler import compile_sprint_graph


class SprintGraphRuntime:
    """Wrapper around the compiled sprint-level LangGraph."""

    def __init__(self) -> None:
        self._runtime = compile_sprint_graph()

    async def run(self, sprint: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        state = {"sprint": sprint, "context": context}
        result = await self._runtime.graph.ainvoke(state)
        return dict(result or {})
