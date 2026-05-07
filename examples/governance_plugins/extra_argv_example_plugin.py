# SPDX-License-Identifier: MIT
"""示例：通过 pluggy 追加一条治理 ``argv`` 条目（默认 ``enabled: false``，避免误伤 CI）。

条目形状与治理 YAML 中 ``argv`` 列表元素一致，见 ``docs/GOVERNANCE_ENGINEERING.md``。
"""

from __future__ import annotations

from typing import Any, List

import pluggy

hookimpl = pluggy.HookimplMarker("sprintcycle_governance")


class _EchoArgvPlugin:
    @hookimpl
    def extra_governance_argv(
        self,
        gate: str,
        project_path: str,
        runtime_config: Any,
    ) -> List[dict[str, Any]]:
        # 仅在 review 门禁合并；可按 runtime_config 或 gate 分支
        if gate not in ("review", "both"):
            return []
        return [
            {
                "name": "example-echo-argv",
                "argv": ["python", "-c", "print('pluggy extra_governance_argv ok')"],
                "enabled": False,
                "tags": [],
            }
        ]


def register(pm: pluggy.PluginManager) -> None:
    pm.register(_EchoArgvPlugin())
