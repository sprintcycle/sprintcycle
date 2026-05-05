"""Scrum 类型别名与 PRDTask.description。"""

from __future__ import annotations

from sprintcycle import (
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
    ProductAnchor,
    ReleasePlanParser,
)
from sprintcycle.release_plan.models import PRD, PRDProject, PRDSprint, PRDTask


def test_type_aliases_are_identity() -> None:
    assert ReleasePlan is PRD
    assert SprintDefinition is PRDSprint
    assert SprintBacklogItem is PRDTask
    assert ProductAnchor is PRDProject


def test_release_plan_parser_alias() -> None:
    from sprintcycle.release_plan.parser import PRDParser

    assert ReleasePlanParser is PRDParser


def test_sprint_backlog_item_description_property() -> None:
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
    prd = ReleasePlanParser().parse_string(yaml.strip())
    assert prd.sprints[0].tasks[0].description == "from description key"
