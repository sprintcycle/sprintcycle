from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .model import GuardFinding
from ...release_plan.models import ReleasePlan


def check_release_plan(release_plan: ReleasePlan) -> List[GuardFinding]:
    out: List[GuardFinding] = []

    if not getattr(release_plan, "sprints", None):
        out.append(
            GuardFinding(
                rule_id="planning:release_plan_empty",
                severity="error",
                message="ReleasePlan 不能为空",
                location={},
            )
        )
        return out

    sprint_names = []
    for i, sprint in enumerate(release_plan.sprints):
        name = getattr(sprint, "name", "") or ""
        if not name.strip():
            out.append(
                GovernanceViolation(
                    rule_id="planning:sprint_name_empty",
                    severity="error",
                    message=f"Sprint #{i + 1} 名称为空",
                    location={"sprint_index": i},
                )
            )
        sprint_names.append(name)

    if len(set(sprint_names)) != len(sprint_names):
        out.append(
            GovernanceViolation(
                rule_id="planning:sprint_name_duplicate",
                severity="error",
                message="ReleasePlan 中存在重复的 Sprint 名称",
                location={"sprint_names": sprint_names},
            )
        )

    return out


def check_spec_refs(root: Path, release_plan: ReleasePlan) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    for si, sprint in enumerate(getattr(release_plan, "sprints", [])):
        for ti, task in enumerate(getattr(sprint, "tasks", [])):
            ref = getattr(task, "spec_ref", None)
            if not ref:
                continue

            p = Path(str(ref).strip())
            if p.is_absolute():
                out.append(
                    GovernanceViolation(
                        rule_id="planning:spec_ref_absolute",
                        severity="warning",
                        message=f"Sprint「{sprint.name}」任务 #{ti + 1} 的 spec_ref 应为相对路径: {ref}",
                        location={"sprint": sprint.name, "task_index": ti, "spec_ref": ref},
                    )
                )
                continue

            full = (root / p).resolve()
            if not full.exists():
                out.append(
                    GovernanceViolation(
                        rule_id="planning:spec_ref_missing",
                        severity="warning",
                        message=f"Sprint「{sprint.name}」任务 #{ti + 1} 的 spec_ref 文件不存在: {ref}",
                        location={"sprint": sprint.name, "task_index": ti, "path": str(full)},
                    )
                )

    return out


def check_governance_marker(root: Path, glob_pat: str, marker: str) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if not marker.strip():
        return out

    for path in root.glob(glob_pat):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if marker not in text:
            out.append(
                GovernanceViolation(
                    rule_id="planning:marker_missing",
                    severity="warning",
                    message=f"文件缺少约定标记 {marker!r}: {path.relative_to(root)}",
                    location={"file": str(path)},
                )
            )

    return out


def check_hook_context_usage(context: Optional[Dict[str, Any]]) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if context is None:
        return out
    if not isinstance(context, dict):
        out.append(
            GovernanceViolation(
                rule_id="review:hook_context_invalid",
                severity="warning",
                message="治理 context 应为 dict",
                location={"type": type(context).__name__},
            )
        )
        return out
    if "project_path" not in context:
        out.append(
            GovernanceViolation(
                rule_id="review:hook_context_project_path_missing",
                severity="info",
                message="context 中未显式携带 project_path，治理将回退到默认项目根",
                location={},
            )
        )
    return out


def check_report_shape(report_data: Any) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if report_data is None:
        return out
    if not isinstance(report_data, dict):
        out.append(
            GovernanceViolation(
                rule_id="review:report_shape_invalid",
                severity="warning",
                message="治理报告数据应为 dict",
                location={"type": type(report_data).__name__},
            )
        )
        return out
    if "violations" not in report_data:
        out.append(
            GovernanceViolation(
                rule_id="review:report_violations_missing",
                severity="warning",
                message="治理报告缺少 violations 字段",
                location={},
            )
        )
    return out


def check_event_shape(event_data: Any) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if event_data is None:
        return out
    if not isinstance(event_data, dict):
        out.append(
            GovernanceViolation(
                rule_id="review:event_shape_invalid",
                severity="warning",
                message="事件数据应为 dict",
                location={"type": type(event_data).__name__},
            )
        )
        return out
    if "type" not in event_data:
        out.append(
            GovernanceViolation(
                rule_id="review:event_type_missing",
                severity="warning",
                message="事件缺少 type 字段",
                location={},
            )
        )
    return out


def check_extension_point_usage(context: Optional[Dict[str, Any]]) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if not isinstance(context, dict):
        return out
    if context.get("governance_extension_bypass"):
        out.append(
            GovernanceViolation(
                rule_id="review:extension_point_bypass",
                severity="error",
                message="检测到治理扩展点旁路标记，禁止绕过 ArchGuardModule 直接接入内部实现",
                location={},
            )
        )
    return out


def check_evolution_mainline(context: Optional[Dict[str, Any]]) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if not isinstance(context, dict):
        return out
    if not context.get("evolution_mainline"):
        out.append(
            GovernanceViolation(
                rule_id="review:evolution_mainline_missing",
                severity="info",
                message="未显式声明本次变更的演进主线",
                location={},
            )
        )
    return out


def check_compatibility_flags(context: Optional[Dict[str, Any]]) -> List[GuardFinding]:
    out: List[GuardFinding] = []
    if not isinstance(context, dict):
        return out
    if context.get("breaking_change") and not context.get("compatibility_plan"):
        out.append(
            GovernanceViolation(
                rule_id="review:compatibility_plan_missing",
                severity="warning",
                message="检测到破坏性变更，但未提供兼容性方案",
                location={},
            )
        )
    return out
