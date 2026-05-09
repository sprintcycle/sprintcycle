"""Compose 轻量门禁检查。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .arch_guard.model import GuardFinding


def check_compose_hints(path: Path, text: str) -> List[GuardFinding]:
    findings: List[GuardFinding] = []
    if "image:" in text and "build:" not in text:
        findings.append(
            GuardFinding(
                rule_id="compose:image_without_build",
                severity="warning",
                message=f"{path.name}: 使用 image 但未声明 build，确认是否符合发布意图",
                location={"path": str(path)},
            )
        )
    return findings


def check_compose_supply_chain_hints(path: Path, services: Dict[str, Any]) -> List[GuardFinding]:
    findings: List[GuardFinding] = []
    if not services:
        return findings
    for name, cfg in services.items():
        if isinstance(cfg, dict) and "image" in cfg and "build" not in cfg:
            findings.append(
                GuardFinding(
                    rule_id="compose:supply_chain:image_only",
                    severity="warning",
                    message=f"服务 {name} 仅使用 image，建议确认供应链来源",
                    location={"path": str(path), "service": name},
                )
            )
    return findings
