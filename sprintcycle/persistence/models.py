"""ORM 模型：executions、knowledge_cards。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ExecutionRow(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    prd_name: Mapped[str] = mapped_column(String(512), default="")
    mode: Mapped[str] = mapped_column(String(64), default="normal")
    status: Mapped[str] = mapped_column(String(32), index=True, default="pending")
    current_sprint: Mapped[int] = mapped_column(Integer, default=0)
    total_sprints: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(64), default="")
    updated_at: Mapped[str] = mapped_column(String(64), default="")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checkpoint: Mapped[Optional[dict]] = mapped_column(SQLiteJSON, nullable=True)
    execution_meta: Mapped[dict] = mapped_column(SQLiteJSON, default=dict)


class KnowledgeCardRow(Base):
    __tablename__ = "knowledge_cards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sprint_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(256), default="", index=True)
    outcome: Mapped[str] = mapped_column(String(64), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    lessons: Mapped[dict] = mapped_column(SQLiteJSON, default=dict)
    related_files: Mapped[List[str]] = mapped_column(SQLiteJSON, default=list)
    tags: Mapped[List[str]] = mapped_column(SQLiteJSON, default=list)
    scores: Mapped[dict] = mapped_column(SQLiteJSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now())
