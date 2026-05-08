"""ArchGuard 侧的 ADR 索引一致性检查。"""

from __future__ import annotations

from ..adr_check import (  # noqa: F401
    check_adr_readme_index,
    check_adr_readme_strict_glob,
)

__all__ = ["check_adr_readme_index", "check_adr_readme_strict_glob"]
