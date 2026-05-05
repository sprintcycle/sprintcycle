"""
EvolutionReleasePlan → 主路径 ``release_plan.models.PRD``（V4.0 §6.2 委托 ``SprintOrchestrator`` 时使用）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from ..release_plan.models import PRD, ExecutionMode, PRDProject, PRDSprint, PRDTask
from .evolution_plan_source import EvolutionReleasePlan


def _task_dict_to_prd_task(t: Any) -> PRDTask:
    if isinstance(t, PRDTask):
        return t
    if isinstance(t, str):
        return PRDTask(description=t, agent="coder")
    if isinstance(t, dict):
        desc = t.get("description")
        if desc is None or (isinstance(desc, str) and not str(desc).strip()):
            raise ValueError("Sprint Backlog item dict must include non-empty 'description'")
        return PRDTask(
            description=str(desc),
            agent=str(t.get("agent") or "coder"),
            target=t.get("target"),
            constraints=list(t.get("constraints") or []),
            expected_output=t.get("expected_output"),
            timeout=int(t.get("timeout") or 600),
        )
    return PRDTask(description=str(t), agent="coder")


def evolution_release_plan_to_prd(evo: EvolutionReleasePlan, project_root: str) -> PRD:
    raw = (evo.path or project_root or ".").strip() or "."
    try:
        p = Path(raw)
        resolved = str(p.resolve()) if p.exists() else raw
    except Exception:
        resolved = raw
    proj = PRDProject(name=evo.name, path=resolved, version=str(evo.version))
    sprints: List[PRDSprint] = []
    for sp in evo.sprints:
        if not isinstance(sp, dict):
            continue
        name = str(sp.get("name") or "sprint")
        goals = [str(g) for g in sp.get("goals", [])]
        raw_tasks = sp.get("tasks", [])
        tasks = [_task_dict_to_prd_task(t) for t in raw_tasks]
        sprints.append(PRDSprint(name=name, goals=goals, tasks=tasks))
    meta = dict(evo.metadata) if evo.metadata else {}
    src_val = (
        evo.source_type.value
        if hasattr(evo.source_type, "value")
        else str(evo.source_type)
    )
    meta.setdefault("evolution_release_plan_source", src_val)
    return PRD(project=proj, mode=ExecutionMode.NORMAL, sprints=sprints, metadata=meta)
