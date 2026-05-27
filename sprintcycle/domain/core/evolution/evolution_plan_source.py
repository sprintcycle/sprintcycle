"""
计划来源 — 产出 ``ReleasePlan``

用于磁盘 ``release_plan/*.yaml`` 扫描、诊断生成等；执行请经 ``SprintCycle`` /
``SprintOrchestrator``。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan
from sprintcycle.domain.generic.interfaces import ReleasePlanParserProtocol


class EvolutionPlanSourceType(Enum):
    """计划来源类型（manual / diagnostic）。"""

    MANUAL = "manual"
    DIAGNOSTIC = "diagnostic"


class EvolutionPlanSource(ABC):
    """抽象：产出 ``ReleasePlan`` 列表。"""

    @property
    @abstractmethod
    def source_type(self) -> EvolutionPlanSourceType:
        """来源类型。"""
        ...

    @abstractmethod
    def load(self) -> List[ReleasePlan]:
        """加载 ReleasePlan 列表。"""
        ...


class ReleasePlanFileSource(EvolutionPlanSource):
    """从文件系统加载 ReleasePlan。"""

    def __init__(
        self,
        plan_dir: str,
        parser: ReleasePlanParserProtocol,
    ):
        self._plan_dir = Path(plan_dir)
        self._parser = parser

    @property
    def source_type(self) -> EvolutionPlanSourceType:
        return EvolutionPlanSourceType.MANUAL

    def load(self) -> List[ReleasePlan]:
        if not self._plan_dir.exists():
            return []

        plans = []
        for yaml_file in self._plan_dir.glob("*.yaml"):
            try:
                content = yaml_file.read_text(encoding="utf-8")
                plan = self._parser.parse(content)
                plans.append(plan)
            except Exception as e:
                logger.warning(f"Failed to parse {yaml_file}: {e}")

        return plans


__all__ = [
    "EvolutionPlanSourceType",
    "EvolutionPlanSource",
    "ReleasePlanFileSource",
]
