"""
自进化 Release Plan → 与普通模式相同的多 Sprint 结构（单一执行路径）。

执行前将 ``mode: evolution`` + ``evolution.targets`` 展开为
``SprintDefinition`` / ``SprintBacklogItem``（优化类任务使用 ``coder`` + constraints）。
"""

from __future__ import annotations

from dataclasses import replace
from enum import Enum
from typing import List

from .models import ExecutionMode, ReleasePlan, SprintBacklogItem, SprintDefinition


class EvolutionPath(str, Enum):
    """优化维度（与执行策略字符串一致；供配置/元数据使用）。"""

    PERFORMANCE = "performance"
    QUALITY = "quality"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    REFACTORING = "refactoring"


EvolutionStrategy = EvolutionPath  # 后向兼容别名


def infer_evolution_strategy(goals: List[str]) -> str:
    """由 goals 文本推断展开任务使用的 strategy 标签。"""
    goals_text = " ".join(goals).lower()
    if any(kw in goals_text for kw in ("性能", "速度", "performance", "latency", "吞吐")):
        return EvolutionPath.PERFORMANCE.value
    if any(kw in goals_text for kw in ("可读", "可维护", "readability", "maintainability", "文档")):
        return EvolutionPath.READABILITY.value
    if any(kw in goals_text for kw in ("重构", "拆分", "refactor", "架构")):
        return EvolutionPath.REFACTORING.value
    return EvolutionPath.QUALITY.value


def expand_release_plan_for_execution(plan: ReleasePlan) -> ReleasePlan:
    """
    若非自进化模式，原样返回。

    若为自进化模式且配置了 ``evolution.targets``，则生成新的
    ``ReleasePlan``：``mode`` 置为 ``NORMAL``，``sprints`` 为按 target
    展开的标准流水线，``evolution`` 清空（快照写入 ``metadata``）。
    """
    if not plan.is_evolution_mode:
        return plan
    evo = plan.evolution
    if evo is None or not evo.targets:
        return plan

    strategy = infer_evolution_strategy(evo.goals)
    goals = list(evo.goals)
    base_constraints = list(evo.constraints or [])
    ex_constraints = base_constraints + [
        f"evolution_strategy:{strategy}",
        "task_kind:evolution_optimize",
    ]

    new_sprints: List[SprintDefinition] = []
    for target in evo.targets:
        opt_desc = (
            f"在以下进化目标下优化 `{target}` 的实现（策略: {strategy}）"
            + (f": {'; '.join(goals)}" if goals else "")
            + "。在保持行为兼容的前提下改进性能、质量与可维护性。"
        )
        new_sprints.append(
            SprintDefinition(
                name=f"进化: {target}",
                goals=list(goals),
                tasks=[
                    SprintBacklogItem(
                        description=f"架构设计: {target}",
                        agent="architect",
                        target=target,
                    ),
                    SprintBacklogItem(
                        description=opt_desc,
                        agent="coder",
                        target=target,
                        constraints=list(ex_constraints),
                    ),
                    SprintBacklogItem(
                        description=f"验证进化结果: {target}",
                        agent="tester",
                        target=target,
                    ),
                    SprintBacklogItem(
                        description=f"回归测试: {target}",
                        agent="regression_tester",
                        target=target,
                    ),
                ],
            )
        )

    meta = dict(plan.metadata or {})
    meta["expanded_from_evolution"] = True
    meta["original_mode"] = plan.mode.value
    meta["evolution_snapshot"] = evo.to_dict()

    return replace(
        plan,
        mode=ExecutionMode.NORMAL,
        sprints=new_sprints,
        evolution=None,
        metadata=meta,
    )


__all__ = [
    "EvolutionPath",
    "EvolutionStrategy",
    "expand_release_plan_for_execution",
    "infer_evolution_strategy",
]
