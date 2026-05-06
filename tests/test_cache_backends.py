"""统一缓存抽象与 ExecutionCache 集成。"""

import tempfile
from pathlib import Path

from sprintcycle.cache import DiskCacheBackend, NullCacheBackend, build_cache_backend
from sprintcycle.config.runtime_config import RuntimeConfig
from sprintcycle.execution.cache import ExecutionCache, configure_execution_cache_from_runtime, get_cache, set_cache


def test_disk_cache_backend_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        b = DiskCacheBackend(d, max_entries=10)
        assert b.get("k") is None
        b.set("k", {"a": 1}, expire_seconds=3600)
        assert b.get("k") == {"a": 1}
        assert b.contains("k")
        assert b.delete("k")
        assert b.get("k") is None


def test_null_backend():
    n = NullCacheBackend()
    assert n.get("x") is None
    n.set("x", 1)
    assert n.get("x") is None
    assert n.backend_name == "disabled"


def test_build_cache_backend_disabled():
    r = RuntimeConfig(cache_enabled=False)
    b = build_cache_backend(r, ".")
    assert b.backend_name == "disabled"


def test_execution_cache_wraps_backend():
    with tempfile.TemporaryDirectory() as d:
        ex = ExecutionCache(cache_dir=d, ttl_hours=1, max_entries=5, backend=DiskCacheBackend(d, max_entries=5))
        ex.set("h", {"ok": True})
        assert ex.get("h") == {"ok": True}
        st = ex.stats
        assert st["backend"] == "diskcache"


def test_configure_execution_cache_from_runtime_resets_global():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "proj"
        root.mkdir()
        r = RuntimeConfig(
            cache_enabled=True,
            cache_backend="diskcache",
            cache_dir=str(root / ".sc-cache"),
            cache_max_entries=50,
            cache_default_ttl_hours=12,
        )
        configure_execution_cache_from_runtime(r, str(root))
        c = get_cache()
        c.set("probe", 42, ttl_hours=1)
        assert c.get("probe") == 42
        # restore default-ish singleton for other tests
        set_cache(ExecutionCache())


def test_static_analyzer_tool_cache_uses_execution_cache():
    from sprintcycle.execution.static_analyzer import StaticAnalyzer

    with tempfile.TemporaryDirectory() as td:
        set_cache(ExecutionCache(cache_dir=str(Path(td) / "c")))
        sa = StaticAnalyzer(td)
        _ = sa._is_tool_available("ruff")
        _ = sa._is_tool_available("ruff")
        set_cache(ExecutionCache())
