"""同步 SQLite 存储适配器（用于 CLI/脚本等同步调用场景）。

提供同步版本的 SQLite 操作，内部统一使用 asyncio.run() 桥接。
避免 asyncio.run() 散落在代码各处，便于统一管理和调试。

使用场景：
- CLI 命令
- 同步脚本（如 import_json_state.py）
- 需要在同步上下文中访问 SQLite 的地方

注意：
- 服务层应直接使用 BaseSqliteStore 的 async 接口
- 仅在无法使用 async 的场景使用此适配器
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from sqlalchemy.ext.asyncio import AsyncConnection

from sprintcycle.infrastructure.persistence.base.sqlite_store import BaseSqliteStore


class SyncSqliteStore(BaseSqliteStore):
    """同步 SQLite 存储适配器。

    继承 BaseSqliteStore，提供同步版本的方法。
    内部通过 asyncio.run() 调用异步方法。
    """

    def __init__(self, db_path: str, **kwargs) -> None:
        super().__init__(db_path, **kwargs)
        # 维护一个事件循环引用，避免重复创建
        self._loop = None

    def _run_sync(self, coro) -> Any:
        """统一的 sync→async 桥接方法。"""
        try:
            loop = asyncio.get_running_loop()
            # 如果已有运行中的循环，使用 create_task
            if loop.is_running():
                return asyncio.create_task(coro)
        except RuntimeError:
            pass
        # 否则创建新循环
        return asyncio.run(coro)

    @contextmanager
    def connect(self) -> Iterator[Any]:
        """同步连接上下文管理器。"""
        conn = self._run_sync(super().connect().__aenter__())
        try:
            yield conn
        finally:
            self._run_sync(super().connect().__aexit__(None, None, None))

    def execute(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Sequence[Any]:
        """同步执行查询并返回全部结果行。"""
        return self._run_sync(super().execute(query, params))

    def execute_one(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> Any | None:
        """同步执行查询并返回第一行。"""
        return self._run_sync(super().execute_one(query, params))

    def execute_modify(
        self,
        query: str,
        params: Sequence[Any] | None = None,
    ) -> int:
        """同步执行修改语句，返回影响的行数。"""
        return self._run_sync(super().execute_modify(query, params))

    def close(self) -> None:
        """同步关闭引擎。"""
        self._run_sync(super().close())

    def _define_schema(self, conn: AsyncConnection) -> None:
        """子类必须实现的模板方法。"""
        raise NotImplementedError("Subclasses must implement _define_schema")
