"""知识卡片 CRUD 与简单检索（SQLite + SQLAlchemy）。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import KnowledgeCardRow
from .session import create_engine_for_path, init_db


@dataclass
class KnowledgeCard:
    id: str
    sprint_id: Optional[str]
    domain: str
    outcome: str
    body: str
    lessons: Dict[str, Any]
    related_files: List[str]
    tags: List[str]
    scores: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sprint_id": self.sprint_id,
            "domain": self.domain,
            "outcome": self.outcome,
            "body": self.body,
            "lessons": self.lessons,
            "related_files": self.related_files,
            "tags": self.tags,
            "scores": self.scores,
        }


class KnowledgeCardRepository:
    """与 executions 共用同一 DB 文件时可复用引擎。"""

    def __init__(self, db_path: str):
        self.engine = create_engine_for_path(db_path)
        init_db(self.engine)
        self._Session = sessionmaker(self.engine, expire_on_commit=False, class_=Session)

    def _session(self) -> Session:
        return self._Session()

    @staticmethod
    def _from_row(row: KnowledgeCardRow) -> KnowledgeCard:
        return KnowledgeCard(
            id=row.id,
            sprint_id=row.sprint_id,
            domain=row.domain or "",
            outcome=row.outcome or "",
            body=row.body or "",
            lessons=dict(row.lessons or {}),
            related_files=list(row.related_files or []),
            tags=list(row.tags or []),
            scores=dict(row.scores or {}),
        )

    def add(
        self,
        *,
        domain: str = "",
        outcome: str = "",
        body: str = "",
        sprint_id: Optional[str] = None,
        lessons: Optional[Dict[str, Any]] = None,
        related_files: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        scores: Optional[Dict[str, Any]] = None,
        card_id: Optional[str] = None,
    ) -> KnowledgeCard:
        cid = card_id or uuid.uuid4().hex
        row = KnowledgeCardRow(
            id=cid,
            sprint_id=sprint_id,
            domain=domain,
            outcome=outcome,
            body=body,
            lessons=dict(lessons or {}),
            related_files=list(related_files or []),
            tags=list(tags or []),
            scores=dict(scores or {}),
        )
        s = self._session()
        try:
            s.add(row)
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()
        return self._from_row(row)

    def get(self, card_id: str) -> Optional[KnowledgeCard]:
        s = self._session()
        try:
            row = s.get(KnowledgeCardRow, card_id)
            if row is None:
                return None
            return self._from_row(row)
        finally:
            s.close()

    def search(
        self,
        query: str = "",
        tags: Optional[Sequence[str]] = None,
        limit: int = 50,
    ) -> List[KnowledgeCard]:
        q = select(KnowledgeCardRow).order_by(KnowledgeCardRow.created_at.desc()).limit(limit * 4)
        needle = (query or "").strip().lower()
        tag_set = {t.lower() for t in (tags or []) if t}
        s = self._session()
        try:
            rows = list(s.scalars(q).all())
        finally:
            s.close()
        out: List[KnowledgeCard] = []
        for row in rows:
            card = self._from_row(row)
            if needle:
                tags_s = " ".join(card.tags).lower()
                blob = f"{card.domain} {card.body} {card.outcome} {tags_s}".lower()
                tokens = [t for t in needle.split() if len(t) >= 2]
                if tokens:
                    if not any(t in blob for t in tokens):
                        continue
                elif needle not in blob:
                    continue
            if tag_set:
                ctags = {t.lower() for t in card.tags}
                if not tag_set.issubset(ctags):
                    continue
            out.append(card)
            if len(out) >= limit:
                break
        return out

    def list_recent(self, limit: int = 50) -> List[KnowledgeCard]:
        s = self._session()
        try:
            q = select(KnowledgeCardRow).order_by(KnowledgeCardRow.created_at.desc()).limit(limit)
            rows = list(s.scalars(q).all())
            return [self._from_row(r) for r in rows]
        finally:
            s.close()

    def delete(self, card_id: str) -> bool:
        s = self._session()
        try:
            row = s.get(KnowledgeCardRow, card_id)
            if row is None:
                return False
            s.delete(row)
            s.commit()
            return True
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()
