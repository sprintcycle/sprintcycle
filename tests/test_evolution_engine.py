"""
进化引擎测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sprintcycle.evolution.engine import EvolutionEngine
from sprintcycle.evolution.types import Gene, GeneType, Variation, VariationType, SprintContext, EvolutionMetrics


class MockConfig:
    """模拟配置"""
    def __init__(self):
        self.llm_provider = "deepseek"
        self.llm_model = "deepseek-reasoner"
        self.llm_api_key = "test-key"
        self.llm_api_base = None
        self.cache_dir = "./test_cache"
        self.pareto_dimensions = ["correctness", "performance", "stability"]
        self.inheritance_enabled = True


@pytest.fixture
def evolution_engine():
    """创建进化引擎"""
    with patch("sprintcycle.evolution.engine.GEPAClient"):
        return EvolutionEngine(MockConfig())


@pytest.fixture
def sample_context():
    """创建示例上下文"""
    return SprintContext(
        sprint_id="sprint-001",
        sprint_number=1,
        goal="优化代码",
        current_metrics={"success_rate": 0.8},
    )


@pytest.fixture
def sample_variations():
    """创建示例变体"""
    return [
        Variation(
            id=f"var_{i}",
            gene_id="gene_1",
            variation_type=VariationType.POINT,
            original_content="def foo(): pass",
            modified_content=f"def foo(): return {i}",
            change_summary=f"返回 {i}",
            risk_level="low",
            predicted_fitness={"correctness": 0.5 + i * 0.1, "performance": 0.6, "stability": 0.7},
        )
        for i in range(3)
    ]


class TestEvolutionEngineInit:
    """EvolutionEngine 初始化测试"""

    def test_init_creates_client(self):
        """测试初始化创建客户端"""
        with patch("sprintcycle.evolution.engine.GEPAClient") as MockClient:
            engine = EvolutionEngine(MockConfig())
            MockClient.assert_called_once()

    def test_init_empty_gene_pool(self):
        """测试初始化空基因池"""
        with patch("sprintcycle.evolution.engine.GEPAClient"):
            engine = EvolutionEngine(MockConfig())
            assert engine.gene_pool == []
            assert engine.history == []

    def test_init_metrics(self):
        """测试初始化指标"""
        with patch("sprintcycle.evolution.engine.GEPAClient"):
            engine = EvolutionEngine(MockConfig())
            assert engine.metrics is not None
            assert engine.metrics.generations == 0


class TestEvolutionEngineCallbacks:
    """EvolutionEngine 回调测试"""

    def test_register_callbacks(self, evolution_engine):
        """测试注册回调"""
        callbacks = {
            "on_variation": lambda x: x,
            "on_selection": lambda x: x,
            "on_inheritance": lambda x: x,
        }
        evolution_engine.register_callbacks(**callbacks)
        assert evolution_engine._callbacks["on_variation"] is not None
        assert evolution_engine._callbacks["on_selection"] is not None
        assert evolution_engine._callbacks["on_inheritance"] is not None


class TestEvolutionEngineShouldEvolve:
    """should_evolve 测试"""

    def test_should_evolve_low_success_rate(self, evolution_engine):
        """测试低成功率触发进化"""
        metrics = {"success_rate": 0.5, "error_count": 5, "avg_duration": 300}
        assert evolution_engine.should_evolve(metrics)

    def test_should_evolve_high_error_count(self, evolution_engine):
        """测试高错误数触发进化"""
        metrics = {"success_rate": 0.9, "error_count": 15, "avg_duration": 300}
        assert evolution_engine.should_evolve(metrics)

    def test_should_evolve_high_duration(self, evolution_engine):
        """测试高耗时触发进化"""
        metrics = {"success_rate": 0.9, "error_count": 5, "avg_duration": 700}
        assert evolution_engine.should_evolve(metrics)

    def test_should_not_evolve(self, evolution_engine):
        """测试不需要进化"""
        metrics = {"success_rate": 0.9, "error_count": 5, "avg_duration": 300}
        assert not evolution_engine.should_evolve(metrics)


class TestEvolutionEngineGenePool:
    """基因池管理测试"""

    def test_add_gene(self, evolution_engine):
        """测试添加基因"""
        gene = Gene(
            id="gene_1",
            type=GeneType.CODE,
            content="def foo(): pass",
            fitness_scores={"correctness": 0.8},
        )
        evolution_engine.add_gene(gene)
        assert len(evolution_engine.gene_pool) == 1
        assert evolution_engine.metrics.total_genes == 1

    def test_get_elite_genes(self, evolution_engine):
        """测试获取精英基因"""
        genes = [
            Gene(id=f"gene_{i}", type=GeneType.CODE, content="code",
                 fitness_scores={"correctness": 0.5 + i * 0.1})
            for i in range(5)
        ]
        for g in genes:
            evolution_engine.add_gene(g)

        elite = evolution_engine._get_elite_genes(top_k=2)
        assert len(elite) == 2
        assert elite[0].fitness_scores["correctness"] >= elite[1].fitness_scores["correctness"]

    def test_get_best_genes(self, evolution_engine):
        """测试获取最佳基因"""
        genes = [
            Gene(id=f"gene_{i}", type=GeneType.CODE, content="code",
                 fitness_scores={"correctness": 0.5 + i * 0.1})
            for i in range(10)
        ]
        for g in genes:
            evolution_engine.add_gene(g)

        best = evolution_engine.get_best_genes(top_k=3)
        assert len(best) == 3

    def test_get_pareto_front(self, evolution_engine):
        """测试获取 Pareto 前沿"""
        genes = [
            Gene(id="gene_1", type=GeneType.CODE, content="code",
                 fitness_scores={"correctness": 0.9, "performance": 0.5}),
            Gene(id="gene_2", type=GeneType.CODE, content="code",
                 fitness_scores={"correctness": 0.5, "performance": 0.9}),
            Gene(id="gene_3", type=GeneType.CODE, content="code",
                 fitness_scores={"correctness": 0.6, "performance": 0.6}),
        ]
        for g in genes:
            evolution_engine.add_gene(g)

        pareto = evolution_engine.get_pareto_front()
        assert len(pareto) >= 1


class TestEvolutionEngineCheckpoint:
    """检查点测试"""

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, evolution_engine, tmp_path):
        """测试保存检查点"""
        evolution_engine.client.cache_dir = tmp_path
        gene = Gene(id="gene_1", type=GeneType.CODE, content="code",
                   fitness_scores={"correctness": 0.8})
        evolution_engine.add_gene(gene)

        await evolution_engine._save_checkpoint("test-sprint")
        evolution_engine.client.save_checkpoint.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_checkpoint(self, evolution_engine):
        """测试加载检查点"""
        evolution_engine.client.load_checkpoint = AsyncMock(return_value={
            "gene_pool": [
                {"id": "gene_1", "type": "code", "content": "code",
                 "fitness_scores": {"correctness": 0.8}, "metadata": {},
                 "parent_ids": [], "version": 1}
            ],
            "metrics": {"total_genes": 1},
        })

        result = await evolution_engine.load_checkpoint("test-sprint")
        assert result
        assert len(evolution_engine.gene_pool) == 1

    @pytest.mark.asyncio
    async def test_load_checkpoint_failure(self, evolution_engine):
        """测试加载检查点失败"""
        evolution_engine.client.load_checkpoint = AsyncMock(return_value=None)
        result = await evolution_engine.load_checkpoint("nonexistent")
        assert not result
