"""
依赖注入示例 - 展示如何使用新的 DI Container

本文件展示：
1. 如何使用 Container 获取服务
2. 如何使用 Override 进行测试 Mock
3. 如何使用配置注入
4. 生命周期管理（Singleton vs Factory）
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from sprintcycle.application.composition.di_container import (
    Container,
    create_container,
    container,
    CoreInfrastructureContainer,
    GovernanceAdaptersContainer,
)
from sprintcycle.application.composition.di_bridge import (
    get_cache_backend,
    get_state_store,
    get_runtime_config,
)


def test_container_creation():
    """测试容器创建和配置"""
    test_container = create_container(
        project_path="/tmp/test_project",
        state_store_dir="/tmp/test_state",
    )

    assert test_container is not None
    assert test_container.config.project_path() == "/tmp/test_project"
    print("✓ 容器创建成功")


def test_get_cache_backend():
    """测试获取缓存后端"""
    cache = get_cache_backend()

    assert cache is not None
    assert hasattr(cache, 'get')
    assert hasattr(cache, 'set')
    print(f"✓ 缓存后端类型: {type(cache).__name__}")


def test_singleton_lifecycle():
    """测试单例生命周期 - 同一实例"""
    cache1 = get_cache_backend()
    cache2 = get_cache_backend()

    assert cache1 is cache2
    print("✓ Singleton 生命周期正确：多次获取返回同一实例")


def test_override_for_testing():
    """测试 Override 功能 - Mock 测试"""
    class MockCache:
        def __init__(self):
            self._data = {}

        def get(self, key: str) -> Any:
            return self._data.get(key)

        def set(self, key: str, value: Any, *, expire_seconds: int = None) -> None:
            self._data[key] = value

        def delete(self, key: str) -> bool:
            if key in self._data:
                del self._data[key]
                return True
            return False

        def contains(self, key: str) -> bool:
            return key in self._data

        def clear(self) -> None:
            self._data.clear()

        def __len__(self) -> int:
            return len(self._data)

        @property
        def backend_name(self) -> str:
            return "mock"

    mock_cache = MockCache()

    with container.cache_backend.override(mock_cache):
        cache = get_cache_backend()
        assert cache is mock_cache
        print("✓ Override 成功：Mock 缓存被注入")

    cache_after = get_cache_backend()
    assert cache_after is not mock_cache
    print("✓ Override 正确退出：原始缓存恢复")


def test_configuration_injection():
    """测试配置注入"""
    test_container = create_container(
        project_path="/tmp/test_project",
    )

    config = test_container.runtime_config()

    assert config is not None
    print(f"✓ 配置注入成功: {type(config).__name__}")


def test_governance_adapters():
    """测试治理适配器获取"""
    archguard = container.governance.archguard_adapter()
    ruff = container.governance.ruff_adapter()

    assert archguard is not None
    assert ruff is not None
    assert archguard is not ruff
    print(f"✓ 治理适配器创建成功")


def test_subcontainers():
    """测试子容器隔离"""
    infra = container.infrastructure
    governance = container.governance

    assert infra is not None
    assert governance is not None
    assert infra.config is governance.config
    print("✓ 子容器结构正确")


if __name__ == "__main__":
    print("=" * 60)
    print("依赖注入示例测试")
    print("=" * 60)
    print()

    test_container_creation()
    test_get_cache_backend()
    test_singleton_lifecycle()
    test_configuration_injection()
    test_governance_adapters()
    test_subcontainers()

    print()
    print("=" * 60)
    print("所有示例测试通过！")
    print("=" * 60)
