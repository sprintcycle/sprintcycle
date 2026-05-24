"""
异步 SQLite 存储基类（SQLAlchemy 2.0 async）。

遵循洋葱架构：本模块位于 infrastructure 层，被 governance/application/domain 层复用。
统一 5 套 SQLite 实现（state_store、event_backend、mq、registry、hitl）的共性逻辑：

- 路径规范化 + 父目录自动创建
- 引擎/连接生命周期管理
- WAL pragma 初始化
- 异步连接上下文管理器
- 统一 JSON 序列化工具

子类只需：
1. 实现 ``_define_schema()`` 定义表结构
2. 调用 ``async def`` 方法操作数据
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Sequence

from loguru import logger

try:
    import aiosqlite
except ImportError:  # pragma: no cover
    aiosqlite = None  # type: ignore[assignment]

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, async_engine_from_config


class BaseSqliteStore(ABC):
    """异步 SQLite 存储基类。

    Args:
        db_path: SQLite 数据库路径（支持 ~ 展开和相对路径）
        enable_wal: 是否启用 WAL 模式（默认 True）
        connect_timeout: 连接超时秒数（默认 30）
    """

    # 类级别：所有实例共享同一引擎（进程内单例）
    _engines: dict[str, AsyncEngine] = {}

    def __init__(
        self,
        db_path: str,
        *,
        enable_wal: bool = True,
        connect_timeout: int = 30,
    ) -> None:
        self._raw_path = db_path
        self._resolved_path = str(Path(db_path).expanduser().resolve())
        self._enable_wal = enable_wal
        self._connect_timeout = connect_timeout
        self._schema_initialized = False

    # ─────────────────────────────────────────────────────────────────
    # 公开 API（子类继承使用）
    # ─────────────────────────────────────────────────────────────────

    @property
    def db_path(self) -> str:
        """规范化后的绝对路径。"""
        return self._resolved_path

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """异步连接上下文管理器，自动归还连接。

        用法：
            async with self.connect() as conn:
                await conn.execute(...)
        """
        engine = await self._get_engine()
        async with engine.connect() as conn:
            # 确保 schema 已初始化（惰性单次）
            if not self._schema_initialized:
                await self._init_schema(conn)
                self._schema_initialized = True
            yield conn

    async def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Sequence[Any]:
        """执行查询并返回全部结果行。"""
        async with self.connect() as conn:
            result = await conn.execute(text(query), params or ())
            if result.returns_rows:
                return list(result.fetchall())
            return []

    async def execute_one(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any | None:
        """执行查询并返回第一行。"""
        rows = await self.execute(query, params)
        return rows[0] if rows else None

    async def execute_modify(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> int:
        """执行修改语句（INSERT/UPDATE/DELETE），返回影响的行数。"""
        async with self.connect() as conn:
            result = await conn.execute(text(query), params or ())
            await conn.commit()
            return result.rowcount or 0

    @staticmethod
    def json_dumps(data: Any) -> str:
        """JSON 序列化（支持中文）。"""
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def json_loads(raw: str | bytes | None) -> Any:
        """JSON 反序列化。"""
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    @staticmethod
    def now_iso() -> str:
        """返回当前时间的 ISO 格式字符串。"""
        return datetime.now().isoformat()

    # ─────────────────────────────────────────────────────────────────
    # 模板方法（子类实现）
    # ─────────────────────────────────────────────────────────────────

    @abstractmethod
    def _define_schema(self, conn: AsyncConnection) -> None:
        """定义表结构（CREATE TABLE IF NOT EXISTS ...）。

        由 ``_init_schema()`` 调用，子类实现具体 DDL。
        只需处理当前 Store 需要的表，无需处理共享表。
        """

    # ─────────────────────────────────────────────────────────────────
    # 私有方法（基类逻辑）
    # ─────────────────────────────────────────────────────────────────

    async def _get_engine(self) -> AsyncEngine:
        """获取或创建进程级单例引擎。"""
        if self._resolved_path not in self._engines:
            # 确保父目录存在
            Path(self._resolved_path).parent.mkdir(parents=True, exist_ok=True)

            url = f"sqlite+aiosqlite:///{self._resolved_path}"
            self._engines[self._resolved_path] = async_engine_from_config(
                {
                    "url": url,
                    "connect_args": {
                        "timeout": self._connect_timeout,
                        "check_same_thread": False,
                    },
                    "echo": False,
                },
                future=True,
            )
            logger.debug("BaseSqliteStore: created engine for {}", self._resolved_path)

        return self._engines[self._resolved_path]

    async def _init_schema(self, conn: AsyncConnection) -> None:
        """初始化 schema（仅调用一次）。"""
        if self._enable_wal:
            try:
                await conn.execute(text("PRAGMA journal_mode=WAL;"))
                await conn.execute(text("PRAGMA synchronous=NORMAL;"))
                await conn.execute(text("PRAGMA foreign_keys=ON;"))
            except Exception as e:
                logger.warning("BaseSqliteStore: pragma skipped: {}", e)

        self._define_schema(conn)
        await conn.commit()
        logger.debug("BaseSqliteStore: schema initialized for {}", self._resolved_path)

    async def close(self) -> None:
        """关闭引擎（进程退出时调用）。"""
        if self._resolved_path in self._engines:
            await self._engines[self._resolved_path].dispose()
            del self._engines[self._resolved_path]
            logger.debug("BaseSqliteStore: engine disposed for {}", self._resolved_path)
