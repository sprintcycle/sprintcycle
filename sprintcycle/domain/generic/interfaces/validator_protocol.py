"""
Release Plan Validator - Domain Layer

纯领域层验证器，仅验证内存中的 ReleasePlan 模型，
不依赖文件系统或外部基础设施。
"""

from dataclasses import dataclass
from typing import List

from sprintcycle.domain.generic.models import (
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)


class ValidationError(Exception):
    """验证错误"""

    pass


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ReleasePlanValidator:
    """
    执行计划验证器 - 纯领域层

    验证内存中 ReleasePlan 对象的结构完整性和内容有效性，
    不进行文件 I/O 操作。
    """

    # Agent 类型白名单
    VALID_AGENTS = {"coder", "implement", "tester", "architect", "regression_tester"}

    def validate(self, plan: ReleasePlan) -> ValidationResult:
        """验证 ``ReleasePlan`` 对象。"""
        errors: List[str] = []
        warnings: List[str] = []

        project_errors, project_warnings = self._validate_project(plan.project)
        errors.extend(project_errors)
        warnings.extend(project_warnings)

        mode_errors, mode_warnings = self._validate_mode(plan)
        errors.extend(mode_errors)
        warnings.extend(mode_warnings)

        sprint_errors, sprint_warnings = self._validate_sprints(plan)
        errors.extend(sprint_errors)
        warnings.extend(sprint_warnings)

        if not warnings and len(plan.sprints) > 5:
            warnings.append(f"Sprint 数量较多 ({len(plan.sprints)})，建议拆分为多份执行计划")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def _validate_project(self, project: ProductAnchor) -> tuple:
        """验证项目信息"""
        errors: List[str] = []
        warnings: List[str] = []

        if not project.name:
            errors.append("project.name 不能为空")
        elif len(project.name) > 100:
            warnings.append("project.name 过长，可能影响显示")

        if not project.path:
            errors.append("project.path 不能为空")

        if project.version and not project.version.startswith("v"):
            warnings.append("version 建议使用 'v' 前缀格式，如 'v1.0.0'")

        return errors, warnings

    def _validate_mode(self, plan: ReleasePlan) -> tuple:
        """验证执行模式"""
        errors: List[str] = []
        warnings: List[str] = []

        if plan.mode == ExecutionMode.EVOLUTION:
            if not plan.evolution:
                errors.append("自进化模式 (mode: evolution) 必须配置 evolution 部分")
            elif not plan.evolution.targets:
                errors.append("自进化模式必须指定至少一个 targets")
            elif not plan.evolution.goals:
                warnings.append("自进化模式建议指定 goals")

        return errors, warnings

    def _validate_sprints(self, plan: ReleasePlan) -> tuple:
        """验证 Sprint 列表"""
        errors: List[str] = []
        warnings: List[str] = []

        if plan.is_evolution_mode and plan.evolution and plan.evolution.targets:
            if not plan.sprints:
                warnings.append("自进化模式: sprints 为空，执行时将仅按 evolution.targets 展开为标准 Sprint")
                return errors, warnings
            warnings.append(
                "自进化模式: 执行时将按 evolution.targets 重新展开为标准 Sprint，"
                "YAML 中的 sprints 仅作参考/文档，不会在执行阶段原样使用"
            )

        if not plan.sprints:
            errors.append("必须定义至少一个 Sprint")
            return errors, warnings

        for i, sprint in enumerate(plan.sprints):
            sprint_errors, sprint_warnings = self._validate_single_sprint(sprint, i)
            errors.extend(sprint_errors)
            warnings.extend(sprint_warnings)

        return errors, warnings

    def _validate_single_sprint(self, sprint: SprintDefinition, index: int) -> tuple:
        """验证单个 Sprint"""
        errors: List[str] = []
        warnings: List[str] = []

        sprint_label = f"Sprint #{index + 1} '{sprint.name}'"

        if not sprint.name:
            errors.append(f"{sprint_label}: 缺少 name")

        if not sprint.tasks:
            errors.append(f"{sprint_label}: 缺少 tasks")
            return errors, warnings

        for i, task in enumerate(sprint.tasks):
            task_errors, task_warnings = self._validate_task(task, index, i)
            errors.extend(task_errors)
            warnings.extend(task_warnings)

        return errors, warnings

    def _validate_task(self, task: SprintBacklogItem, sprint_index: int, task_index: int) -> tuple:
        """验证单个任务"""
        errors: List[str] = []
        warnings: List[str] = []

        task_label = f"Sprint #{sprint_index + 1} Task #{task_index + 1}"

        if not task.description:
            errors.append(f"{task_label}: 缺少 task 描述")
        elif len(task.description) < 10:
            warnings.append(f"{task_label}: task 描述过短，建议提供更详细的任务说明")

        if task.agent not in self.VALID_AGENTS:
            errors.append(f"{task_label}: 未知的 agent 类型 '{task.agent}'")

        if task.timeout <= 0:
            errors.append(f"{task_label}: timeout 必须大于 0")
        elif task.timeout > 3600:
            warnings.append(f"{task_label}: timeout 较长 ({task.timeout}s)，可能导致执行缓慢")

        return errors, warnings
