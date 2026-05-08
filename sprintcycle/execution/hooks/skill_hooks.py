"""Skill 生命周期钩子实现。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...release_plan.models import ReleasePlan, SprintDefinition
from ..skill_models import SkillArtifact, SkillExecutionRecord, SkillInjectionState, TaskSkillTrace
from ..skill_store import SkillStore
from ..skills import SkillOrchestrator
from ..sprint_types import SprintResult
from .sprint_hooks import SprintLifecycleHooks


class SkillLifecycleHook(SprintLifecycleHooks):
    def __init__(self, orchestrator: SkillOrchestrator, store: Optional[SkillStore] = None) -> None:
        self._orchestrator = orchestrator
        self._store = store or SkillStore()

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        task_text = sprint.goals[0] if sprint.goals else sprint.name
        matches = self._orchestrator.after_plan(task_text, context)
        context["skill_matches"] = [m.__dict__ for m in matches]
        execution_id = context.get("execution_id", "default")
        for m in matches:
            state = SkillInjectionState(skill_id=m.skill_id, scene=m.scene)
            state.injection_source = m.path
            state.review_checklist = list(m.checklist)
            state.prompt_fragments = [f"skill:{m.skill_id}", f"version:{m.version}", f"source:{m.market_source}"]
            state.mark_injected()
            self._store.save_state(execution_id, sprint.name, task_text, state)
            artifact = self._store.get_latest_artifact(m.skill_id)
            if artifact is None:
                self._store.upsert_artifact(
                    SkillArtifact(
                        skill_id=m.skill_id,
                        version=m.version,
                        path=m.path,
                        content_hash="",
                        source=m.market_source,
                        status="injected",
                    )
                )
            else:
                artifact.status = "injected"
                artifact.path = m.path
                artifact.version = m.version
                artifact.source = m.market_source
                self._store.upsert_artifact(artifact)
        context["task_skill_trace"] = TaskSkillTrace(
            execution_id=execution_id,
            sprint_name=sprint.name,
            task_name=task_text,
            scene=context.get("skill_scene", "general"),
            matched_skills=[m.skill_id for m in matches],
            injected_skills=[m.skill_id for m in matches],
            review_checklist=[item for m in matches for item in m.checklist],
            retro_metrics={"market_source": "openclaw"},
        ).__dict__

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
            self._store.append_record(SkillExecutionRecord(
                execution_id=execution_id,
                sprint_name=sprint.name,
                task_name=task_name,
                scene=state.scene,
                skill_id=state.skill_id,
                state=state,
                market_source=item.get("market_source", "openclaw"),
                market_version=item.get("version", "latest"),
            ))
        trace = context.get("task_skill_trace")
        if trace:
            trace["review_status"] = review_status
            trace["review_score"] = review_score
            self._store.append_trace(TaskSkillTrace(**trace))
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
        merged = list(review_checklists)
        skill_items = context.get("skill_matches", [])
        for item in skill_items:
            merged.extend(item.get("checklist", []))
            merged.append({"category": "skill", "title": f"{item['skill_id']} 相关审查", "required": True, "source": item["skill_id"]})
        # 去重（保留顺序）
        seen = set()
        deduped = []
        for item in merged:
            key = str(item)
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
            state.retro_metrics.update({
                "review_status": context.get("review_status", "unknown"),
                "review_score": context.get("review_score", 0.0),
                "skill_reason": item.get("reason", ""),
            })
            self._store.save_state(execution_id, sprint.name, task_name, state)
            self._store.append_record(SkillExecutionRecord(
                execution_id=execution_id,
                sprint_name=sprint.name,
                task_name=task_name,
                scene=state.scene,
                skill_id=state.skill_id,
                state=state,
                market_source=item.get("market_source", "openclaw"),
                market_version=item.get("version", "latest"),
            ))
        self._orchestrator.after_retro(context)


__all__ = ["SkillLifecycleHook"]
