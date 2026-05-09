"""Governance 侧的 SDD / release-plan 检查。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..quality_spec.reports.finding import Finding as QualityFinding
from ..quality_spec.spec.task_spec import TaskSpec


def _to_guard_finding(rule_id: str, severity: str, message: str, location: Dict[str, Any] | None = None):
    from .arch_guard.model import GuardFinding

    return GuardFinding(rule_id=rule_id, severity=severity, message=message, location=location or {})


def violations_from_release_plan_validator(release_plan: Any) -> List[Any]:
    findings: List[Any] = []
    try:
        task_specs = []
        if hasattr(release_plan, "to_task_specs"):
            task_specs = list(release_plan.to_task_specs() or [])
        for spec in task_specs:
            if not isinstance(spec, TaskSpec):
                continue
            try:
                spec.validate_minimal()
            except Exception as e:
                findings.append(
                    _to_guard_finding(
                        rule_id="planning:task_spec:minimal",
                        severity="error",
                        message=f"TaskSpec 校验失败: {e}",
                        location={"task_id": getattr(spec, "id", "")},
                    )
                )
    except Exception as e:
        logger.warning("release plan validator 检查失败: {}", e)
        findings.append(
            _to_guard_finding(
                rule_id="planning:release_plan_validator",
                severity="warning",
                message=str(e),
                location={},
            )
        )
    return findings


def violations_for_task_spec_refs(root: Path, release_plan: Any) -> List[Any]:
    findings: List[Any] = []
    try:
        task_specs = []
        if hasattr(release_plan, "to_task_specs"):
            task_specs = list(release_plan.to_task_specs() or [])
        for spec in task_specs:
            if not isinstance(spec, TaskSpec):
                continue
            for ref in getattr(spec, "spec_refs", []) or []:
                candidate = (root / ref).resolve() if not Path(ref).is_absolute() else Path(ref)
                if not candidate.exists():
                    findings.append(
                        _to_guard_finding(
                            rule_id="planning:task_spec_ref_missing",
                            severity="warning",
                            message=f"TaskSpec spec_ref 不存在: {ref}",
                            location={"ref": ref, "task_id": spec.id},
                        )
                    )
    except Exception as e:
        logger.warning("task spec refs 检查失败: {}", e)
        findings.append(
            _to_guard_finding(
                rule_id="planning:task_spec_ref_error",
                severity="warning",
                message=str(e),
                location={},
            )
        )
    return findings


def violations_acceptance_files(root: Path, glob_pattern: str) -> List[Any]:
    from .arch_guard.model import GuardFinding

    findings: List[Any] = []
    for p in root.glob(glob_pattern):
        if p.is_file():
            continue
    if not any(root.glob(glob_pattern)):
        findings.append(
            GuardFinding(
                rule_id="planning:acceptance_glob",
                severity="warning",
                message=f"acceptance_glob 未匹配任何文件: {glob_pattern}",
                location={"glob": glob_pattern},
            )
        )
    return findings


def violations_spec_marker_in_files(root: Path, glob_pattern: str, marker: str) -> List[Any]:
    from .arch_guard.model import GuardFinding

    findings: List[Any] = []
    matches = list(root.glob(glob_pattern))
    if not matches:
        return findings
    for p in matches:
        if p.is_file() and marker not in p.read_text(encoding="utf-8", errors="replace"):
            findings.append(
                GuardFinding(
                    rule_id="planning:spec_marker_missing",
                    severity="warning",
                    message=f"文件缺少 spec marker: {p.name}",
                    location={"path": str(p), "marker": marker},
                )
            )
    return findings
