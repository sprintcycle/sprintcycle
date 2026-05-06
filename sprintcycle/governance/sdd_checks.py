"""SDD：spec 标记、任务 ``spec_ref``、验收文件、执行计划结构校验（Planning gate 扩展）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import yaml

from ..release_plan.models import ReleasePlan
from ..release_plan.validator import ReleasePlanValidator
from .report import GovernanceViolation


def violations_from_release_plan_validator(release_plan: ReleasePlan) -> List[GovernanceViolation]:
    """将 ``ReleasePlanValidator`` 结果转为治理违规（默认 severity=warning，便于观察模式）。"""
    vr = ReleasePlanValidator().validate(release_plan)
    out: List[GovernanceViolation] = []
    for msg in vr.errors:
        out.append(
            GovernanceViolation(
                rule_id="planning:release_plan_validator_error",
                severity="error",
                message=msg,
                location={"source": "ReleasePlanValidator"},
            )
        )
    for msg in vr.warnings:
        out.append(
            GovernanceViolation(
                rule_id="planning:release_plan_validator_warning",
                severity="warning",
                message=msg,
                location={"source": "ReleasePlanValidator"},
            )
        )
    return out


def violations_for_task_spec_refs(root: Path, release_plan: ReleasePlan) -> List[GovernanceViolation]:
    """每条 Backlog 项可选 ``spec_ref``：须为项目根下存在的相对路径文件。"""
    out: List[GovernanceViolation] = []
    for si, sp in enumerate(release_plan.sprints):
        for ti, task in enumerate(sp.tasks):
            ref = getattr(task, "spec_ref", None)
            if not ref or not str(ref).strip():
                continue
            p = Path(str(ref).strip())
            if p.is_absolute():
                out.append(
                    GovernanceViolation(
                        rule_id="planning:spec_ref_absolute",
                        severity="warning",
                        message=f"Sprint「{sp.name}」任务 #{ti + 1}：spec_ref 应为相对项目根的路径，收到绝对路径: {ref}",
                        location={"sprint": sp.name, "task_index": ti},
                    )
                )
                continue
            full = (root / p).resolve()
            if not full.is_file():
                out.append(
                    GovernanceViolation(
                        rule_id="planning:spec_ref_missing",
                        severity="warning",
                        message=f"Sprint「{sp.name}」任务 #{ti + 1}：spec_ref 文件不存在: {ref}",
                        location={"sprint": sp.name, "task_index": ti, "path": str(full)},
                    )
                )
    return out


def violations_spec_marker_in_files(
    root: Path,
    glob_pat: str,
    marker: str,
) -> List[GovernanceViolation]:
    """``governance_spec_marker`` 非空时：每个 spec_glob 匹配文件须包含该子串。"""
    out: List[GovernanceViolation] = []
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
                    rule_id="planning:spec_marker_missing",
                    severity="warning",
                    message=f"规范文件缺少约定标记 {marker!r}: {path.relative_to(root)}",
                    location={"file": str(path)},
                )
            )
    return out


def violations_acceptance_files(root: Path, acceptance_glob: str) -> List[GovernanceViolation]:
    """
    ``governance_acceptance_glob`` 非空时：须至少匹配到一个 YAML 文件，且可解析为 dict
    （可选键 ``acceptance`` 为列表即视为有效 SDD 片段）。
    """
    out: List[GovernanceViolation] = []
    g = (acceptance_glob or "").strip()
    if not g:
        return out
    matches = [p for p in root.glob(g) if p.is_file()]
    if not matches:
        out.append(
            GovernanceViolation(
                rule_id="planning:acceptance_glob_empty",
                severity="warning",
                message=f"acceptance_glob 未匹配任何文件: {g}",
                location={"glob": g},
            )
        )
        return out
    for path in matches:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            data = yaml.safe_load(raw)
        except Exception as e:
            out.append(
                GovernanceViolation(
                    rule_id="planning:acceptance_yaml_invalid",
                    severity="warning",
                    message=f"验收 YAML 解析失败 {path.relative_to(root)}: {e}",
                    location={"file": str(path)},
                )
            )
            continue
        if data is not None and not isinstance(data, dict):
            out.append(
                GovernanceViolation(
                    rule_id="planning:acceptance_yaml_shape",
                    severity="warning",
                    message=f"验收文件应为 YAML 映射: {path.relative_to(root)}",
                    location={"file": str(path)},
                )
            )
    return out
