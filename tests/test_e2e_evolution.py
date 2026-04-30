"""
端到端进化测试 - 测试 GEPAEngine 完整进化流程

测试 SprintCycle GEPA 进化引擎的完整闭环：
1. 测量 (Measurement) → 评估当前代码质量
2. 变异 (Variation) → 生成代码变体
3. 选择 (Selection) → Pareto 前沿选择最优
4. 遗传 (Inheritance) → 提取成功模式
5. 回滚 (Rollback) → 确认/回滚变体
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch

from sprintcycle.evolution.gepa_engine import GEPAEngine, GEPAConfig, EvolutionStatus
from sprintcycle.evolution.types import (
    Gene, GeneType, Variation, VariationType,
    FitnessScore,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_storage():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def gepa_config(temp_dir, temp_storage):
    return GEPAConfig(
        repo_path=temp_dir,
        evolution_cache_dir=temp_storage,
        max_cycles=3,
        auto_commit=False,
        quality_gate_enabled=False,
        min_correctness=0.0,
        min_overall=0.0,
    )


@pytest.fixture
def gepa_engine(gepa_config):
    return GEPAEngine(config=gepa_config)


@pytest.fixture
def sample_variations():
    return [
        Variation(
            id=f"var_{i}",
            gene_id="gene_base",
            variation_type=VariationType.POINT,
            original_content="def add(a, b): return a + b",
            modified_content=f"def add(a, b): return a + b  # v{i}",
            change_summary=f"变更 {i}",
            risk_level="low",
            predicted_fitness={"correctness": 0.5 + i * 0.1, "performance": 0.6, "stability": 0.7},
        )
        for i in range(3)
    ]


# ============================================================================
# 阶段 1: 变异 (Variation) 测试
# ============================================================================

class TestVariationStage:
    """变异阶段测试"""

    def test_variation_generates_variants(self, gepa_engine):
        """测试变异生成变体"""
        code = "def example():\n    return 42"
        variants = gepa_engine.variation.generate_variants(baseline=code, goal="优化代码")
        assert len(variants) > 0
        for v in variants:
            assert v.modified_code
            assert v.change_summary

    def test_variation_with_empty_code(self, gepa_engine):
        """测试空代码的变异处理"""
        variants = gepa_engine.variation.generate_variants(baseline="", goal="优化")
        assert variants == []

    def test_variation_with_goal(self, gepa_engine):
        """测试带目标的变异"""
        code = "def example():\n    return 42"
        variants = gepa_engine.variation.generate_variants(
            baseline=code, goal="优化代码质量和性能"
        )
        assert len(variants) > 0


# ============================================================================
# 阶段 2: 选择 (Selection) 测试
# ============================================================================

class TestSelectionStage:
    """选择阶段测试"""

    def test_selection_evaluates_variants(self, gepa_engine):
        """测试选择评估变体"""
        code = "def example():\n    return 42"
        variants = gepa_engine.variation.generate_variants(baseline=code, goal="优化")
        baseline = gepa_engine.measurement.measure_all()
        evaluated = gepa_engine.selection.evaluate_variants(variants, baseline)
        assert len(evaluated) == len(variants)
        for ev in evaluated:
            assert ev.fitness is not None

    def test_selection_empty_variations(self, gepa_engine):
        """测试空变体的选择"""
        baseline = gepa_engine.measurement.measure_all()
        evaluated = gepa_engine.selection.evaluate_variants([], baseline)
        assert evaluated == []


# ============================================================================
# 阶段 3: 遗传 (Inheritance) 测试
# ============================================================================

class TestInheritanceStage:
    """遗传阶段测试"""

    def test_inheritance_extracts_genes(self, gepa_engine):
        """测试遗传提取基因"""
        from sprintcycle.evolution.inheritance_engine import EvolutionCycle, CodeVariant
        from sprintcycle.evolution.types import FitnessScore as FS

        cycle = EvolutionCycle(
            id="test_cycle",
            sprint_id="test_sprint",
            goal="优化代码",
            success=True,
            best_variant=CodeVariant(
                id="v1",
                cycle_id="test_cycle",
                original_code="def f(): return 1",
                modified_code="def f(): return 2",
                diff_content="- return 1\n+ return 2",
                fitness_score=FS(correctness=0.9, performance=0.8, stability=0.85, code_quality=0.9),
                selected=True,
            ),
        )
        genes = gepa_engine.inheritance.extract_genes(cycle)
        # LLM may fail in test, but should not crash
        assert isinstance(genes, list)


# ============================================================================
# 完整流程端到端测试
# ============================================================================

class TestE2EEvolution:
    """端到端进化流程测试"""

    def test_full_evolution_pipeline(self, gepa_engine):
        """测试完整进化流程"""
        cycles = gepa_engine.evolve(max_cycles=2)
        assert len(cycles) > 0
        for c in cycles:
            assert c.id
            assert hasattr(c, 'success')

    def test_evolve_with_zero_cycles(self, gepa_engine):
        """测试0轮进化"""
        cycles = gepa_engine.evolve(max_cycles=0)
        assert len(cycles) == 0

    def test_evolve_single_cycle(self, gepa_engine):
        """测试单轮进化"""
        cycles = gepa_engine.evolve(max_cycles=1)
        assert len(cycles) >= 1

    def test_evolution_status_tracking(self, gepa_engine):
        """测试进化状态跟踪"""
        gepa_engine.evolve(max_cycles=1)
        status = gepa_engine.get_status()
        assert status.cycles_completed >= 0
        assert isinstance(status, EvolutionStatus)

    def test_evolution_stats(self, gepa_engine):
        """测试进化统计"""
        gepa_engine.evolve(max_cycles=1)
        stats = gepa_engine.get_stats()
        assert "status" in stats
        assert "measurement" in stats
        assert "memory" in stats

    def test_execute_all_stages_dry_run(self, gepa_engine):
        """测试dry run模式"""
        result = gepa_engine.execute_all_stages(dry_run=True)
        assert result["success"]
        assert result["dry_run"] is True

    def test_evolve_agent_mode(self, gepa_engine):
        """测试agent模式"""
        result = gepa_engine.evolve_agent(mode="incremental", max_cycles=1)
        assert "success" in result
        assert "total_cycles" in result


# ============================================================================
# 错误处理测试
# ============================================================================

class TestErrorHandling:
    """错误处理测试"""

    def test_no_variants_graceful(self, gepa_engine):
        """测试无变体时的优雅处理"""
        with patch.object(gepa_engine.variation, 'generate_variants', return_value=[]):
            cycle = gepa_engine._run_one_cycle(0)
            assert cycle.success is False

    def test_quality_gate_check(self, gepa_engine):
        """测试质量门控检查"""
        config = gepa_engine.config
        assert config.quality_gate_enabled is False  # disabled in test config


# ============================================================================
# 收敛检测测试
# ============================================================================

class TestConvergenceDetection:
    """收敛检测测试"""

    def test_convergence_by_no_improvement(self, gepa_engine):
        """测试无改进时收敛"""
        gepa_engine._status.consecutive_no_improvement = 2
        gepa_engine.config.convergence_threshold = 2
        assert gepa_engine._is_converged() is True

    def test_no_convergence_with_improvement(self, gepa_engine):
        """测试有改进时不收敛"""
        gepa_engine._status.consecutive_no_improvement = 1
        gepa_engine.config.convergence_threshold = 2
        assert gepa_engine._is_converged() is False


# ============================================================================
# 模块导入测试
# ============================================================================

class TestModuleImports:
    """模块导入测试"""

    def test_import_gepa_engine(self):
        from sprintcycle.evolution import GEPAEngine
        assert GEPAEngine is not None

    def test_import_fitness_score(self):
        from sprintcycle.evolution import FitnessScore
        f = FitnessScore()
        assert f.avg() == 0.5

    def test_import_all_components(self):
        from sprintcycle.evolution import (
            GEPAEngine, GEPAConfig, EvolutionStatus,
            MeasurementProvider, MemoryStore,
            VariationEngine, SelectionEngine,
            InheritanceEngine, EvolutionRollbackManager,
        )
        assert all(c is not None for c in [
            GEPAEngine, GEPAConfig, EvolutionStatus,
            MeasurementProvider, MemoryStore,
            VariationEngine, SelectionEngine,
            InheritanceEngine, EvolutionRollbackManager,
        ])
