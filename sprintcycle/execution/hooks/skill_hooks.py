"""Skill 生命周期钩子实现。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sprintcycle.domain.models import ReleasePlan, SprintDefinition
from ..core.protocols import SkillChecklistItem, SkillTrace
from ..agents.skill_models import SkillArtifact, SkillExecutionRecord, SkillInjectionState
from ..agents.skill_store import SkillStore
from ..agents.skills import SkillOrchestrator
from ..core.sprint_types import SprintResult
from .sprint_hooks import SprintLifecycleHooks


class SkillLifecycleHook(SprintLifecycleHooks):
    def __init__(self, orchestrator: SkillOrchestrator, store: Optional[SkillStore] = None) -> None:
        self._orchestrator = orchestrator
        self._store = store or SkillStore()

    def _match_to_checklist(self, match: Dict[str, Any]) -> SkillChecklistItem:
        return SkillChecklistItem(
            category="skill",
            title=f"{match['skill_id']} 相关审查",
            required=True,
            source=match.get("source", "skill"),
            details={"skill_id": match["skill_id"], "version": match.get("version", "latest")},
        )

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        task_text = sprint.goals[0] if sprint.goals else sprint.name
        matches = self._orchestrator.after_plan(task_text, context)
        match_dicts = [m.snapshot().to_dict() for m in matches]
        context["skill_matches"] = match_dicts
        execution_id = context.get("execution_id", "default")
        for m in match_dicts:
            state = SkillInjectionState(skill_id=m["skill_id"], scene=m["scene"])
            state.injection_source = m["path"]
            state.review_checklist = [self._match_to_checklist(m)]
            state.prompt_fragments = [f"skill:{m['skill_id']}", f"version:{m['version']}", f"source:{m['source']}"]
            state.mark_injected()
            self._store.save_state(execution_id, sprint.name, task_text, state)
            artifact = self._store.get_latest_artifact(m["skill_id"])
            if artifact is None:
                self._store.upsert_artifact(
                    SkillArtifact(
                        skill_id=m["skill_id"],
                        version=m["version"],
                        path=m["path"],
                        content_hash=m.get("checksum", ""),
                        source=m.get("source", "openclaw"),
                        status="injected",
                    )
                )
            else:
                artifact.status = "injected"
                artifact.path = m["path"]
                artifact.version = m["version"]
                artifact.source = m.get("source", "openclaw")
                self._store.upsert_artifact(artifact)
        trace = SkillTrace(
            execution_id=execution_id,
            sprint_name=sprint.name,
            task_name=task_text,
            scene=context.get("skill_scene", "general"),
            matched_skills=[m["skill_id"] for m in match_dicts],
            injected_skills=[m["skill_id"] for m in match_dicts],
            review_checklist=[self._match_to_checklist(m) for m in match_dicts],
            retro_metrics={"market_source": "openclaw"},
        )
        context["task_skill_trace"] = trace.to_dict()

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        execution_id = context.get("execution_id", "default")
        task_name = sprint.goals[0] if sprint.goals else sprint.name
        review_status = "passed" if result.status.value == "success" else "failed"
        review_score = 1.0 if review_status == "passed" else 0.0
        for item in context.get("skill_matches", []):
            loaded = self._store.load_state(execution_id, sprint.name, task_name, item["skill_id"])
            state = loaded or SkillInjectionState(skill_id=item["skill_id"], scene=item["scene"])
            state.mark_reviewed()
            state.review_notes.append(f"review_status={review_status}")
            state.retro_metrics.update({"review_score": review_score, "review_status": review_status})
            self._store.save_state(execution_id, sprint.name, task_name, state)
            self._store.append_record(
                SkillExecutionRecord(
                    execution_id=execution_id,
                    sprint_name=sprint.name,
                    task_name=task_name,
                    scene=state.scene,
                    skill_id=state.skill_id,
                    state=state,
                    market_source=item.get("source", "openclaw"),
                    market_version=item.get("version", "latest"),
                )
            )
        trace = context.get("task_skill_trace")
        if trace:
            trace_obj = SkillTrace(
                execution_id=trace["execution_id"],
                sprint_name=trace["sprint_name"],
                task_name=trace["task_name"],
                scene=trace["scene"],
                matched_skills=list(trace.get("matched_skills", [])),
                injected_skills=list(trace.get("injected_skills", [])),
                review_checklist=[
                    SkillChecklistItem(**item) if isinstance(item, dict) else item
                    for item in trace.get("review_checklist", [])
                ],
                review_status=review_status,
                review_score=review_score,
                retro_metrics=dict(trace.get("retro_metrics", {})),
            )
            self._store.append_trace(trace_obj)
        context["review_status"] = review_status
        context["review_score"] = review_score

    async def before_review(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        review_checklists = context.setdefault("review_checklists", [])
        merged: list[SkillChecklistItem] = [
            item if isinstance(item, SkillChecklistItem) else SkillChecklistItem(**item) for item in review_checklists
        ]
        skill_items = context.get("skill_matches", [])
        for item in skill_items:
            merged.extend([SkillChecklistItem(**c) if isinstance(c, dict) else c for c in item.get("checklist", [])])
            merged.append(self._match_to_checklist(item))
        seen = set()
        deduped: list[SkillChecklistItem] = []
        for item in merged:
            key = (item.category, item.title, item.source)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        context["review_checklists"] = deduped

    async def after_retro(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        execution_id = context.get("execution_id", "default")
        task_name = sprint.goals[0] if sprint.goals else sprint.name
        for item in context.get("skill_matches", []):
            state = self._store.load_state(execution_id, sprint.name, task_name, item["skill_id"])
            state = state or SkillInjectionState(skill_id=item["skill_id"], scene=item["scene"])
            state.mark_retro()
            state.retro_metrics.update(
                {
                    "review_status": context.get("review_status", "unknown"),
                    "review_score": context.get("review_score", 0.0),
                    "skill_reason": item.get("reason", ""),
                }
            )
            self._store.save_state(execution_id, sprint.name, task_name, state)
            self._store.append_record(
                SkillExecutionRecord(
                    execution_id=execution_id,
                    sprint_name=sprint.name,
                    task_name=task_name,
                    scene=state.scene,
                    skill_id=state.skill_id,
                    state=state,
                    market_source=item.get("source", "openclaw"),
                    market_version=item.get("version", "latest"),
                )
            )
        self._orchestrator.after_retro(context)


__all__ = ["SkillLifecycleHook"]
