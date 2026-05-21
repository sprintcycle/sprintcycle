"""治理层 YAML 声明式检查与 argv 运行器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def load_governance_yaml(root: Path) -> Dict[str, Any]:
    return {}


def checks_for_gate(data: Dict[str, Any], gate: str) -> List[Dict[str, Any]]:
    return list((data or {}).get(gate) or [])


def filter_argv_items_by_governance_sources(items: List[Dict[str, Any]], cfg: Any, root: Optional[Path] = None) -> List[Dict[str, Any]]:
    return list(items)


def run_argv_item(item: Dict[str, Any], root: Path, gate: str, extra_env: Optional[Dict[str, str]] = None):
    return []


def run_argv_checks(items: List[Dict[str, Any]], root: Path, gate: str):
    findings = []
    for item in items:
        findings.extend(run_argv_item(item, root, gate))
    return findings
