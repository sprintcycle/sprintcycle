from pathlib import Path

from sprintcycle.infrastructure.integrations.langgraph.checkpoint import LocalJsonCheckpointStore


def test_local_json_checkpoint_store_roundtrip(tmp_path: Path):
    store = LocalJsonCheckpointStore(checkpoint_dir=str(tmp_path / "checkpoints"))
    key = "thread-123"
    state = {"intent": "build", "attempt": 1}

    store.save(key, state)

    assert store.load(key) == state
