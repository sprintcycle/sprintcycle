"""执行状态规范键与 ``wire_compat`` 读取辅助。"""

from __future__ import annotations

from pathlib import Path

from sprintcycle.execution.state.wire_compat import (
    KEY_PLAN_ID,
    KEY_PLAN_NAME,
    KEY_PLAN_YAML,
    checkpoint_plan_yaml,
    context_plan_id_name,
    dict_plan_name,
    metadata_plan_id,
)


def test_checkpoint_plan_yaml() -> None:
    assert checkpoint_plan_yaml({KEY_PLAN_YAML: "x"}) == "x"
    assert checkpoint_plan_yaml({}) is None
    assert checkpoint_plan_yaml(None) is None


def test_metadata_plan_id() -> None:
    assert metadata_plan_id({}) == "unknown"
    assert metadata_plan_id({KEY_PLAN_ID: "  "}, default="x") == "x"
    assert metadata_plan_id({KEY_PLAN_ID: "rid"}) == "rid"


def test_context_plan_id_name_and_dict_plan_name() -> None:
    rid, name = context_plan_id_name({KEY_PLAN_ID: "a", KEY_PLAN_NAME: "n"})
    assert rid == "a" and name == "n"
    assert dict_plan_name({KEY_PLAN_NAME: "P"}) == "P"
    assert dict_plan_name({}) == ""


def test_init_db_fresh_sqlite(tmp_path: Path) -> None:
    from sprintcycle.persistence.session import create_engine_for_path, init_db

    db = tmp_path / "fresh.sqlite"
    engine = create_engine_for_path(str(db))
    init_db(engine)
    engine.dispose()
