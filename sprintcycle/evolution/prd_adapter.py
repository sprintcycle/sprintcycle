"""
EvolutionPRD → 主路径 PRD 模型（V4.0 §6.2 委托 TaskDispatcher 时使用）
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from ..prd.models import PRD, ExecutionMode, PRDProject, PRDSprint, PRDTask
from .prd_source import EvolutionPRD


def _task_dict_to_prd_task(t: Any) -> PRDTask:
    if isinstance(t, PRDTask):
        return t
    if isinstance(t, str):
        return PRDTask(task=t, agent="coder")
    if isinstance(t, dict):
        desc = t.get("task") or t.get("name") or "task"
        return PRDTask(
            task=str(desc),
            agent=str(t.get("agent") or "coder"),
            target=t.get("target"),
            constraints=list(t.get("constraints") or []),
            expected_output=t.get("expected_output"),
            timeout=int(t.get("timeout") or 600),
        )
    return PRDTask(task=str(t), agent="coder")


def evolution_prd_to_prd(evo: EvolutionPRD, project_root: str) -> PRD:
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
    meta.setdefault("evolution_prd_source", evo.source_type.value if hasattr(evo.source_type, "value") else str(evo.source_type))
    return PRD(project=proj, mode=ExecutionMode.NORMAL, sprints=sprints, metadata=meta)
