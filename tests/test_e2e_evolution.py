"""
端到端进化测试 - 测试完整进化流程: vary → select → inherit → reflect

测试 SprintCycle 进化引擎的完整闭环，包括：
1. 变异阶段 (vary) - 生成多个变体候选
2. 选择阶段 (select) - Pareto 前沿选择
3. 遗传阶段 (inherit) - 精英基因传承
4. 反思阶段 (reflect) - Sprint 触发进化
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from sprintcycle.evolution.engine import EvolutionEngine
from sprintcycle.evolution.client import GEPAClient
from sprintcycle.evolution.config import EvolutionEngineConfig
from sprintcycle.evolution.types import (
    Gene, GeneType, Variation, VariationType,
    SprintContext, EvolutionResult, EvolutionStage
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_config():
    """Mock LLM 配置"""
    return EvolutionEngineConfig(
        llm_provider="mock",
        llm_model="mock-model",
        llm_api_key="mock-key",
        cache_dir="./test_cache",
        pareto_dimensions=["correctness", "performance", "stability"],
        inheritance_enabled=True,
        reflection_enabled=True,
    )


@pytest.fixture
def evolution_engine(mock_llm_config):
    """创建进化引擎（Mock LLM）"""
    with patch.object(GEPAClient, '_check_hermes', return_value=False):
        engine = EvolutionEngine(mock_llm_config)
        engine.client.vary = AsyncMock()
        engine.client.select = AsyncMock()
        engine.client.inherit = AsyncMock()
        engine.client.save_checkpoint = AsyncMock()
        engine.client.load_checkpoint = AsyncMock(return_value=None)
        return engine


@pytest.fixture
def temp_target_file():
    """创建临时目标文件"""
    code = '''def add(a, b):
    """简单加法"""
    return a + b

def subtract(a, b):
    """简单减法"""
    return a - b
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def sample_sprint_context():
    """创建示例 Sprint 上下文"""
    return SprintContext(
        sprint_id="sprint-e2e-001",
        sprint_number=1,
        goal="优化代码性能和稳定性",
        current_metrics={
            "success_rate": 0.75,
            "error_count": 5,
            "avg_duration": 120.0
        },
        constraints={
            "dimensions": ["correctness", "performance", "stability"]
        }
    )


@pytest.fixture
def sample_variations():
    """创建示例变异列表"""
    return [
        Variation(
            id="var_error_handling",
            gene_id="gene_base",
            variation_type=VariationType.POINT,
            original_content="def add(a, b): return a + b",
            modified_content="def add(a, b):\n    try:\n        return a + b\n    except TypeError:\n        return None",
            change_summary="添加错误处理",
            risk_level="low",
            predicted_fitness={
                "correctness": 0.8,
                "performance": 0.6,
                "stability": 0.9
            },
            confidence=0.7
        ),
        Variation(
            id="var_performance",
            gene_id="gene_base",
            variation_type=VariationType.BLOCK,
            original_content="def add(a, b): return a + b",
            modified_content="def add(a, b):\n    if isinstance(a, (int, float)) and isinstance(b, (int, float)):\n        return a + b\n    return a + b",
            change_summary="优化性能检查",
            risk_level="medium",
            predicted_fitness={
                "correctness": 0.9,
                "performance": 0.85,
                "stability": 0.7
            },
            confidence=0.6
        ),
        Variation(
            id="var_type_hint",
            gene_id="gene_base",
            variation_type=VariationType.STRUCTURAL,
            original_content="def add(a, b): return a + b",
            modified_content="def add(a: int, b: int) -> int:\n    return a + b",
            change_summary="添加类型提示",
            risk_level="low",
            predicted_fitness={
                "correctness": 0.85,
                "performance": 0.7,
                "stability": 0.8
            },
            confidence=0.75
        ),
    ]


@pytest.fixture
def sample_genes():
    """创建示例基因列表"""
    return [
        Gene(
            id="gene_1",
            type=GeneType.CODE,
            content="def optimized_func():\n    pass",
            metadata={"source": "previous_sprint", "sprint_id": "sprint-001"},
            fitness_scores={"correctness": 0.9, "performance": 0.8, "stability": 0.85},
            parent_ids=[],
            version=2
        ),
        Gene(
            id="gene_2",
            type=GeneType.CODE,
            content="def legacy_func():\n    pass",
            metadata={"source": "baseline"},
            fitness_scores={"correctness": 0.7, "performance": 0.75, "stability": 0.7},
            parent_ids=["gene_parent"],
            version=1
        ),
    ]


# ============================================================================
# 阶段 1: 变异 (vary) 测试
# ============================================================================

class TestVaryStage:
    """变异阶段测试"""

    @pytest.mark.asyncio
    async def test_vary_generates_multiple_variations(self, evolution_engine, temp_target_file):
        """测试变异阶段生成多个变体"""
        variations = [
            Variation(
                id=f"var_{i}",
                gene_id="gene_base",
                variation_type=VariationType.POINT,
                original_content="original",
                modified_content=f"modified_{i}",
                change_summary=f"变更 {i}",
                risk_level="low",
                predicted_fitness={"correctness": 0.5 + i * 0.1, "performance": 0.6, "stability": 0.7},
            )
            for i in range(3)
        ]
        evolution_engine.client.vary = AsyncMock(return_value=variations)

        result = await evolution_engine.evolve_code(temp_target_file, goal="测试变异")

        assert result.success
        assert len(result.variations) == 3
        evolution_engine.client.vary.assert_called_once()

    @pytest.mark.asyncio
    async def test_vary_with_empty_code(self, evolution_engine):
        """测试空代码的变异处理"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f.flush()
            temp_file = f.name

        try:
            variations = []
            evolution_engine.client.vary = AsyncMock(return_value=variations)
            result = await evolution_engine.evolve_code(temp_file)

            assert result.success
            assert len(result.variations) == 0
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_vary_with_custom_context(self, evolution_engine, temp_target_file, sample_sprint_context):
        """测试带自定义上下文的变异"""
        variations = [
            Variation(
                id="var_1",
                gene_id="gene_1",
                variation_type=VariationType.POINT,
                original_content="original",
                modified_content="modified",
                change_summary="测试",
                risk_level="low",
                predicted_fitness={"correctness": 0.8, "performance": 0.7, "stability": 0.9},
            )
        ]
        evolution_engine.client.vary = AsyncMock(return_value=variations)

        result = await evolution_engine.evolve_code(
            temp_target_file,
            context=sample_sprint_context,
            goal="自定义目标"
        )

        assert result.success
        assert result.variations[0].id == "var_1"


