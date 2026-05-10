"""Dependency guardrails for SprintCycle directory governance.

This module captures the allowed layer-to-layer dependency directions so the
architecture can be checked mechanically later.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .architecture_layers import LAYER_NAMES


@dataclass(frozen=True)
class DependencyRule:
    layer: str
    allowed_dependencies: List[str]
    forbidden_dependencies: List[str]


DEPENDENCY_RULES: Dict[str, DependencyRule] = {
    "execution": DependencyRule(
        layer="execution",
        allowed_dependencies=["observability", "governance"],
        forbidden_dependencies=["dashboard", "deployment"],
    ),
    "governance": DependencyRule(
        layer="governance",
        allowed_dependencies=["execution", "observability", "fitness"],
        forbidden_dependencies=["dashboard", "deployment"],
    ),
    "observability": DependencyRule(
        layer="observability",
        allowed_dependencies=["execution"],
        forbidden_dependencies=["dashboard", "deployment", "governance"],
    ),
    "fitness": DependencyRule(
        layer="fitness",
        allowed_dependencies=["observability", "execution"],
        forbidden_dependencies=["dashboard", "deployment", "governance"],
    ),
    "dashboard": DependencyRule(
        layer="dashboard",
        allowed_dependencies=["api", "governance", "observability", "fitness", "deployment"],
        forbidden_dependencies=["execution_impl", "state_mutation"],
    ),
    "deployment": DependencyRule(
        layer="deployment",
        allowed_dependencies=["execution", "observability"],
        forbidden_dependencies=["dashboard", "governance"],
    ),
}


def get_dependency_rule(layer: str) -> DependencyRule:
    key = (layer or "").strip().lower()
    if key not in DEPENDENCY_RULES:
        raise KeyError(f"Unknown layer: {layer}")
    return DEPENDENCY_RULES[key]


def dependency_rules_payload() -> Dict[str, Dict[str, object]]:
    return {
        name: {
            "allowed_dependencies": list(rule.allowed_dependencies),
            "forbidden_dependencies": list(rule.forbidden_dependencies),
        }
        for name, rule in DEPENDENCY_RULES.items()
    }
