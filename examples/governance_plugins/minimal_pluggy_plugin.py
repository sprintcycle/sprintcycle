# SPDX-License-Identifier: MIT
'''最小 pluggy 治理插件：注册 ``extra_governance_argv`` 并返回空列表。

复制到你的 Python 包内，在 ``pyproject.toml`` 中注册 entry point::

    [project.entry-points."sprintcycle_governance.pluggy_plugin"]
    my_minimal = "your_package.governance_plugins.minimal_pluggy_plugin:register"

并在 ``sprintcycle.toml`` 中开启 ``[governance] pluggy_argv = true``。
'''

from __future__ import annotations

from typing import Any, List

import pluggy

hookimpl = pluggy.HookimplMarker("sprintcycle_governance")


class _MinimalPlugin:
    @hookimpl
    def extra_governance_argv(
        self,
        gate: str,
        project_path: str,
        runtime_config: Any,
    ) -> List[dict[str, Any]]:
        return []


def register(pm: pluggy.PluginManager) -> None:
    """由 importlib entry point ``sprintcycle_governance.pluggy_plugin`` 加载。"""
    pm.register(_MinimalPlugin())
