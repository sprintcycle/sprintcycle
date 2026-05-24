"""
基于 SQLite + SQLAlchemy 的执行状态存储（与 StateStore 方法签名对齐）。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from sprintcycle.application.release_plan.payload_keys import checkpoint_plan_yaml
from sprintcycle.infrastructure.persistence.models import ExecutionRow
from sprintcycle.infrastructure.persistence.session import create_engine_for_path, init_db
from sprintcycle.execution.core.sprint_types import ExecutionStatus
from .machine import validate_transition
from .state_store import ExecutionState


class SqliteExecutionStore:
    """与 ``StateStore`` 相同的对外 API，便于 ``get_state_store`` 切换后端。"""
