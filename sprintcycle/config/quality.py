"""
质量档位 L0–L3（与产品方案 V4.0 对齐）

与 **G1–G4 质量门禁**（见 ``SPRINTCYCLE_PRODUCT_TECH_PLAN.md`` §2.3、``docs/PRODUCT_TECH_V4.md``）对应关系（概念层）：

- **G1** 静态与规范 → L1+ 侧由 ``runs_static_gate`` 等体现；L0 跳过静态门禁。
- **G2** 测试与覆盖 → L2/L3 由 ``runs_pytest`` / ``runs_coverage_gate`` 体现。
- **G3** 适应度与回归 → 与测量、反馈闭环结合（L3 下 Sprint 后测量等）。
- **G4** 架构不变量 → L3 下 ``runs_architecture_guard``（import-linter 等 CI 硬门禁）。

L0: 仅代码生成
L1: 静态检查（Ruff + Mypy）默认档
L2: L1 + 单元测试 + 覆盖率门禁
L3: L2 + 架构不变量 + 进化适应度（架构门禁在后续迭代完整落地）
"""

from __future__ import annotations

from typing import Literal

QualityLevel = Literal["L0", "L1", "L2", "L3"]
QualityProfile = Literal["default", "off", "fast", "strict"]

QUALITY_LEVELS = frozenset({"L0", "L1", "L2", "L3"})
QUALITY_PROFILES = frozenset({"default", "off", "fast", "strict"})


def normalize_quality_level(level: str) -> str:
    u = (level or "L1").strip().upper()
    return u if u in QUALITY_LEVELS else "L1"


def normalize_quality_profile(profile: str) -> str:
    """V4.0 §6.3：preset 档位；``default`` 表示完全按 ``quality_level`` (L0–L3)。"""
    p = (profile or "default").strip().lower()
    return p if p in QUALITY_PROFILES else "default"


def resolve_effective_quality_level(quality_profile: str, quality_level: str) -> str:
    """
    解析实际用于门禁的 L 档位。

    ``quality_profile`` 为 ``off`` / ``fast`` / ``strict`` 时**覆盖** ``quality_level``；
    ``default`` 时仅使用 ``quality_level``（与既有 sprintcycle.toml 的 ``level`` 兼容）。
    """
    p = normalize_quality_profile(quality_profile)
    if p == "default":
        return normalize_quality_level(quality_level)
    if p == "off":
        return "L0"
    if p == "fast":
        return "L1"
    if p == "strict":
        return "L3"
    return normalize_quality_level(quality_level)


def runs_pytest(level: str) -> bool:
    return normalize_quality_level(level) in ("L2", "L3")


def runs_static_gate(level: str) -> bool:
    return normalize_quality_level(level) != "L0"


def runs_coverage_gate(level: str) -> bool:
    return normalize_quality_level(level) in ("L2", "L3")


def runs_architecture_guard(level: str) -> bool:
    return normalize_quality_level(level) == "L3"
