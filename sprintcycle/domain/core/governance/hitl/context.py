"""HITL 上下文构建与摘要。"""

from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, Optional

from .types import HitlCorrection, HitlReplayDirective


def build_hitl_context(*, gate: str, summary: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ctx = {"gate": gate, "summary": summary}
    if extra:
        ctx.update(extra)
    return ctx


def merge_correction_into_context(context: Dict[str, Any], correction: Optional[HitlCorrection]) -> Dict[str, Any]:
    merged = copy.deepcopy(context)
    if correction is None:
        return merged
    merged.setdefault("hitl", {})
    merged["hitl"]["correction"] = correction.to_dict()
    if correction.targets:
        merged["hitl"]["correction_targets"] = list(correction.targets)
    for patch in correction.patches:
        if not isinstance(patch, dict):
            continue
        path = patch.get("path")
        value = patch.get("value")
        if isinstance(path, str) and path:
            merged[path] = value
    merged["hitl"]["correction_applied"] = True
    return merged


def build_replay_context(
    context: Dict[str, Any],
    replay: Optional[HitlReplayDirective],
    *,
    reset_fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    merged = copy.deepcopy(context)
    if replay is None:
        return merged
    merged.setdefault("hitl", {})
    merged["hitl"]["replay"] = replay.to_dict()
    for field in list(reset_fields or []) + list(replay.reset_fields):
        merged.pop(field, None)
    if replay.target_gate:
        merged["hitl"]["replay_target_gate"] = replay.target_gate
    if replay.target_stage:
        merged["hitl"]["replay_target_stage"] = replay.target_stage
    return merged


def summarize_context_diff(before: Dict[str, Any], after: Dict[str, Any], max_items: int = 12) -> str:
    diffs = []
    keys = sorted(set(before.keys()) | set(after.keys()))
    for key in keys:
        if before.get(key) != after.get(key):
            diffs.append(key)
    if not diffs:
        return "no changes"
    if len(diffs) <= max_items:
        return ", ".join(diffs)
    return ", ".join(diffs[:max_items]) + f" ... (+{len(diffs) - max_items})"


def summarize_hitl_context(context: Dict[str, Any], max_len: int = 240) -> str:
    summary = str(context.get("summary") or context.get("reason") or context.get("gate") or "")
    if len(summary) <= max_len:
        return summary
    return summary[: max_len - 3] + "..."
