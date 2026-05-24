"""Layer contract for SprintCycle directory governance.

This module is the executable source of truth for the six-layer boundary design.
It intentionally stays small and data-driven so that other modules can import
these rules without duplicating architectural policy strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class LayerContract:
    name: str
    purpose: str
    allowed: Tuple[str, ...]
    forbidden: Tuple[str, ...]
    responsibility_ceiling: str


LAYER_CONTRACTS: Dict[str, LayerContract] = {
    "execution": LayerContract(
        name="execution",
        purpose="执行编排层 / 核心内核",
        allowed=(
            "task lifecycle",
            "state machine",
            "stage/step progression",
            "resume/replay/retry",
            "execution events",
            "release plan expansion",
        ),
        forbidden=(
            "ui rendering",
            "approval decisions",
            "fitness scoring implementation",
            "log visualization",
            "deployment policy decisions",
        ),
        responsibility_ceiling="只做执行与状态推进，不做裁决与展示。",
    ),
    "governance": LayerContract(
        name="governance",
        purpose="治理层 / 门控外环",
        allowed=(
            "suggestion approval",
            "risk control",
            "HITL coordination",
            "policy gates",
            "admission control",
            "governance reports",
        ),
        forbidden=(
            "direct sandbox execution",
            "direct code mutation",
            "state machine mutation",
            "ui rendering",
            "fitness scoring implementation",
        ),
        responsibility_ceiling="只做能不能过，不做怎么跑。",
    ),
    "observability": LayerContract(
        name="observability",
        purpose="可观测层 / 证据层",
        allowed=(
            "trace recording",
            "event recording",
            "log/artifact projection",
            "replay data construction",
            "evidence chain organization",
        ),
        forbidden=(
            "approval decisions",
            "execution control",
            "repair execution",
            "governance rulings",
            "state mutation",
        ),
        responsibility_ceiling="只保留事实，不参与裁决。",
    ),
    "fitness": LayerContract(
        name="fitness",
        purpose="适应度 / 评估层",
        allowed=(
            "quality scoring",
            "threshold checks",
            "multi-dimensional evaluation",
            "recommendation generation",
        ),
        forbidden=(
            "state mutation",
            "repair execution",
            "ui rendering",
            "governance rulings",
            "deployment actions",
        ),
        responsibility_ceiling="只打分，不执行业务动作。",
    ),
    "dashboard": LayerContract(
        name="dashboard",
        purpose="控制台层 / 投影与交互层",
        allowed=(
            "display",
            "interaction",
            "API adaptation",
            "SSE projection",
            "user command forwarding",
        ),
        forbidden=(
            "execution logic",
            "approval logic",
            "scoring logic",
            "state progression",
            "deployment execution",
        ),
        responsibility_ceiling="只做看和点，不做判断。",
    ),
    "deployment": LayerContract(
        name="deployment",
        purpose="自动部署层 / 交付出口",
        allowed=(
            "build",
            "run",
            "rollback",
            "deployment record keeping",
            "runtime registry updates",
        ),
        forbidden=(
            "governance decisions",
            "ui rendering",
            "fitness judgments",
            "state machine progression",
        ),
        responsibility_ceiling="交付能力独立，便于替换。",
    ),
}


def get_layer_contract(layer: str) -> LayerContract:
    key = (layer or "").strip().lower()
    if key not in LAYER_CONTRACTS:
        raise KeyError(f"Unknown layer: {layer}")
    return LAYER_CONTRACTS[key]


def layer_rules_payload() -> Dict[str, Dict[str, object]]:
    return {
        name: {
            "purpose": contract.purpose,
            "allowed": list(contract.allowed),
            "forbidden": list(contract.forbidden),
            "responsibility_ceiling": contract.responsibility_ceiling,
        }
        for name, contract in LAYER_CONTRACTS.items()
    }
