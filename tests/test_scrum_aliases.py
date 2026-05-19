"""根包与 ``release_plan.models`` 对 Scrum 对齐类型的一致导出。"""

from __future__ import annotations

from sprintcycle import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
    ReleasePlanParser,
)
from sprintcycle.application.release_plan import models as rm


def test_root_package_matches_release_plan_models() -> None:
    assert ReleasePlan is rm.ReleasePlan
    assert SprintDefinition is rm.SprintDefinition
    assert SprintBacklogItem is rm.SprintBacklogItem
    assert ProductAnchor is rm.ProductAnchor
    assert EvolutionParams is rm.EvolutionParams
    assert ExecutionMode is rm.ExecutionMode


def test_release_plan_parser_is_single_export() -> None:
    from sprintcycle.application.release_plan.parser import ReleasePlanParser as ParserCls

    assert ReleasePlanParser is ParserCls


def test_sprint_backlog_item_description_field() -> None:
    item = SprintBacklogItem(description="hello", agent="coder")
    assert item.description == "hello"
    item.description = "world"
    assert item.description == "world"


def test_yaml_description_key() -> None:
    yaml = """
project:
  name: p
  path: "."
mode: normal
sprints:
  - name: S1
    goals: ["g"]
    tasks:
      - description: from description key
        agent: coder
"""
    plan = ReleasePlanParser().parse_string(yaml.strip())
    assert plan.sprints[0].tasks[0].description == "from description key"
