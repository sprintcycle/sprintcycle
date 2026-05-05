"""
Release Plan 解析器（YAML → 内存模型）

**Scrum 对齐**：解析产物为「多 Sprint 可执行计划」；单条 ``tasks[]`` 以
``description`` 为主键，对应 **Sprint Backlog Item** 的工作说明。

详见 ``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``。
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from loguru import logger

from .models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)
from .validator import ReleasePlanValidator


class YAMLError(ValueError):
    """YAML 解析错误"""
    pass


class ReleasePlanParseError(ValueError):
    """执行计划 YAML 解析错误"""
    pass


class ReleasePlanParser:
    """
    将 YAML **执行计划**解析为 ``ReleasePlan`` 对象。

    提取 ``project``、``sprints[]``（Sprint Goal + Sprint Backlog）及工作项上的 ``agent`` 等。
    """

    # Agent 类型映射
    VALID_AGENTS = {"coder", "implement", "tester", "architect", "regression_tester"}

    # 执行模式映射
    MODE_MAPPING = {
        "normal": ExecutionMode.NORMAL,
        "evolution": ExecutionMode.EVOLUTION,
        "self_evolution": ExecutionMode.EVOLUTION,
    }

    def __init__(self, validator: Optional[ReleasePlanValidator] = None):
        """
        初始化解析器

        Args:
            validator: 执行计划验证器（可选）
        """
        self.validator = validator or ReleasePlanValidator()

    def parse_file(self, file_path: Union[str, Path]) -> ReleasePlan:
        """解析 YAML 文件为 ``ReleasePlan``。"""
        path = Path(file_path)

        if not path.exists():
            raise ReleasePlanParseError(f"文件不存在: {path}")

        if path.suffix not in {".yaml", ".yml"}:
            raise ReleasePlanParseError(f"不支持的文件格式: {path.suffix}，仅支持 .yaml 或 .yml")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise YAMLError(f"YAML 解析失败: {e}")
        except UnicodeDecodeError:
            raise YAMLError("文件编码错误，请使用 UTF-8 编码")
        except Exception as e:
            raise YAMLError(f"读取文件失败: {e}")

        if data is None:
            raise ReleasePlanParseError("执行计划文件为空")

        return self.parse_dict(data, source_path=str(path))

    def parse_string(self, content: str, source_path: str = "<string>") -> ReleasePlan:
        """解析 YAML 字符串为 ``ReleasePlan``。"""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise YAMLError(f"YAML 解析失败: {e}")

        if data is None:
            raise ReleasePlanParseError("执行计划内容为空")

        return self.parse_dict(data, source_path=source_path)

    def parse_dict(self, data: Dict[str, Any], source_path: str = "<dict>") -> ReleasePlan:
        """解析字典为 ``ReleasePlan``。"""
        try:
            project = self._parse_project(data.get("project", {}))

            mode_str = data.get("mode", "normal")
            mode = self.MODE_MAPPING.get(mode_str.lower(), ExecutionMode.NORMAL)

            evolution = None
            if mode == ExecutionMode.EVOLUTION:
                evolution = self._parse_evolution(data.get("evolution", {}))

            sprints_data = data.get("sprints", [])
            if not sprints_data:
                raise ReleasePlanParseError(f"{source_path}: 缺少 sprints 定义")

            sprints = [self._parse_sprint(s, i) for i, s in enumerate(sprints_data)]

            plan = ReleasePlan(
                project=project,
                mode=mode,
                evolution=evolution,
                sprints=sprints,
                metadata={"source_path": source_path},
            )

            validation_result = self.validator.validate(plan)
            if not validation_result.is_valid:
                errors = "\n  - ".join(validation_result.errors)
                raise ReleasePlanParseError(f"{source_path}: 执行计划验证失败:\n  - {errors}")

            logger.info(
                f"✅ 成功解析执行计划: {project.name} (包含 {len(sprints)} 个 Sprint, {plan.total_tasks} 个任务)"
            )
            return plan

        except ReleasePlanParseError:
            raise
        except Exception as e:
            raise ReleasePlanParseError(f"{source_path}: 解析失败: {e}")

    def _parse_project(self, data: Dict[str, Any]) -> ProductAnchor:
        """解析项目信息"""
        name = data.get("name")
        if not name:
            raise ReleasePlanParseError("缺少 project.name")

        path = data.get("path")
        if not path:
            raise ReleasePlanParseError("缺少 project.path")

        return ProductAnchor(
            name=name,
            path=path,
            version=data.get("version", "v1.0.0"),
        )

    def _parse_evolution(self, data: Dict[str, Any]) -> EvolutionParams:
        """解析进化配置"""
        return EvolutionParams(
            targets=data.get("targets", []),
            goals=data.get("goals", []),
            constraints=data.get("constraints", []),
            max_variations=data.get("max_variations", 5),
            iterations=data.get("iterations", 3),
        )

    def _parse_sprint(self, data: Dict[str, Any], index: int) -> SprintDefinition:
        """解析 Sprint 定义"""
        name = data.get("name")
        if not name:
            raise ReleasePlanParseError(f"Sprint #{index + 1}: 缺少 name")

        goals = data.get("goals", [])
        if not goals and "goal" in data:
            goals = [data["goal"]] if isinstance(data["goal"], str) else data["goal"]

        tasks_data = data.get("tasks", [])
        if not tasks_data:
            raise ReleasePlanParseError(f"Sprint '{name}': 缺少 tasks")

        tasks = [self._parse_task(t, i, name) for i, t in enumerate(tasks_data)]

        return SprintDefinition(
            name=name,
            goals=goals,
            tasks=tasks,
        )

    def _parse_task(self, data: Dict[str, Any], index: int, sprint_name: str) -> SprintBacklogItem:
        """解析 Sprint Backlog 项（仅接受 ``description``）。"""
        task_content = data.get("description")
        if task_content is None or (isinstance(task_content, str) and not str(task_content).strip()):
            raise ReleasePlanParseError(
                f"Sprint '{sprint_name}' Sprint Backlog Item #{index + 1}: "
                "缺少非空字段 ``description``"
            )

        agent = data.get("agent", "coder")
        if agent not in self.VALID_AGENTS:
            logger.warning(
                f"Sprint '{sprint_name}' Task #{index + 1}: 未知的 agent 类型 '{agent}'，使用 'coder'"
            )
            agent = "coder"

        target = data.get("target")

        constraints = data.get("constraints", [])
        if isinstance(constraints, str):
            constraints = [constraints]

        return SprintBacklogItem(
            description=task_content,
            agent=agent,
            target=target,
            constraints=constraints,
            expected_output=data.get("expected_output"),
            timeout=data.get("timeout", 600),
        )

    @classmethod
    def from_release_plan(cls, plan: ReleasePlan) -> dict[str, Any]:
        """从 ``ReleasePlan`` 创建调度摘要字典。"""
        return {
            "project": plan.project.to_dict(),
            "mode": plan.mode.value,
            "total_sprints": len(plan.sprints),
            "total_tasks": plan.total_tasks,
            "is_evolution": plan.is_evolution_mode,
        }