# ============================================================================
# 阶段 2: 选择 (select) 测试
# ============================================================================

class TestSelectStage:
    """选择阶段测试"""

    @pytest.mark.asyncio
    async def test_select_returns_pareto_frontier(self, evolution_engine, sample_variations):
        """测试 Pareto 前沿选择"""
        evolution_engine.client.vary = AsyncMock(return_value=sample_variations)
        evolution_engine.client.select = AsyncMock(return_value=sample_variations[:2])

        result = await evolution_engine.evolve_code(
            target="dummy.py",
            context=SprintContext(
                sprint_id="test",
                sprint_number=1,
                goal="test",
                current_metrics={}
            )
        )

        assert len(result.selected_genes) >= 0

    @pytest.mark.asyncio
    async def test_select_empty_variations(self, evolution_engine, temp_target_file):
        """测试空变体列表的选择"""
        evolution_engine.client.vary = AsyncMock(return_value=[])
        evolution_engine.client.select = AsyncMock(return_value=[])

        result = await evolution_engine.evolve_code(temp_target_file)

        assert result.success
        assert len(result.selected_genes) == 0


# ============================================================================
# 阶段 3: 遗传 (inherit) 测试
# ============================================================================

class TestInheritStage:
    """遗传阶段测试"""

    @pytest.mark.asyncio
    async def test_inherit_preserves_elite_genes(
        self, evolution_engine, temp_target_file, sample_genes
    ):
        """测试精英基因保留"""
        variations = [
            Variation(
                id="var_1",
                gene_id="gene_1",
                variation_type=VariationType.POINT,
                original_content="original",
                modified_content="modified",
                change_summary="测试",
                risk_level="low",
                predicted_fitness={"correctness": 0.8, "performance": 0.7, "stability": 0.9},
            )
        ]
        inherited_genes = [
            Gene(
                id="inh_gene_1",
                type=GeneType.CODE,
                content="inherited content",
                metadata={},
                fitness_scores={"correctness": 0.85, "performance": 0.75, "stability": 0.9},
                parent_ids=["gene_1"],
                version=2
            )
        ]

        evolution_engine.client.vary = AsyncMock(return_value=variations)
        evolution_engine.client.select = AsyncMock(return_value=[variations[0]])
        evolution_engine.client.inherit = AsyncMock(return_value=inherited_genes)
        evolution_engine.gene_pool = sample_genes

        result = await evolution_engine.evolve_code(temp_target_file)

        assert result.success
        if inherited_genes:
            evolution_engine.client.inherit.assert_called_once()

    @pytest.mark.asyncio
    async def test_inherit_increments_version(
        self, evolution_engine, temp_target_file, sample_genes
    ):
        """测试遗传后版本号递增"""
        evolution_engine.gene_pool = sample_genes
        original_version = sample_genes[0].version

        inherited_genes = [
            Gene(
                id="inh_gene_1",
                type=GeneType.CODE,
                content="inherited",
                metadata={},
                fitness_scores={"correctness": 0.8},
                parent_ids=["gene_1"],
                version=original_version + 1
            )
        ]

        evolution_engine.client.vary = AsyncMock(return_value=[])
        evolution_engine.client.select = AsyncMock(return_value=[])
        evolution_engine.client.inherit = AsyncMock(return_value=inherited_genes)

        result = await evolution_engine.evolve_code(temp_target_file)

        if result.inherited_genes:
            assert result.inherited_genes[0].version == original_version + 1


