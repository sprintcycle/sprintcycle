"""将 JSON ``StateStore`` 目录下的执行记录导入 SQLite。"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def import_json_executions_to_sqlite(
    json_state_dir: Union[str, Path],
    sqlite_db: Union[str, Path],
) -> int:
    """
    扫描 ``json_state_dir`` 下 ``*.json``，写入 ``sqlite_db``（upsert）。

    Returns:
        成功导入（写入）条数。
    """
    from ..execution.sqlite_state_store import SqliteExecutionStore
    from ..execution.state_store import ExecutionState

    src = Path(json_state_dir).expanduser().resolve()
    if not src.is_dir():
        logger.warning("import_json: 不是目录: %s", src)
        return 0
    store = SqliteExecutionStore(str(Path(sqlite_db).expanduser().resolve()))
    n = 0
    for path in sorted(src.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            state = ExecutionState.from_dict(data)
            store.save(state)
            n += 1
        except Exception as e:
            logger.warning("跳过 %s: %s", path.name, e)
    return n
