"""Sprint 结束后将结构化摘要沉淀为知识卡片（SQLite knowledge_cards）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from sprintcycle.domain.evolution.measurement import MeasurementResult
    from sprintcycle.domain.models import ReleasePlan, SprintDefinition
    from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
    from sprintcycle.domain.interfaces import SprintResult


def persist_sprint_outcome_card(
    *,
    project_path: str,
    config: "RuntimeConfig",
    release_plan: "ReleasePlan",
    sprint_index: int,
    sprint: "SprintDefinition",
    sprint_result: "SprintResult",
    measurement: Optional["MeasurementResult"],
) -> Optional[str]:
    """
    将单次 Sprint 结果写入知识库（与 executions 共用 sqlite_path 时同库）。

    P2 企业审计/Helm 等不在此实现；仅写卡片表，供后续检索与注入复用。
    """
    if not getattr(config, "persist_sprint_knowledge_cards", True):
        return None
    try:
        from sprintcycle.infrastructure.persistence.knowledge_repository import KnowledgeCardRepository
        from sprintcycle.infrastructure.knowledge.knowledge_hook import resolve_knowledge_db_path
    except Exception as e:  # pragma: no cover
        logger.debug("knowledge card deps unavailable: {}", e)
        return None

    try:
        db_path = resolve_knowledge_db_path(project_path, config)
        repo = KnowledgeCardRepository(db_path)
    except Exception as e:
        logger.warning("Sprint 知识卡片跳过（无法打开知识库）: {}", e)
        return None

    ok = (
        sprint_result.status.value in ("success", "skipped")
        if hasattr(sprint_result.status, "value")
        else str(sprint_result.status) in ("success", "skipped")
    )
    lessons: Dict[str, Any] = {
        "sprint_index": sprint_index,
        "sprint_status": getattr(sprint_result.status, "value", str(sprint_result.status)),
        "success_count": sprint_result.success_count,
        "failed_count": sprint_result.failed_count,
        "task_count": len(sprint_result.task_results),
        "duration_sec": sprint_result.duration,
    }
    errors: List[str] = []
    related: List[str] = []
    for tr in sprint_result.task_results:
        t = tr.work_item
        if getattr(t, "target", None):
            related.append(str(t.target))
        if tr.status.value != "success" if hasattr(tr.status, "value") else str(tr.status) != "success":
            if tr.error:
                errors.append(f"{t.agent}: {tr.error[:500]}")

    if errors:
        lessons["task_errors"] = errors

    scores: Dict[str, Any] = {}
    if measurement is not None:
        scores = {
            "overall": measurement.overall,
            "correctness": measurement.correctness,
            "code_quality": measurement.code_quality,
        }
        rm = (measurement.details or {}).get("run_metadata")
        if isinstance(rm, dict) and rm:
            scores["run_metadata"] = dict(rm)

    domain = getattr(release_plan.project, "name", "") or "sprint"
    outcome = "success" if ok else "failed"
    body_lines = [
        f"Sprint「{sprint.name}」完成于项目 {domain}。",
        f"任务成功 {sprint_result.success_count}/{len(sprint_result.task_results)}。",
    ]
    if errors:
        body_lines.append("失败摘要: " + "; ".join(errors[:3]))
    body = "\n".join(body_lines)

    sprint_id = f"{getattr(release_plan, 'execution_id', None) or 'run'}:{sprint_index}:{sprint.name}"

    try:
        card = repo.add(
            domain=domain,
            outcome=outcome,
            body=body,
            sprint_id=sprint_id,
            lessons=lessons,
            related_files=list({p for p in related if p}),
            tags=["sprint_outcome", "auto"],
            scores=scores,
        )
        logger.info("已写入 Sprint 结果知识卡片 id={} sprint_id={}", card.id, sprint_id)
        return card.id
    except Exception as e:
        logger.warning("写入 Sprint 知识卡片失败: {}", e)
        return None
