"""Mechanical dependency checker for SprintCycle layered governance.

This module performs a lightweight import scan and reports obvious layer
violations. It is intentionally simple and can later be wired into CI/lint.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .architecture_guard import DEPENDENCY_RULES, dependency_rules_payload
from .architecture_layers import LAYER_NAMES


@dataclass(frozen=True)
class ArchitectureViolation:
    path: str
    layer: str
    imported_module: str
    reason: str


@dataclass
class ArchitectureCheckResult:
    success: bool
    violations: List[ArchitectureViolation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "violations": [
                {
                    "path": v.path,
                    "layer": v.layer,
                    "imported_module": v.imported_module,
                    "reason": v.reason,
                }
                for v in self.violations
            ],
            "violation_count": len(self.violations),
            "rules": dependency_rules_payload(),
        }


def _infer_layer(path: Path) -> str | None:
    parts = path.parts
    for layer in LAYER_NAMES:
        if layer in parts:
            return layer
    return None


def _module_from_import(node: ast.AST) -> str:
    if isinstance(node, ast.Import):
        return ",".join(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return node.module or ""
    return ""


def check_architecture(root: str | Path) -> ArchitectureCheckResult:
    base = Path(root).resolve()
    violations: List[ArchitectureViolation] = []

    for py_file in base.rglob("*.py"):
        layer = _infer_layer(py_file.relative_to(base))
        if layer is None or layer not in DEPENDENCY_RULES:
            continue
        rule = DEPENDENCY_RULES[layer]
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = _module_from_import(node)
                for forbidden in rule.forbidden_dependencies:
                    if forbidden and forbidden in mod:
                        violations.append(
                            ArchitectureViolation(
                                path=str(py_file),
                                layer=layer,
                                imported_module=mod,
                                reason=f"forbidden dependency matched: {forbidden}",
                            )
                        )
                        break

    return ArchitectureCheckResult(success=not violations, violations=violations)
