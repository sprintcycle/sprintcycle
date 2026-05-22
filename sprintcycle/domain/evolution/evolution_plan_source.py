"""
计划来源 — 产出 ``ReleasePlan``（与 ``ReleasePlanParser`` 解析结果一致）。

用于磁盘 ``release_plan/*.yaml`` 扫描、诊断生成等；执行请经 ``SprintCycle`` /
``SprintOrchestrator``。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from enum import Enum
from pathlib import Path
from typing import List

from loguru import logger

from sprintcycle.domain.models import ReleasePlan
from sprintcycle.application.release_plan.parser import ReleasePlanParseError, ReleasePlanParser


class EvolutionPlanSourceType(Enum):
    """计划来源类型（manual / diagnostic）。"""

    MANUAL = "manual"
    DIAGNOSTIC = "diagnostic"


class EvolutionPlanSource(ABC):
    """抽象：产出 ``ReleasePlan`` 列表。"""

    @abstractmethod
    def generate(self, project_path: str) -> List[ReleasePlan]:
        pass

    @abstractmethod
    def get_source_type(self) -> EvolutionPlanSourceType:
        pass


class ManualReleasePlanSource(EvolutionPlanSource):
    """
    从项目根目录下的 **``release_plan/``** 读取 ``*.yaml``，解析为 ``ReleasePlan``。
    """

    def __init__(self, plan_subdir: str = "release_plan"):
        self._plan_subdir = Path(plan_subdir)

    def generate(self, project_path: str) -> List[ReleasePlan]:
        plan_dir = Path(project_path) / self._plan_subdir
        if not plan_dir.exists():
            logger.warning(f"执行计划目录不存在: {plan_dir}")
            return []

        parser = ReleasePlanParser()
        plans: List[ReleasePlan] = []
        for yaml_file in plan_dir.glob("*.yaml"):
            try:
                rp = parser.parse_file(yaml_file)
                md = dict(rp.metadata)
                md["yaml_path"] = str(yaml_file)
                md["plan_source_type"] = EvolutionPlanSourceType.MANUAL.value
                md["diagnostic_priority"] = 100
                md["diagnostic_confidence"] = 1.0
                md["diagnostic_expected_benefit"] = 1.0
                plans.append(replace(rp, metadata=md))
            except ReleasePlanParseError as e:
                logger.error(f"解析执行计划失败 {yaml_file}: {e}")
            except Exception as e:
                logger.error(f"加载执行计划文件失败 {yaml_file}: {e}")

        plans.sort(key=lambda p: int(p.metadata.get("diagnostic_priority", 0)), reverse=True)
        return plans

    def get_source_type(self) -> EvolutionPlanSourceType:
        return EvolutionPlanSourceType.MANUAL


class DiagnosticReleasePlanSource(EvolutionPlanSource):
    """诊断驱动生成 ``ReleasePlan``。"""

    def __init__(
        self,
        diagnostic_provider=None,
        release_plan_generator=None,
        max_plans: int = 5,
    ):
        self._diagnostic = diagnostic_provider
        self._generator = release_plan_generator
        self._max_plans = max_plans

    def generate(self, project_path: str) -> List[ReleasePlan]:
        if self._diagnostic is None:
            from sprintcycle.support.diagnostic import ProjectDiagnostic

            self._diagnostic = ProjectDiagnostic()

        if self._generator is None:
            from sprintcycle.support.diagnostic import DiagnosticReleasePlanGenerator

            self._generator = DiagnosticReleasePlanGenerator()

        logger.info(f"开始诊断项目: {project_path}")
        try:
            health_report = self._diagnostic.diagnose(project_path)
        except Exception as e:
            logger.opt(exception=True).error("项目诊断失败: {}", e)
            return []

        logger.info("生成执行计划…")
        try:
            raw_plans = self._generator.generate(health_report, project_path)
        except Exception as e:
            logger.opt(exception=True).error("计划生成失败: {}", e)
            return []

        filtered = self._filter_plans(raw_plans)
        filtered.sort(
            key=lambda p: int(p.metadata.get("diagnostic_priority", 0)),
            reverse=True,
        )
        return filtered[: self._max_plans]

    def _filter_plans(self, plans: List[ReleasePlan]) -> List[ReleasePlan]:
        return [
            p
            for p in plans
            if float(p.metadata.get("diagnostic_confidence", 0.5)) >= 0.5
            and float(p.metadata.get("diagnostic_expected_benefit", 0)) > 0
        ]

    def get_source_type(self) -> EvolutionPlanSourceType:
        return EvolutionPlanSourceType.DIAGNOSTIC
