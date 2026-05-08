"""执行规划器。

把 SprintExecutor / SprintOrchestrator 中的 context 拼装、Sprint 失败决策、
以及 Sprint 后评估拆成可替换组件。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .context import SprintExecutionContext, TaskExecutionContext
from .policies import SprintFeedbackPolicy, SprintRetryPolicy, TaskRetryPolicy
from ..release_plan.models import ReleasePlan, SprintBacklogItem, SprintDefinition


class TaskContextBuilder:
    def build(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        raw_context: Dict[str, Any],
    ) -> TaskExecutionContext:
        deps = dict(raw_context.get("dependencies") or {})
        codebase_context: Dict[str, Any] = {
            "project_path": str(raw_context.get("project_path", ".")),
        }
        rp_ctx = raw_context.get("release_plan")
        if rp_ctx is not None:
            codebase_context["release_plan"] = rp_ctx
            meta = getattr(rp_ctx, "metadata", None) or {}
            refs = meta.get("reference_project_paths")
            if refs:
                codebase_context["reference_project_paths"] = refs
            eff = meta.get("effective_write_policy")
            if eff:
                codebase_context["effective_write_policy"] = eff
            wp = meta.get("write_policy")
            if wp:
                codebase_context["write_policy"] = wp
        for key in ("architecture_design", "modules", "tech_stack", "issues", "code"):
            if key in raw_context:
                codebase_context[key] = raw_context[key]
        if raw_context.get("task_guidance"):
            codebase_context["task_guidance"] = raw_context["task_guidance"]
        if raw_context.get("verify_fix_notes"):
            vn = str(raw_context["verify_fix_notes"]).strip()
            if vn:
                prev = (codebase_context.get("task_guidance") or "").strip()
                extra = "\n\n[Coder 验证-修复 — 上一轮失败]\n" + vn
                codebase_context["task_guidance"] = (prev + extra).strip() if prev else extra.strip()
        if raw_context.get("release_plan_overlay_yaml"):
            codebase_context["release_plan_overlay"] = raw_context["release_plan_overlay_yaml"]
        locked_engine = str(
            raw_context.get("_sprint_coding_engine") or raw_context.get("coding_engine", "aider")
        )
        return TaskExecutionContext(
            project_path=str(raw_context.get("project_path", ".")),
            sprint_name=str(raw_context.get("sprint_name", sprint_name)),
            sprint_index=int(raw_context.get("sprint_index", 0)),
            coding_engine="cursor" if locked_engine == "aider" else locked_engine,
            quality_level=str(raw_context.get("quality_level", "L1")),
            release_plan=rp_ctx,
            release_plan_name=str(raw_context.get("release_plan_name", "")),
            release_plan_id=str(raw_context.get("release_plan_id", "")),
            architecture_design=raw_context.get("architecture_design"),
            dependencies=deps,
            codebase_context=codebase_context,
            task_guidance=str(raw_context.get("task_guidance", "")),
            verify_fix_notes=str(raw_context.get("verify_fix_notes", "")),
            improvement_suggestions=list(raw_context.get("improvement_suggestions") or []),
            retry_from_failure=bool(raw_context.get("retry_from_failure", False)),
            metadata={
                "coding_engine": locked_engine,
                "quality_level": raw_context.get("quality_level", "L1"),
                "constraints": getattr(task, "constraints", []) or [],
            },
            config={"cache_llm_codegen": bool(raw_context.get("cache_llm_codegen", True))},
        )


class SprintContextBuilder:
    def build(
        self,
        release_plan: ReleasePlan,
        runtime_config: Any,
        project_root: str,
    ) -> SprintExecutionContext:
        meta = getattr(release_plan, "metadata", None) or {}
        return SprintExecutionContext(
            project_path=project_root,
            release_plan=release_plan,
            release_plan_name=release_plan.project.name,
            release_plan_id=str(meta.get("id", "")),
            coding_engine=getattr(runtime_config, "coding_engine", "aider"),
            quality_level=runtime_config.effective_quality_level(),
        )


@dataclass
class SprintLoopResultPolicy:
    sprint_retry_policy: SprintRetryPolicy
    sprint_feedback_policy: SprintFeedbackPolicy

    def should_retry(self, sprint: SprintDefinition) -> bool:
        return self.sprint_retry_policy.should_retry(sprint).should_retry

    def build_retry_context(self, decision: Dict[str, Any], feedback: Any) -> Dict[str, Any]:
        return self.sprint_feedback_policy.build_context(decision, feedback)


__all__ = ["TaskContextBuilder", "SprintContextBuilder", "SprintLoopResultPolicy"]
