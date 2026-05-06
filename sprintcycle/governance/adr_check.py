"""ADR 目录与 README 索引一致性（低成本）。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set

from .report import GovernanceViolation


def _linked_basenames_from_readme(text: str) -> Set[str]:
    """从 README 中提取指向 ``*.md`` 的链接目标文件名（仅 basename）。"""
    out: Set[str] = set()
    for m in re.finditer(r"\[[^\]]*\]\(([^\s)]+\.md)\)", text, flags=re.IGNORECASE):
        name = Path(m.group(1).strip()).name
        if name.lower() != "readme.md":
            out.add(name)
    for m in re.finditer(r"(?<![\w/])(\d{4}-\d{2}-\d{2}-[\w-]+\.md)\b", text, flags=re.IGNORECASE):
        name = m.group(1).strip()
        if name.lower() != "readme.md":
            out.add(name)
    return out


def check_adr_readme_index(project_root: Path) -> List[GovernanceViolation]:
    """
    若存在 ``docs/adr/README.md``，则校验：
    - README 中列出的 ``NNNN-*.md`` 均存在于 ``docs/adr/``；
    - ``docs/adr/`` 下除 README 外的 ``*.md`` 最好在 README 中有索引（warning）。
    """
    violations: List[GovernanceViolation] = []
    adr_dir = project_root / "docs" / "adr"
    readme = adr_dir / "README.md"
    if not readme.is_file():
        return violations

    text = readme.read_text(encoding="utf-8", errors="replace")
    linked = _linked_basenames_from_readme(text)
    on_disk = {p.name for p in adr_dir.glob("*.md") if p.name.lower() != "readme.md"}

    missing_on_disk = linked - on_disk
    for name in sorted(missing_on_disk):
        violations.append(
            GovernanceViolation(
                rule_id="adr:readme_stale",
                severity="error",
                message=f"README 索引了不存在的文件: {name}",
                location={"readme": str(readme), "file": name},
            )
        )

    orphan = on_disk - linked
    for name in sorted(orphan):
        violations.append(
            GovernanceViolation(
                rule_id="adr:unindexed",
                severity="warning",
                message=f"ADR 文件未在 README 中索引: {name}",
                location={"readme": str(readme), "file": name},
            )
        )

    return violations


def check_adr_readme_strict_glob(project_root: Path, adr_glob: str) -> List[GovernanceViolation]:
    """
    D-2 v1：当配置 ``governance_adr_glob``（相对项目根的路径 glob）时，
    ``docs/adr/README.md`` 中索引的 ``*.md`` basename 集合必须与 glob 匹配到的
    非 README 的 ``*.md`` 文件 basename 集合**完全一致**（双向差异均为 error）。
    """
    violations: List[GovernanceViolation] = []
    pattern = (adr_glob or "").strip()
    if not pattern:
        return violations

    glob_names: Set[str] = set()
    for p in sorted(project_root.glob(pattern)):
        if not p.is_file():
            continue
        if p.suffix.lower() != ".md":
            continue
        if p.name.lower() == "readme.md":
            continue
        glob_names.add(p.name)

    adr_dir = project_root / "docs" / "adr"
    readme = adr_dir / "README.md"
    if not readme.is_file():
        violations.append(
            GovernanceViolation(
                rule_id="adr:readme_required",
                severity="error",
                message="启用 adr_glob 严格模式需要存在 docs/adr/README.md",
                location={"glob": pattern, "readme": str(readme)},
            )
        )
        return violations

    text = readme.read_text(encoding="utf-8", errors="replace")
    linked = _linked_basenames_from_readme(text)

    for name in sorted(linked - glob_names):
        violations.append(
            GovernanceViolation(
                rule_id="adr:readme_not_in_glob",
                severity="error",
                message=f"README 索引了不在 adr_glob 集合内的文件: {name}",
                location={"readme": str(readme), "file": name, "glob": pattern},
            )
        )
    for name in sorted(glob_names - linked):
        violations.append(
            GovernanceViolation(
                rule_id="adr:glob_not_indexed",
                severity="error",
                message=f"adr_glob 匹配的文件未在 README 中索引: {name}",
                location={"readme": str(readme), "file": name, "glob": pattern},
            )
        )
    return violations
