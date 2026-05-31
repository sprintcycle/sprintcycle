"""Lifecycle evidence schema definitions for SprintCycle.

This module provides the evidence schema constants and validation utilities
previously part of LifecycleContract.

**Evidence Schema:**
- STAGE_EVIDENCE_SCHEMA: Required evidence keys per stage
- STAGE_EVIDENCE_TRUTHY_KEYS: Keys that must be truthy
- STAGE_EVIDENCE_KEYS: All evidence stage keys
- CANONICAL_EVIDENCE_KEYS: Canonical name mappings
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .state_machine import LIFECYCLE_STAGES, FAILURE_KIND_BY_STAGE


# =============================================================================
# Evidence Schema Definitions
# =============================================================================

STAGE_EVIDENCE_SCHEMA: Dict[str, tuple[str, ...]] = {
    "normalized": ("normalized",),
    "plan": ("objective", "present"),
    "prepare": ("ready", "checks", "blockers", "present"),
    "decompose": ("subtasks", "present"),
    "execute": ("trace", "present"),
    "observe": ("trace", "diagnostics", "present"),
    "diagnose": ("root_causes", "repair_ready", "confidence", "recommendations", "present"),
    "repair": ("attempted", "closed_loop", "verify_result", "present"),
    "verify": ("closed_loop", "verify_result", "present"),
    "deliver": ("outputs", "runtime_linkage", "present"),
    "runtime": ("linked", "healthy", "present"),
    "governance": ("approved", "present"),
    "promotion": ("evidence", "completion_score"),
    "evolution": ("versioned", "version_id", "present"),
}


STAGE_EVIDENCE_TRUTHY_KEYS: Dict[str, tuple[str, ...]] = {
    "normalized": ("normalized",),
    "prepare": ("ready", "present"),
    "decompose": ("present",),
    "execute": ("present",),
    "observe": ("present",),
    "diagnose": ("present",),
    "repair": ("attempted", "closed_loop", "present"),
    "verify": ("closed_loop", "present"),
    "deliver": ("present",),
    "runtime": ("linked", "healthy", "present"),
    "governance": ("approved", "present"),
    "promotion": ("evidence", "completion_score"),
    "evolution": ("versioned", "version_id", "present"),
}


STAGE_EVIDENCE_KEYS: tuple[str, ...] = (
    "normalized",
    "plan",
    "prepare",
    "decompose",
    "execute",
    "observe",
    "diagnose",
    "repair",
    "verify",
    "deliver",
    "runtime",
    "governance",
    "promotion",
    "evolution",
)


CANONICAL_EVIDENCE_KEYS: Dict[str, str] = {
    "governing": "governance",
    "governance": "governance",
}


TERMINAL_STATUSES: tuple[str, ...] = ("success", "failed", "cancelled", "promoted")
REQUIRED_EVIDENCE_SECTIONS: tuple[str, ...] = (
    "contract",
    "stages",
    "runtime",
    "governance",
    "promotion",
    "evolution",
)
REQUIRED_STAGE_SEQUENCE: tuple[str, ...] = (
    "normalized",
    "plan",
    "prepare",
    "decompose",
    "execute",
    "observe",
    "diagnose",
    "repair",
    "verify",
    "deliver",
    "runtime",
    "governance",
    "promotion",
    "evolution",
)
RECOVERY_STAGE_TARGETS: Dict[str, str] = {
    "running": "repair",
    "observing": "repair",
    "diagnosed": "repair",
    "repairing": "verify",
    "verifying": "observe",
    "delivering": "repair",
    "runtime_linked": "repair",
    "governing": "repair",
    "promotion_ready": "repair",
    "failed": "repair",
}


# =============================================================================
# Evidence Utilities
# =============================================================================

def ensure_lifecycle_evidence(evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = dict(evidence or {})
    payload.setdefault("contract", {})
    payload.setdefault("stages", {})
    payload.setdefault("runtime", {})
    payload.setdefault("governance", {})
    payload.setdefault("promotion", {})
    payload.setdefault("evolution", {})
    payload.setdefault("suggestion", {})
    payload.setdefault("trace", {})
    payload.setdefault("diagnostics", {})
    payload.setdefault("recovery", {})
    stages = payload.setdefault("stages", {})
    for stage in STAGE_EVIDENCE_KEYS:
        canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
        stages.setdefault(canonical_stage, {})
    if "governing" in stages and "governance" not in stages:
        stages["governance"] = dict(stages.get("governing") or {})
    return payload


def next_stage(stage: str) -> str:
    if stage not in LIFECYCLE_STAGES:
        return ""
    idx = LIFECYCLE_STAGES.index(stage)
    return LIFECYCLE_STAGES[idx + 1] if idx + 1 < len(LIFECYCLE_STAGES) else ""


def normalize_lifecycle_metadata(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = dict(metadata or {})
    meta.setdefault("task_type", meta.get("task_type") or "project_optimization")
    meta.setdefault("intent", meta.get("intent") or meta.get("task_id") or meta.get("name") or "")
    meta.setdefault("source", meta.get("source") or "web")
    meta.setdefault("stability_contract", "web_end_to_end")
    return meta


def _has_truthy_path(payload: Dict[str, Any], path: str) -> bool:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return bool(current)


def validate_lifecycle_evidence(contract: Dict[str, Any]) -> List[str]:
    payload = dict(contract or {})
    evidence = ensure_lifecycle_evidence(payload.get("evidence"))
    errors: List[str] = []
    stages = dict(evidence.get("stages") or {}) if isinstance(evidence.get("stages"), dict) else {}
    for stage, required_keys in STAGE_EVIDENCE_SCHEMA.items():
        canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
        stage_payload = dict(stages.get(canonical_stage) or {}) if canonical_stage in stages else {}
        if canonical_stage in {"governance", "promotion", "evolution", "runtime"}:
            stage_payload = dict(evidence.get(canonical_stage) or {})
        if not isinstance(stage_payload, dict):
            errors.append(f"evidence.{canonical_stage} must be a mapping")
            continue
        missing = [key for key in required_keys if key not in stage_payload]
        if missing:
            errors.append(f"evidence.{canonical_stage} missing keys: {', '.join(missing)}")
            continue
        truthy_required = STAGE_EVIDENCE_TRUTHY_KEYS.get(stage, ())
        for key in truthy_required:
            if key in stage_payload and not stage_payload.get(key):
                errors.append(f"evidence.{canonical_stage}.{key} must be truthy")
    required_stage_names = [stage for stage in REQUIRED_STAGE_SEQUENCE if stage not in {"governance", "governing"}]
    for stage in required_stage_names:
        canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
        if canonical_stage in {"runtime", "governance", "promotion", "evolution"}:
            if not _has_truthy_path(evidence, canonical_stage):
                errors.append(f"missing evidence section: {canonical_stage}")
            continue
        if not _has_truthy_path(stages, canonical_stage):
            errors.append(f"missing stage evidence: {canonical_stage}")
    contract_section = dict(evidence.get("contract") or {})
    if not contract_section.get("normalized"):
        errors.append("evidence.contract.normalized must be truthy")
    if not evidence.get("runtime"):
        errors.append("evidence.runtime must be present")
    if not evidence.get("promotion"):
        errors.append("evidence.promotion must be present")
    if not evidence.get("evolution"):
        errors.append("evidence.evolution must be present")
    return errors


__all__ = [
    "STAGE_EVIDENCE_SCHEMA",
    "STAGE_EVIDENCE_TRUTHY_KEYS",
    "FAILURE_KIND_BY_STAGE",
    "STAGE_EVIDENCE_KEYS",
    "CANONICAL_EVIDENCE_KEYS",
    "TERMINAL_STATUSES",
    "REQUIRED_EVIDENCE_SECTIONS",
    "REQUIRED_STAGE_SEQUENCE",
    "RECOVERY_STAGE_TARGETS",
    "ensure_lifecycle_evidence",
    "next_stage",
    "normalize_lifecycle_metadata",
    "validate_lifecycle_evidence",
]