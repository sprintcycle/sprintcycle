"""
Release Plan 数据模型（执行计划 / 多 Sprint 交付切片）

**Scrum 对照**（详见 ``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``）：

- ``ReleasePlan``：持久化计划文档，近似 **Release 内多 Sprint 的交付编排**（非完整 Product Backlog）。
- ``SprintDefinition``：一次 **Sprint** 的边界；``goals`` ≈ Sprint Goal 表述；``tasks`` ≈ Sprint Backlog。
- ``SprintBacklogItem``：Sprint 内单条工作项；YAML 入站字段 **仅** ``description``。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionMode(Enum):
    """计划级执行模式（Scrum：默认即标准 Sprint 交付链）。"""
    NORMAL = "normal"  # 标准 Sprint Backlog 顺序交付（实现/测试等）
    EVOLUTION = "evolution"  # 持续改进/实验环（非 Scrum 标准事件；序列化值保持 evolution）


@dataclass
class ProductAnchor:
    """产品侧锚点：名称、路径、版本。"""
    name: str
    path: str
    version: str = "v1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "version": self.version,
        }


@dataclass
class EvolutionParams:
    """进化配置（自进化模式专用）"""
    targets: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    max_variations: int = 5
    iterations: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "targets": self.targets,
            "goals": self.goals,
            "constraints": self.constraints,
            "max_variations": self.max_variations,
            "iterations": self.iterations,
        }


@dataclass
class SprintBacklogItem:
    """Sprint 内工作项（Scrum：Sprint Backlog Item）；主字段 ``description``。"""
    description: str
    agent: str = "coder"  # Agent 类型
    target: Optional[str] = None  # 目标文件/目录
    constraints: List[str] = field(default_factory=list)  # 任务约束
    expected_output: Optional[str] = None  # 期望输出
    timeout: int = 600  # 超时时间（秒）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "agent": self.agent,
            "target": self.target,
            "constraints": self.constraints,
            "expected_output": self.expected_output,
            "timeout": self.timeout,
        }


@dataclass
class SprintDefinition:
    """单次 Sprint：Sprint Goal（``goals``）+ Sprint Backlog（``tasks``）。"""
    name: str
    goals: List[str] = field(default_factory=list)
    tasks: List[SprintBacklogItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "goals": self.goals,
            "tasks": [t.to_dict() for t in self.tasks],
        }


@dataclass
class ReleasePlan:
    """可执行交付计划（多 Sprint）。"""
    project: ProductAnchor
    mode: ExecutionMode = ExecutionMode.NORMAL
    evolution: Optional[EvolutionParams] = None
    sprints: List[SprintDefinition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_evolution_mode(self) -> bool:
        """是否自进化模式"""
        return self.mode == ExecutionMode.EVOLUTION

    @property
    def total_tasks(self) -> int:
        """总任务数"""
        return sum(len(sprint.tasks) for sprint in self.sprints)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project.to_dict(),
            "mode": self.mode.value,
            "evolution": self.evolution.to_dict() if self.evolution else None,
            "sprints": [s.to_dict() for s in self.sprints],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    def to_yaml(self) -> str:
        """转换为 YAML 字符串"""
        from io import StringIO

        import yaml

        data: Dict[str, Any] = {
            "project": self.project.to_dict(),
            "mode": self.mode.value,
        }

        if self.evolution:
            data["evolution"] = self.evolution.to_dict()

        data["sprints"] = [s.to_dict() for s in self.sprints]

        if self.metadata:
            data["metadata"] = self.metadata

        class SafeDumper(yaml.SafeDumper):
            def increase_indent(self, flow=False, indentless=False):
                return super().increase_indent(flow, False)

        output = StringIO()
        yaml.dump(
            data,
            output,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            Dumper=SafeDumper,
        )

        return output.getvalue()

    @classmethod
    def sample_release_plan_yaml(cls) -> str:
        """生成示例执行计划 YAML 字符串"""
        return '''# SprintCycle 执行计划示例

project:
  name: "my-project"
  path: "/path/to/project"
  version: "v1.0.0"

mode: normal

sprints:
  - name: "Sprint 1: 功能开发"
    goals:
      - "实现核心功能"
    tasks:
      - description: |
          创建主页面
        agent: coder
        target: src/pages/main.vue
'''