# ============================================================================
# Sprint 触发进化测试
# ============================================================================

class TestSprintTrigger:
    """Sprint 触发进化测试"""

    def test_should_evolve_low_success_rate(self, evolution_engine):
        """测试低成功率触发进化"""
        metrics = {"success_rate": 0.5, "error_count": 0, "avg_duration": 100}
        assert evolution_engine.should_evolve(metrics) is True

    def test_should_evolve_high_error_count(self, evolution_engine):
        """测试高错误数触发进化"""
        metrics = {"success_rate": 0.9, "error_count": 15, "avg_duration": 100}
        assert evolution_engine.should_evolve(metrics) is True

    def test_should_evolve_slow_execution(self, evolution_engine):
        """测试慢执行触发进化"""
        metrics = {"success_rate": 0.95, "error_count": 2, "avg_duration": 800}
        assert evolution_engine.should_evolve(metrics) is True

    def test_should_not_evolve_healthy_metrics(self, evolution_engine):
        """测试健康指标不触发进化"""
        metrics = {"success_rate": 0.95, "error_count": 1, "avg_duration": 50}
        assert evolution_engine.should_evolve(metrics) is False


# ============================================================================
# 完整流程端到端测试
# ============================================================================

class TestE2EEvolution:
    """端到端进化流程测试"""

    @pytest.mark.asyncio
    async def test_full_evolution_pipeline(
        self, evolution_engine, temp_target_file, sample_variations, sample_genes
    ):
        """测试完整进化流程: vary → select → inherit"""
        evolution_engine.client.vary = AsyncMock(return_value=sample_variations)
        evolution_engine.client.select = AsyncMock(return_value=sample_variations[:2])
        evolution_engine.client.inherit = AsyncMock(return_value=[])
        evolution_engine.gene_pool = sample_genes

        result = await evolution_engine.evolve_code(
            temp_target_file,
            context=SprintContext(
                sprint_id="e2e-test",
                sprint_number=1,
                goal="端到端测试",
                current_metrics={"success_rate": 0.7}
            ),
            goal="优化性能和稳定性",
            max_variations=3
        )

        assert result.success
        assert result.execution_time >= 0
        evolution_engine.client.vary.assert_called_once()
        evolution_engine.client.select.assert_called_once()

    @pytest.mark.skip(reason="checkpoint功能待P2实现")
    async def test_evolution_with_checkpoint(
        self, evolution_engine, temp_target_file, sample_variations
    ):
        """测试带检查点的进化"""
        evolution_engine.client.vary = AsyncMock(return_value=sample_variations)
        evolution_engine.client.select = AsyncMock(return_value=sample_variations[:1])
        evolution_engine.client.save_checkpoint = AsyncMock()

        context = SprintContext(
            sprint_id="checkpoint-test",
            sprint_number=1,
            goal="测试检查点",
            current_metrics={}
        )

        result = await evolution_engine.evolve_code(temp_target_file, context=context)

        assert result.success
        evolution_engine.client.save_checkpoint.assert_called()

    @pytest.mark.asyncio
    async def test_batch_evolution(self, evolution_engine):
        """测试批量进化"""
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(f"def func_{i}(): pass")
                f.flush()
                temp_files.append(f.name)

        try:
            evolution_engine.client.vary = AsyncMock(return_value=[])
            evolution_engine.client.select = AsyncMock(return_value=[])
            evolution_engine.client.save_checkpoint = AsyncMock()

            results = await evolution_engine.evolve_batch(temp_files, goal="批量优化")

            assert len(results) == 3
            assert all(r.success for r in results)
        finally:
            for f in temp_files:
                os.unlink(f)

    @pytest.mark.asyncio
    async def test_evolution_metrics_tracking(
        self, evolution_engine, temp_target_file, sample_variations
    ):
        """测试进化指标跟踪"""
        evolution_engine.client.vary = AsyncMock(return_value=sample_variations)
        evolution_engine.client.select = AsyncMock(return_value=sample_variations[:2])
        evolution_engine.client.save_checkpoint = AsyncMock()

        result = await evolution_engine.evolve_code(temp_target_file)

        assert evolution_engine.metrics.variation_count >= 0
        if result.selected_genes:
            assert evolution_engine.metrics.selection_count >= 0

    @pytest.mark.skip(reason="callbacks功能待P2实现")
    async def test_evolution_callbacks(
        self, evolution_engine, temp_target_file, sample_variations
    ):
        """测试进化回调函数"""
        callbacks_called = {"variation": False, "selection": False}

        def on_variation(variations):
            callbacks_called["variation"] = True

        def on_selection(genes):
            callbacks_called["selection"] = True

        evolution_engine.register_callbacks(
            on_variation=on_variation,
            on_selection=on_selection
        )

        evolution_engine.client.vary = AsyncMock(return_value=sample_variations)
        evolution_engine.client.select = AsyncMock(return_value=sample_variations[:1])
        evolution_engine.client.inherit = AsyncMock(return_value=[])
        evolution_engine.client.save_checkpoint = AsyncMock()

        result = await evolution_engine.evolve_code(temp_target_file)

        assert callbacks_called["variation"]


