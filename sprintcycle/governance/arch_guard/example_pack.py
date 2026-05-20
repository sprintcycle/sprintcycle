"""示例治理规则包。

团队可以把类似内容放到独立目录或项目仓库中，然后在 RuntimeConfig.governance_pack_paths 中配置路径。
支持两种导出方式：

1. `GUARD_RULES = [...]`
2. `register_rules() -> list[GuardRule]`
"""

from __future__ import annotations

from .model import GuardRule

GUARD_RULES = [
    GuardRule(
        rule_id="review:example_pack_rule",
        title="示例规则：扩展包接入成功",
        severity="info",
        action="info",
        gate="review",
        description="用于验证 pack_paths 是否能正确加载外部规则包。",
    )
]


def register_rules() -> list[GuardRule]:
    return GUARD_RULES
