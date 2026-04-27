"""SprintCycle 集成测试

注意：此文件包含旧版本的集成测试，某些模块已迁移或重构。
如需运行完整的集成测试，请使用:
    pytest tests/test_chorus.py tests/test_sprint_chain.py tests/test_optimizations.py tests/test_core.py tests/test_models.py -v
"""
import pytest

def test_integration_skip():
    """跳过旧的集成测试（模块已重构）"""
    pytest.skip("Integration tests require refactoring for v4.8 architecture")
