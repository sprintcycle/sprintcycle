"""SQLite 引擎与会话工厂。"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def create_engine_for_path(db_path: str) -> Engine:
    path = Path(db_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{path}"
    return create_engine(url, future=True, echo=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def session_scope(engine: Engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
