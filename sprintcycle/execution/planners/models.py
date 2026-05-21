"""
Release Plan 数据模型（执行计划 / 多 Sprint 交付切片）

**Scrum 对照**（详见 ``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``）：

- ``ReleasePlan``：持久化计划文档，近似 **Release 内多 Sprint 的交付编排**（非完整 Product Backlog）。
- ``SprintDefinition``：一次 **Sprint** 的边界；``goals`` ≈ Sprint Goal 表述；``tasks`` ≈ Sprint Backlog。
- ``SprintBacklogItem``：Sprint 内单条工作项；YAML 入站字段 **仅** ``description``。

本模块复用 ``application.release_plan.models`` 的核心类型并添加执行层专属方法。
"""

from typing import Any, Dict, List

from sprintcycle.application.release_plan.models import (
    EvolutionParams as _BaseEvolutionParams,
)
from sprintcycle.application.release_plan.models import (
    ExecutionMode,
)
from sprintcycle.application.release_plan.models import (
    ProductAnchor as _BaseProductAnchor,
)
from sprintcycle.application.release_plan.models import (
    ReleasePlan as _BaseReleasePlan,
)
from sprintcycle.application.release_plan.models import (
    SprintBacklogItem as _BaseSprintBacklogItem,
)
from sprintcycle.application.release_plan.models import (
    SprintDefinition as _BaseSprintDefinition,
)
from sprintcycle.domain.quality_spec.spec.constraint_spec import ConstraintSpec
from sprintcycle.domain.quality_spec.spec.task_spec import TaskSpec
from sprintcycle.domain.quality_spec.spec.verification_strategy import VerificationStrategySpec

# Re-export base types so existing import paths remain valid
__all__ = [
    "ExecutionMode",
    "ProductAnchor",
    "EvolutionParams",
    "SprintBacklogItem",
    "SprintDefinition",
    "ReleasePlan",
]


class ProductAnchor(_BaseProductAnchor):
    """产品侧锚点：名称、路径、版本（执行层扩展）。"""

    pass


class EvolutionParams(_BaseEvolutionParams):
    """进化配置（执行层扩展）。"""

    pass


class SprintBacklogItem(_BaseSprintBacklogItem):
    """Sprint 内工作项（执行层扩展）。"""

    def to_task_spec(self, sprint_name: str = "", sprint_goal: str = "") -> TaskSpec:
        spec_refs = [self.spec_ref] if self.spec_ref else []
        task_constraints = ConstraintSpec(domain={"task": list(self.constraints)}).to_dict()
        verification_strategy = VerificationStrategySpec.default_for_task_type("feature").to_dict()
        metadata: Dict[str, Any] = {
            "agent": self.agent,
            "target": self.target,
            "expected_output": self.expected_output,
            "timeout": self.timeout,
            "sprint_name": sprint_name,
            "sprint_goal": sprint_goal,
        }
        return TaskSpec(
            id=metadata.get("target") or self.description[:48].strip().replace(" ", "-") or "task",
            title=self.description.splitlines()[0].strip() if self.description else "",
            type="feature",
            spec_refs=spec_refs,
            acceptance_refs=[],
            constraints=task_constraints,
            verification_strategy=verification_strategy,
            rollback_plan={},
            risk_level="medium",
            intent=self.description,
            summary=self.description,
            metadata=metadata,
        )


class SprintDefinition(_BaseSprintDefinition):
    """单次 Sprint（执行层扩展）。"""

    def to_task_specs(self) -> List[TaskSpec]:
        sprint_goal = " ".join(self.goals).strip()
        return [task.to_task_spec(sprint_name=self.name, sprint_goal=sprint_goal) for task in self.tasks]


class ReleasePlan(_BaseReleasePlan):
    """可执行交付计划，多 Sprint（执行层扩展）。"""

    def to_task_specs(self) -> List[TaskSpec]:
        specs: List[TaskSpec] = []
        for sprint in self.sprints:
            specs.extend(sprint.to_task_specs())
        return specs

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
        return """# SprintCycle 执行计划示例

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
"""