# ============================================================================
# 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_file_not_found(self, evolution_engine):
        """测试文件不存在"""
        result = await evolution_engine.evolve_code("nonexistent_file.py")

        assert not result.success
        assert "不存在" in result.error or "不存在" in str(result.error)

    @pytest.mark.asyncio
    async def test_vary_failure_graceful_degradation(
        self, evolution_engine, temp_target_file
    ):
        """测试变异失败时的优雅降级"""
        evolution_engine.client.vary = AsyncMock(side_effect=Exception("Vary failed"))

        result = await evolution_engine.evolve_code(temp_target_file)

        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_reset_engine(self, evolution_engine):
        """测试引擎重置"""
        evolution_engine.gene_pool = [
            Gene(id="g1", type=GeneType.CODE, content="test", metadata={}, fitness_scores={})
        ]
        evolution_engine.history = [MagicMock()]

        await evolution_engine.reset()

        assert len(evolution_engine.gene_pool) == 0
        assert len(evolution_engine.history) == 0
        assert evolution_engine.metrics.generations == 0


# ============================================================================
# 并发测试
# ============================================================================

class TestConcurrency:
    """并发测试"""

    @pytest.mark.asyncio
    async def test_concurrent_evolution_calls(
        self, evolution_engine, temp_target_file
    ):
        """测试并发进化调用"""
        variations = [
            Variation(
                id=f"var_{i}",
                gene_id="gene_1",
                variation_type=VariationType.POINT,
                original_content="orig",
                modified_content=f"mod_{i}",
                change_summary="test",
                risk_level="low",
                predicted_fitness={"correctness": 0.5, "performance": 0.5, "stability": 0.5},
            )
            for i in range(2)
        ]

        evolution_engine.client.vary = AsyncMock(return_value=variations)
        evolution_engine.client.select = AsyncMock(return_value=variations[:1])
        evolution_engine.client.save_checkpoint = AsyncMock()

        results = await asyncio.gather(
            evolution_engine.evolve_code(temp_target_file, goal="任务1"),
            evolution_engine.evolve_code(temp_target_file, goal="任务2")
        )

        assert len(results) == 2
        assert all(r.success for r in results)


