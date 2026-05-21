"""治理层 YAML 声明式检查与 argv 运行器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def load_governance_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml

        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def checks_for_gate(data: Dict[str, Any], gate: str) -> List[Dict[str, Any]]:
    return list((data or {}).get(gate) or [])


def filter_argv_items_by_governance_sources(
    items: List[Dict[str, Any]], cfg: Any, root: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Filter argv items based on governance source toggles (browser/visual)."""
    browser = getattr(cfg, "governance_review_browser_e2e", False)
    visual = getattr(cfg, "governance_review_visual", False)
    filtered = []
    for item in items:
        tags = item.get("tags") or []
        if "browser" in tags and not browser:
            continue
        if "visual" in tags and not visual:
            continue
        filtered.append(item)
    return filtered


def run_argv_item(item: Dict[str, Any], root: Path, gate: str, extra_env: Optional[Dict[str, str]] = None):
    from .arch_guard.model import GuardFinding

    findings = []
    argv = item.get("argv") or []
    if not argv:
        return findings
    expect_code = item.get("expect_code", 0)
    severity = item.get("severity", "error")
    item_id = item.get("id", "unknown")
    try:
        import os
        import subprocess

        env = dict(os.environ)
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, timeout=60, env=env)
        if proc.returncode != expect_code:
            findings.append(
                GuardFinding(
                    rule_id=f"{gate}:{item_id}",
                    severity=severity,
                    message=f"{item_id} exited {proc.returncode}, expected {expect_code}: {proc.stderr.strip() or proc.stdout.strip() or 'no output'}",
                    location={"argv": argv},
                )
            )
    except Exception as e:
        findings.append(
            GuardFinding(
                rule_id=f"{gate}:{item_id}",
                severity=severity,
                message=f"{item_id} failed: {e}",
                location={"argv": argv},
            )
        )
    return findings


def run_argv_checks(items: List[Dict[str, Any]], root: Path, gate: str):
    findings = []
    for item in items:
        if item.get("enabled") is False:
            continue
        findings.extend(run_argv_item(item, root, gate))
    return findings
