"""configure_default_store / get_state_store 与 RollbackManager 索引加载。"""

from pathlib import Path

import pytest

from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.execution.rollback import RollbackManager
from sprintcycle.infrastructure.persistence.state.state_store import (
    configure_default_store,
    get_state_store,
    reset_default_state_store,
)


@pytest.fixture(autouse=True)
def _reset_store():
    reset_default_state_store()
    yield
    reset_default_state_store()


def test_get_state_store_warns_when_store_dir_ignored_after_configure(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.WARNING)
    configure_default_store(str(tmp_path), RuntimeConfig(storage_backend="json", state_dir=".sprintcycle/state"))
    get_state_store("/nope/ignored")
    assert "get_state_store" in caplog.text and "ignored" in caplog.text.lower()


def test_rollback_manager_loads_index_sync(tmp_path: Path) -> None:
    bk = tmp_path / "backups"
    idx = bk / "index.json"
    bk.mkdir(parents=True, exist_ok=True)
    idx.write_text(
        '{"backups": {}, "file_backups": {}}',
        encoding="utf-8",
    )
    m = RollbackManager(backup_dir=str(bk))
    assert m._backups == {}
    assert m._file_backups == {}
