"""SprintCycle CLI 包。控制台入口 ``cli`` 定义于 ``main``；测试可 patch ``sprintcycle.cli.SprintCycle``。"""

from __future__ import annotations

from sprintcycle.api import SprintCycle
from sprintcycle.cli.main import cli

__all__ = ["cli", "SprintCycle"]