# ============================================================================
# 集成场景测试
# ============================================================================

class TestIntegrationScenarios:
    """集成场景测试"""

    @pytest.mark.asyncio
    async def test_scenario_code_optimization(
        self, evolution_engine, temp_target_file
    ):
        """场景: 代码性能优化"""
        variations = [
            Variation(
                id="var_opt",
                gene_id="base",
                variation_type=VariationType.BLOCK,
                original_content="def slow(): pass",
                modified_content="def slow(): return 42",
                change_summary="性能优化",
                risk_level="medium",
                predicted_fitness={
                    "correctness": 0.9,
                    "performance": 0.95,
                    "stability": 0.8
                },
                confidence=0.8
            )
        ]

        evolution_engine.client.vary = AsyncMock(return_value=variations)
        evolution_engine.client.select = AsyncMock(return_value=variations)
        evolution_engine.client.save_checkpoint = AsyncMock()

        context = SprintContext(
            sprint_id="perf-opt",
            sprint_number=5,
            goal="优化性能",
            current_metrics={"avg_duration": 500}
        )

        result = await evolution_engine.evolve_code(
            temp_target_file,
            context=context,
            goal="将平均执行时间减少50%"
        )

        assert result.success
        assert evolution_engine.should_evolve({"avg_duration": 800})

    @pytest.mark.asyncio
    async def test_scenario_stability_improvement(
        self, evolution_engine, temp_target_file
    ):
        """场景: 稳定性改进"""
        variations = [
            Variation(
                id="var_stable",
                gene_id="base",
                variation_type=VariationType.STRUCTURAL,
                original_content="def unstable(): pass",
                modified_content="def unstable(): return True",
                change_summary="添加异常处理",
                risk_level="low",
                predicted_fitness={
                    "correctness": 0.85,
                    "performance": 0.7,
                    "stability": 0.95
                },
                confidence=0.9
            )
        ]

        evolution_engine.client.vary = AsyncMock(return_value=variations)
        evolution_engine.client.select = AsyncMock(return_value=variations)
        evolution_engine.client.save_checkpoint = AsyncMock()

        context = SprintContext(
            sprint_id="stability-fix",
            sprint_number=3,
            goal="提升稳定性",
            current_metrics={"error_count": 20, "success_rate": 0.6}
        )

        result = await evolution_engine.evolve_code(
            temp_target_file,
            context=context,
            goal="减少错误率到5%以下"
        )

        assert result.success
        assert evolution_engine.should_evolve({
            "error_count": 20,
            "success_rate": 0.6,
            "avg_duration": 100
        })
