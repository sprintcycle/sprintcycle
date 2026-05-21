"""Top-level LangGraph nodes for SprintCycle orchestration."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from .states import IntentState


async def _get_llm_response(prompt: str) -> Dict[str, Any]:
    from sprintcycle.llm import get_llm  # type: ignore

    llm = get_llm()
    response = await llm.ainvoke(prompt)
    if hasattr(response, "to_dict"):
        return response.to_dict()
    if isinstance(response, dict):
        return dict(response)
    return {"raw": response}


async def intent_understand(state: IntentState) -> IntentState:
    intent = str(state.get("intent", ""))
    attempt = int(state.get("attempt", 1) or 1)
    # dry_run: skip LLM call, use fallback
    context = state.get("context", {}) or {}
    if context.get("runtime_config", {}).get("dry_run"):
        return {
            **state,
            "attempt": attempt + 1,
            "intent_analysis": {"goals": [intent], "constraints": [], "priority": "high"},
            "goals": [intent],
        }
    prompt = (
        "分析用户意图，提取以下信息：\n"
        f"用户意图: {intent}\n"
        '请输出JSON格式：{"goals": [], "constraints": [], "priority": "high"}'
    )
    try:
        parsed = await _get_llm_response(prompt)
    except Exception as exc:  # pragma: no cover - defensive graph safety
        return {
            **state,
            "attempt": attempt + 1,
            "error": f"intent_understand_failed: {exc}",
            "intent_analysis": {"goals": [intent]},
        }
    return {
        **state,
        "attempt": attempt + 1,
        "intent_analysis": parsed,
        "goals": parsed.get("goals", [intent]),
    }


async def plan_generate(state: IntentState) -> IntentState:
    goals = state.get("goals", [state.get("intent", "")])
    context = state.get("context", {}) or {}
    if context.get("runtime_config", {}).get("dry_run"):
        # Generate minimal sprint plan from context
        release_plan = context.get("release_plan", {})
        rp = getattr(release_plan, "to_dict", lambda: {"sprints": []})() if not isinstance(release_plan, dict) else release_plan
        return {
            **state,
            "release_plan": rp,
            "release_plan_source": "dry_run",
        }
    prompt = f"根据以下目标生成Sprint计划：\n目标: {goals}\n输出JSON格式的ReleasePlan"
    try:
        release_plan = await _get_llm_response(prompt)
    except Exception as exc:  # pragma: no cover - defensive graph safety
        return {
            **state,
            "error": f"plan_generate_failed: {exc}",
            "release_plan": {"sprints": []},
            "release_plan_source": "llm_error_fallback",
        }
    return {
        **state,
        "release_plan": release_plan,
        "release_plan_source": "llm_generated",
    }


def sprint_split(state: IntentState) -> IntentState:
    release_plan = state.get("release_plan", {}) or {}
    sprints = list(release_plan.get("sprints", []) or [])
    if not sprints:
        sprints = [
            {
                "name": "sprint-1",
                "goals": [state.get("intent", "deliver value")],
                "tasks": [],
            }
        ]
    return {**state, "sprints": sprints}


async def sprint_dispatch(state: IntentState) -> IntentState:
    from .sprint_graph import SprintGraphRuntime

    sprint_graph = SprintGraphRuntime()
    results: List[Dict[str, Any]] = []
    sprints = list(state.get("sprints", []) or [])
    context = dict(state.get("context", {}))
    for sprint in sprints:
        result = await sprint_graph.run(sprint=sprint, context=context)
        results.append(result)
    return {**state, "sprint_results": results}


def intent_evaluate(state: IntentState) -> IntentState:
    sprint_results = list(state.get("sprint_results", []) or [])
    failed_count = 0
    failed_sprints: List[Dict[str, Any]] = []
    for result in sprint_results:
        final_result = result.get("final_sprint_result", {}) or {}
        status = str(final_result.get("status", "")).lower()
        if status not in {"success", "skipped"}:
            failed_count += 1
            failed_sprints.append(
                {
                    "sprint_name": final_result.get("sprint_name", result.get("sprint", {}).get("name", "")),
                    "status": status or "unknown",
                    "repair_action": (result.get("repair_decision", {}) or {}).get("action", "unknown"),
                }
            )
    if failed_count > 0 and int(state.get("attempt", 1) or 1) < 3:
        evaluation = {
            "action": "retry",
            "reason": "sprints_failed",
            "failed_sprint_count": failed_count,
            "failed_sprints": failed_sprints,
        }
    else:
        evaluation = {
            "action": "finalize",
            "reason": "done",
            "failed_sprint_count": failed_count,
            "failed_sprints": failed_sprints,
        }
    return {**state, "evaluation": evaluation}


def intent_finalize(state: IntentState) -> IntentState:
    sprints = list(state.get("sprints", []) or [])
    evaluation = dict(state.get("evaluation", {}) or {})
    final_result = {
        "sprint_count": len(sprints),
        "failed_count": int(evaluation.get("failed_sprint_count", 0) or 0),
        "status": evaluation.get("action", "finalize"),
    }
    return {**state, "final_result": final_result}


def should_retry(state: IntentState) -> Literal["intent_understand", "finalize"]:
    evaluation = state.get("evaluation", {}) or {}
    attempt = int(state.get("attempt", 1) or 1)
    if evaluation.get("action") == "retry" and attempt < 3:
        return "intent_understand"
    return "finalize"


__all__ = [
    "intent_understand",
    "plan_generate",
    "sprint_split",
    "sprint_dispatch",
    "intent_evaluate",
    "intent_finalize",
    "should_retry",
]
