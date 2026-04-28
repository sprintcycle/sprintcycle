"""
GEPA 客户端测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sprintcycle.evolution.client import GEPAClient
from sprintcycle.evolution.types import Gene, GeneType, Variation, VariationType, SprintContext


class MockConfig:
    """模拟配置"""
    def __init__(self):
        self.cache_dir = "./test_cache"
        self.pareto_dimensions = ["correctness", "performance", "stability"]
        self.llm_provider = "deepseek"
        self.llm_model = "deepseek-reasoner"
        self.llm_api_key = "test-key"
        self.llm_api_base = None


@pytest.fixture
def gepa_client():
    """创建 GEPA 客户端（禁用 Hermes）"""
    config = MockConfig()
    with patch.object(GEPAClient, '_check_hermes_availability', return_value=False):
        client = GEPAClient(config)
        return client


@pytest.fixture
def sample_context():
    """创建示例 Sprint 上下文"""
    return SprintContext(
        sprint_id="sprint-001",
        sprint_number=1,
        goal="优化代码性能",
        current_metrics={"success_rate": 0.8},
    )


@pytest.fixture
def sample_variations():
    """创建示例变体列表"""
    return [
        Variation(
            id="var_1",
            gene_id="gene_1",
            variation_type=VariationType.POINT,
            original_content="def foo(): pass",
            modified_content="def foo(): return 1",
            change_summary="添加返回值",
            risk_level="low",
        ),
        Variation(
            id="var_2",
            gene_id="gene_1",
            variation_type=VariationType.BLOCK,
            original_content="def foo(): pass",
            modified_content="def foo():\n    try:\n        pass\n    except: pass",
            change_summary="添加异常处理",
            risk_level="medium",
        ),
    ]


class TestGEPAClientInit:
    """GEPAClient 初始化测试"""

    def test_init_without_hermes(self):
        """测试无 Hermes 库初始化"""
        config = MockConfig()
        with patch.object(GEPAClient, '_check_hermes_availability', return_value=False):
            client = GEPAClient(config)
            assert not client._hermes_available


class TestGEPAClientVary:
    """GEPAClient.vary 测试"""

    @pytest.mark.asyncio
    async def test_vary_fallback(self, gepa_client, sample_context):
        """测试 fallback 变异"""
        result = await gepa_client.vary(
            code="def foo(): pass",
            context=sample_context,
            goal="优化代码",
            max_variations=3,
        )
        assert len(result) == 3
        assert all(isinstance(v, Variation) for v in result)

    @pytest.mark.asyncio
    async def test_vary_respects_max(self, gepa_client, sample_context):
        """测试最大变体数量限制"""
        result = await gepa_client.vary(
            code="def foo(): pass",
            context=sample_context,
            goal="优化代码",
            max_variations=2,
        )
        assert len(result) <= 2


class TestGEPAClientSelect:
    """GEPAClient.select 测试"""

    @pytest.mark.asyncio
    async def test_select_empty(self, gepa_client):
        """测试空变体列表"""
        result = await gepa_client.select([], [])
        assert result == []

    @pytest.mark.asyncio
    async def test_select_pareto_frontier(self, gepa_client, sample_variations):
        """测试 Pareto 前沿选择"""
        fitness_scores = [
            {"correctness": 0.9, "performance": 0.8, "stability": 0.7},
            {"correctness": 0.5, "performance": 0.6, "stability": 0.5},
        ]
        result = await gepa_client.select(sample_variations, fitness_scores)
        assert len(result) <= len(sample_variations)


class TestGEPAClientInherit:
    """GEPAClient.inherit 测试"""

    @pytest.mark.asyncio
    async def test_inherit_fallback(self, gepa_client, sample_context):
        """测试 fallback 遗传"""
        genes = [
            Gene(
                id="gene_1",
                type=GeneType.CODE,
                content="def foo(): pass",
                fitness_scores={"correctness": 0.8},
            )
        ]
        result = await gepa_client.inherit(genes, sample_context)
        assert len(result) == 1
        assert result[0].version == 2  # 版本应该增加

    @pytest.mark.asyncio
    async def test_inherit_empty_genes(self, gepa_client, sample_context):
        """测试空基因列表"""
        result = await gepa_client.inherit([], sample_context)
        assert result == []


class TestGEPAClientReflect:
    """GEPAClient.reflect 测试"""

    @pytest.mark.asyncio
    async def test_reflect_empty_failures(self, gepa_client, sample_context):
        """测试空失败列表"""
        result = await gepa_client.reflect(
            failed_variations=[],
            execution_results=[],
            context=sample_context,
        )
        assert "lessons_learned" in result
        assert "improvement_suggestions" in result
        assert "root_causes" in result
        assert "confidence_adjustments" in result

    @pytest.mark.asyncio
    async def test_reflect_syntax_error(self, gepa_client, sample_context, sample_variations):
        """测试语法错误反思"""
        execution_results = [
            {"success": False, "error_type": "syntax_error", "message": "Invalid syntax"},
        ]
        result = await gepa_client.reflect(
            failed_variations=[sample_variations[0]],
            execution_results=execution_results,
            context=sample_context,
        )
        assert len(result["lessons_learned"]) > 0
        assert any("语法错误" in lesson for lesson in result["lessons_learned"])
        assert sample_variations[0].id in result["confidence_adjustments"]

    @pytest.mark.asyncio
    async def test_reflect_runtime_error(self, gepa_client, sample_context, sample_variations):
        """测试运行时错误反思"""
        execution_results = [
            {"success": False, "error_type": "runtime_error", "message": "Division by zero"},
        ]
        result = await gepa_client.reflect(
            failed_variations=[sample_variations[0]],
            execution_results=execution_results,
            context=sample_context,
        )
        assert any("运行时错误" in lesson for lesson in result["lessons_learned"])

    @pytest.mark.asyncio
    async def test_reflect_performance_degradation(self, gepa_client, sample_context, sample_variations):
        """测试性能下降反思"""
        execution_results = [
            {"success": False, "error_type": "performance_degradation", "message": "Too slow"},
        ]
        result = await gepa_client.reflect(
            failed_variations=[sample_variations[0]],
            execution_results=execution_results,
            context=sample_context,
        )
        assert any("性能" in lesson for lesson in result["lessons_learned"])

    @pytest.mark.asyncio
    async def test_reflect_multiple_failures(self, gepa_client, sample_context, sample_variations):
        """测试多个失败统计"""
        execution_results = [
            {"success": False, "error_type": "syntax_error"},
            {"success": False, "error_type": "syntax_error"},
            {"success": False, "error_type": "runtime_error"},
        ]
        result = await gepa_client.reflect(
            failed_variations=sample_variations[:3],
            execution_results=execution_results,
            context=sample_context,
        )
        assert any("3" in lesson for lesson in result["lessons_learned"])

    @pytest.mark.asyncio
    async def test_reflect_high_failure_rate(self, gepa_client, sample_context):
        """测试高失败率建议"""
        variations = [
            Variation(
                id=f"var_{i}",
                gene_id="gene_1",
                variation_type=VariationType.POINT,
                original_content="code",
                modified_content="new_code",
                change_summary="test",
            )
            for i in range(5)
        ]
        execution_results = [{"success": False, "error_type": "unknown"} for _ in range(5)]
        result = await gepa_client.reflect(
            failed_variations=variations,
            execution_results=execution_results,
            context=sample_context,
        )
        assert any("回滚" in s for s in result["improvement_suggestions"])


class TestGEPAClientCheckpoint:
    """GEPAClient 检查点测试"""

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, gepa_client, tmp_path):
        """测试保存检查点"""
        gepa_client.cache_dir = tmp_path
        data = {"key": "value", "number": 42}
        await gepa_client.save_checkpoint("test-sprint", data)

        checkpoint_file = tmp_path / "test-sprint.json"
        assert checkpoint_file.exists()

    @pytest.mark.asyncio
    async def test_load_checkpoint(self, gepa_client, tmp_path):
        """测试加载检查点"""
        gepa_client.cache_dir = tmp_path

        # 先保存
        data = {"key": "value", "number": 42}
        await gepa_client.save_checkpoint("test-sprint", data)

        # 再加载
        loaded = await gepa_client.load_checkpoint("test-sprint")
        assert loaded is not None
        assert loaded["key"] == "value"
        assert loaded["number"] == 42

    @pytest.mark.asyncio
    async def test_load_nonexistent_checkpoint(self, gepa_client, tmp_path):
        """测试加载不存在的检查点"""
        gepa_client.cache_dir = tmp_path
        result = await gepa_client.load_checkpoint("nonexistent")
        assert result is None


class TestGEPAClientReflectionCache:
    """反思缓存测试"""

    @pytest.mark.asyncio
    async def test_save_and_load_reflection(self, gepa_client, sample_context, tmp_path):
        """测试保存和加载反思结果"""
        gepa_client.cache_dir = tmp_path
        reflection_data = {
            "lessons_learned": ["lesson 1", "lesson 2"],
            "root_causes": ["cause 1"],
            "improvement_suggestions": ["suggestion 1"],
            "confidence_adjustments": {"var_1": 0.2},
        }

        gepa_client._save_reflection_cache("sprint-001", reflection_data)
        loaded = await gepa_client.load_reflection("sprint-001")

        assert loaded is not None
        assert loaded["lessons_learned"] == ["lesson 1", "lesson 2"]

    @pytest.mark.asyncio
    async def test_load_nonexistent_reflection(self, gepa_client):
        """测试加载不存在的反思"""
        result = await gepa_client.load_reflection("nonexistent")
        assert result is None
