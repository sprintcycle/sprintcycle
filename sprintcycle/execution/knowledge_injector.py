"""Phase 0：按 Sprint 检索知识卡片，写入 prd_overlay.yaml，并生成可展示的 diff。"""

from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..prd.models import PRD, PRDSprint

logger = logging.getLogger(__name__)


def _simple_yaml_overlay(notes: List[str], sprint_name: str) -> str:
    lines = [
        "# SprintCycle — prd_overlay (auto-generated, Phase 0 knowledge injection)",
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


class KnowledgeInjector:
    def __init__(self, db_path: str):
        from ..persistence.knowledge_repository import KnowledgeCardRepository

        self._repo = KnowledgeCardRepository(db_path)

    def inject_for_sprint(
        self,
        project_path: str,
        sprint: "PRDSprint",
        prd: Optional["PRD"],
        *,
        max_cards: int = 8,
    ) -> KnowledgeInjectionResult:
        query_bits = [sprint.name, " ".join(sprint.goals)]
        if prd is not None:
            query_bits.append(getattr(prd.project, "name", "") or "")
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
        overlay_path = Path(project_path) / "prd_overlay.yaml"
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
                fromfile="prd_overlay.yaml (before)",
                tofile="prd_overlay.yaml (after)",
                lineterm="\n",
            )
        )
        diff_text = "".join(diff_lines) if diff_lines else "(no textual change)\n"
        try:
            overlay_path.write_text(yaml_text, encoding="utf-8")
        except OSError as e:
            logger.warning("无法写入 prd_overlay.yaml: %s", e)
        if diff_text.strip() != "(no textual change)" and diff_text.strip():
            logger.info("Knowledge injection diff:\n%s", diff_text.rstrip())
        return KnowledgeInjectionResult(
            yaml_text=yaml_text,
            diff_text=diff_text,
            cards_used=ids,
        )
