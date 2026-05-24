"""Phase 0：按 Sprint 检索知识卡片，写入项目根 ``release_plan_overlay.yaml``，并生成可展示的 diff。"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from sprintcycle.domain.models import ReleasePlan, SprintDefinition


RELEASE_PLAN_OVERLAY_FILENAME = "release_plan_overlay.yaml"


def _simple_yaml_overlay(notes: List[str], sprint_name: str) -> str:
    lines = [
        "# SprintCycle — release_plan_overlay (auto-generated, Phase 0 knowledge injection)",
        f"sprint_name: {_yaml_scalar(sprint_name)}",
        "experience_notes:",
    ]
    for n in notes:
        lines.append(f"  - {_yaml_scalar(n)}")
    return "\n".join(lines) + "\n"


def _yaml_scalar(s: str) -> str:
    t = s.replace("\n", " ").strip()
    if not t:
        return '""'
    if any(c in t for c in ':"#[]{},&*!|>'):
        t = t.replace('"', '\\"')
        return f'"{t}"'
    return t


@dataclass
class KnowledgeInjectionResult:
    yaml_text: str
    diff_text: str
    cards_used: List[str]
    # 是否已成功写入项目根 release_plan_overlay.yaml（失败时 yaml_text 仍供内存上下文）
    overlay_written: bool = True


def knowledge_injection_is_material(res: KnowledgeInjectionResult) -> bool:
    """是否有可展示的注入内容（用于 run 前可选确认门）。"""
    if res.cards_used:
        return True
    d = (res.diff_text or "").strip()
    return bool(d) and d != "(no textual change)"


class KnowledgeInjector:
    def __init__(self, db_path: str):
        from sprintcycle.infrastructure.persistence.knowledge_repository import KnowledgeCardRepository

        self._repo = KnowledgeCardRepository(db_path)

    def inject_for_sprint(
        self,
        project_path: str,
        sprint: "SprintDefinition",
        release_plan: Optional["ReleasePlan"],
        *,
        max_cards: int = 8,
        persist_overlay: bool = True,
    ) -> KnowledgeInjectionResult:
        query_bits = [sprint.name, " ".join(sprint.goals)]
        if release_plan is not None:
            query_bits.append(getattr(release_plan.project, "name", "") or "")
        query = " ".join(b for b in query_bits if b).strip()
        cards = self._repo.search(query=query, limit=max_cards)
        notes: List[str] = []
        ids: List[str] = []
        for c in cards:
            snippet = (c.body or c.domain or "")[:400]
            if snippet:
                notes.append(snippet)
                ids.append(c.id)
        yaml_text = _simple_yaml_overlay(notes, sprint.name)
        overlay_path = Path(project_path) / RELEASE_PLAN_OVERLAY_FILENAME
        previous = ""
        if overlay_path.is_file():
            try:
                previous = overlay_path.read_text(encoding="utf-8")
            except OSError:
                previous = ""
        diff_lines = list(
            difflib.unified_diff(
                previous.splitlines(keepends=True),
                yaml_text.splitlines(keepends=True),
                fromfile=f"{RELEASE_PLAN_OVERLAY_FILENAME} (before)",
                tofile=f"{RELEASE_PLAN_OVERLAY_FILENAME} (after)",
                lineterm="\n",
            )
        )
        diff_text = "".join(diff_lines) if diff_lines else "(no textual change)\n"
        overlay_written = False
        if persist_overlay:
            overlay_written = True
            try:
                overlay_path.parent.mkdir(parents=True, exist_ok=True)
                overlay_path.write_text(yaml_text, encoding="utf-8")
            except OSError as e:
                overlay_written = False
                logger.warning(
                    "无法写入 %s（内存中仍有注入内容，磁盘未更新）: %s — %s",
                    RELEASE_PLAN_OVERLAY_FILENAME,
                    overlay_path,
                    e,
                )
        if diff_text.strip() != "(no textual change)" and diff_text.strip():
            logger.info("Knowledge injection diff:\n{}", diff_text.rstrip())
        return KnowledgeInjectionResult(
            yaml_text=yaml_text,
            diff_text=diff_text,
            cards_used=ids,
            overlay_written=overlay_written,
        )
