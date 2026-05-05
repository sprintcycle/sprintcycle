"""pytest 全局 fixtures。"""

from __future__ import annotations

import pytest
from loguru import logger


@pytest.fixture(autouse=True)
def _loguru_sink_for_caplog(caplog: pytest.LogCaptureFixture) -> None:
    """把 loguru 输出接到 caplog.handler，保留对 ``caplog.text`` 的断言能力。"""
    caplog.set_level("DEBUG")
    handler_id = logger.add(caplog.handler, format="{message}", level="DEBUG")
    yield
    try:
        logger.remove(handler_id)
    except ValueError:
        pass
