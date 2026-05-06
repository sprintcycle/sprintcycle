"""Dashboard 配置中心 API。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def dash_client(tmp_path: Path):
    (tmp_path / "sprintcycle.toml").write_text(
        "[project]\npath = \".\"\nparallel_tasks = 2\n",
        encoding="utf-8",
    )
    from sprintcycle.dashboard.server import create_app

    app = create_app(project_path=str(tmp_path))
    with TestClient(app) as client:
        yield client, tmp_path


def test_config_get_and_put_roundtrip(dash_client) -> None:
    client, root = dash_client
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True
    assert isinstance(body.get("data"), dict)
    assert body["data"].get("parallel_tasks") == 2

    r2 = client.put("/api/config", json={"updates": {"max_sprints": 7}})
    assert r2.status_code == 200
    j = r2.json()
    assert j["success"] is True
    assert j["data"].get("max_sprints") == 7

    yaml_path = root / "sprintcycle.runtime.yaml"
    assert yaml_path.is_file()

    r3 = client.get("/api/config")
    assert r3.json()["data"].get("max_sprints") == 7


def test_config_schema(dash_client) -> None:
    client, _ = dash_client
    r = client.get("/api/config/schema")
    assert r.status_code == 200
    j = r.json()
    assert j.get("success") is True
    assert j["data"].get("type") == "object"


def test_config_history_after_put(dash_client) -> None:
    client, _ = dash_client
    client.put("/api/config", json={"updates": {"verbose": True}})
    r = client.get("/api/config/history")
    assert r.status_code == 200
    hist = r.json().get("data", [])
    assert isinstance(hist, list)
    assert any(h.get("source") == "api_put" for h in hist)


def test_config_reload(dash_client) -> None:
    client, _ = dash_client
    r = client.post("/api/config/reload", json={})
    assert r.status_code == 200
    assert r.json().get("success") is True


def test_config_import(dash_client) -> None:
    client, _ = dash_client
    r = client.post(
        "/api/config/import",
        json={"config": {"parallel_tasks": 4, "max_sprints": 9}},
    )
    assert r.status_code == 200
    assert r.json()["data"].get("parallel_tasks") == 4
