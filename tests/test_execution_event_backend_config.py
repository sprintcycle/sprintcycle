"""execution_event_backend：配置选择 sqlite / memory。"""

import pytest

from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.execution.core.events import (
    EventBus,
    ensure_default_execution_event_backend_for_project,
    get_execution_event_backend,
)
from sprintcycle.execution.state.sqlite_event_backend import SQLiteMQEventBackend


@pytest.fixture
def clear_global_backend(monkeypatch):
    import sprintcycle.execution.core.events as ev

    monkeypatch.setattr(ev, "_default_execution_event_backend", None)
    yield
    monkeypatch.setattr(ev, "_default_execution_event_backend", None)


def test_ensure_sqlite_by_default(clear_global_backend, tmp_path):
    cfg = RuntimeConfig()
    ensure_default_execution_event_backend_for_project(str(tmp_path), cfg)
    assert isinstance(get_execution_event_backend(), SQLiteMQEventBackend)


def test_ensure_memory_when_config(clear_global_backend, tmp_path):
    cfg = RuntimeConfig.merge({"execution_event_backend": "memory"}, RuntimeConfig())
    ensure_default_execution_event_backend_for_project(str(tmp_path), cfg)
    assert isinstance(get_execution_event_backend(), EventBus)


def test_invalid_backend_falls_back_to_sqlite(clear_global_backend, tmp_path):
    cfg = RuntimeConfig.merge({"execution_event_backend": "kafka"}, RuntimeConfig())
    ensure_default_execution_event_backend_for_project(str(tmp_path), cfg)
    assert isinstance(get_execution_event_backend(), SQLiteMQEventBackend)
