"""
Evolution plan sources — 进化子域「轻量 Release Plan」视图

**与主路径 ``release_plan.models.PRD`` 的边界**（Scrum 对齐命名见
``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``）：

- 本模块的 ``EvolutionReleasePlan`` 为 **dict 型 Sprint 切片 + 进化元数据**（置信度、收益等），
  供 ``EvolutionPipeline``、磁盘 ``release_plan/*.yaml`` 扫描、诊断生成等使用。
- 委托 ``SprintOrchestrator`` / UI 展示 **主线执行结果** 时，请使用
  ``execution.sprint_types.SprintResult`` / ``TaskResult``（或 ``SprintCycle.run`` 的 ``RunResult``），
  **不要**与 ``EvolutionReleasePlanResult``（进化管道聚合）混拼为同一 JSON 形状。

具体实现：

- ``ManualPRDSource``：从项目根下默认 ``release_plan/`` 读取 ``*.yaml``
- ``DiagnosticPRDSource``：诊断驱动生成计划
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


class EvolutionPlanSourceType(Enum):
    """进化计划来源类型（manual / diagnostic）。"""
    MANUAL = "manual"
    DIAGNOSTIC = "diagnostic"


@dataclass
class EvolutionReleasePlan:
    """
    进化管道用的轻量「Release Plan」视图（非 ``release_plan.models.PRD`` 实例）。

    与主线 ``PRD`` 的区别：Sprint 为 **dict** 列表，并带进化追踪元数据（置信度、预期收益等）。
    经 ``release_plan_adapter.evolution_release_plan_to_prd`` 转为可编排的 ``PRD``。
    """
    name: str
    version: str
    path: str
    goals: List[str] = field(default_factory=list)
    sprints: List[Dict[str, Any]] = field(default_factory=list)
    source_type: EvolutionPlanSourceType = EvolutionPlanSourceType.MANUAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    confidence: float = 0.5
    expected_benefit: float = 0.0
    priority: int = 0

    @property
    def total_tasks(self) -> int:
        return sum(len(sprint.get("tasks", [])) for sprint in self.sprints)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "goals": self.goals,
            "sprints": self.sprints,
            "source_type": self.source_type.value,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "expected_benefit": self.expected_benefit,
            "priority": self.priority,
            "total_tasks": self.total_tasks,
        }


class EvolutionPlanSource(ABC):
    """进化计划来源抽象：产出 ``EvolutionReleasePlan`` 列表。"""

    @abstractmethod
    def generate(self, project_path: str) -> List[EvolutionReleasePlan]:
        pass

    @abstractmethod
    def get_source_type(self) -> EvolutionPlanSourceType:
        pass


class ManualPRDSource(EvolutionPlanSource):
    """
    人工执行计划来源（进化管道用 ``EvolutionReleasePlan`` 视图）。

    默认从项目根目录下的 **``release_plan/``** 读取 ``*.yaml``。
    """

    def __init__(self, plan_subdir: str = "release_plan"):
        self._plan_subdir = Path(plan_subdir)

    def generate(self, project_path: str) -> List[EvolutionReleasePlan]:
        plan_dir = Path(project_path) / self._plan_subdir
        if not plan_dir.exists():
            logger.warning(f"执行计划目录不存在: {plan_dir}")
            return []

        plans: List[EvolutionReleasePlan] = []
        for yaml_file in plan_dir.glob("*.yaml"):
            try:
                loaded = self._load_release_plan_yaml(yaml_file, project_path)
                if loaded:
                    plans.append(loaded)
            except Exception as e:
                logger.error(f"加载执行计划文件失败 {yaml_file}: {e}")

        plans.sort(key=lambda x: x.priority, reverse=True)
        return plans

    def _load_release_plan_yaml(
        self, yaml_path: Path, project_path: str
    ) -> Optional[EvolutionReleasePlan]:
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            project = data.get("project", {})

            goals = []
            for sprint in data.get("sprints", []):
                goals.extend(sprint.get("goals", []))

            sprints = []
            for i, sprint_data in enumerate(data.get("sprints", [])):
                sprint = {
                    "name": sprint_data.get("name", f"Sprint {i+1}"),
                    "goals": sprint_data.get("goals", []),
                    "tasks": sprint_data.get("tasks", []),
                }
                sprints.append(sprint)

            return EvolutionReleasePlan(
                name=project.get("name", yaml_path.stem),
                version=project.get("version", "v1.0.0"),
                path=str(yaml_path),
                goals=goals,
                sprints=sprints,
                source_type=EvolutionPlanSourceType.MANUAL,
                metadata={
                    "yaml_path": str(yaml_path),
                    "project_path": project_path,
                },
                priority=100,
                confidence=1.0,
            )

        except Exception as e:
            logger.error(f"解析执行计划失败 {yaml_path}: {e}")
            return None

    def get_source_type(self) -> EvolutionPlanSourceType:
        return EvolutionPlanSourceType.MANUAL


class DiagnosticPRDSource(EvolutionPlanSource):
    """诊断驱动生成 ``EvolutionReleasePlan``。"""

    def __init__(
        self,
        diagnostic_provider=None,
        prd_generator=None,
        max_prds: int = 5,
    ):
        self._diagnostic = diagnostic_provider
        self._generator = prd_generator
        self._max_prds = max_prds

    def generate(self, project_path: str) -> List[EvolutionReleasePlan]:
        if self._diagnostic is None:
            from sprintcycle.diagnostic import ProjectDiagnostic

            self._diagnostic = ProjectDiagnostic()

        if self._generator is None:
            from sprintcycle.diagnostic import DiagnosticPRDGenerator

            self._generator = DiagnosticPRDGenerator()

        logger.info(f"开始诊断项目: {project_path}")
        try:
            health_report = self._diagnostic.diagnose(project_path)
        except Exception as e:
            logger.opt(exception=True).error("项目诊断失败: {}", e)
            return []

        logger.info("生成进化计划…")
        try:
            raw_plans = self._generator.generate(health_report, project_path)
        except Exception as e:
            logger.opt(exception=True).error("计划生成失败: {}", e)
            return []

        filtered = self._filter_plans(raw_plans)
        filtered.sort(key=lambda x: x.priority, reverse=True)
        return filtered[: self._max_prds]

    def _filter_plans(
        self, plans: List[EvolutionReleasePlan]
    ) -> List[EvolutionReleasePlan]:
        return [
            p
            for p in plans
            if p.confidence >= 0.5 and p.expected_benefit > 0
        ]

    def get_source_type(self) -> EvolutionPlanSourceType:
        return EvolutionPlanSourceType.DIAGNOSTIC
