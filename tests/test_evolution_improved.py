"""
GEPA自进化Demo生成的测试用例 - Evolution模块覆盖率提升
通过DeepSeek LLM生成，针对evolution模块的低覆盖代码
"""
import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sprintcycle.evolution.memory_store import (
    EvolutionMemory,
    MemoryConfig,
    MemoryStore,
)
from sprintcycle.evolution.selection_engine import (
    EvaluatedVariant,
    SelectionConfig,
    SelectionEngine,
)
from sprintcycle.evolution.measurement import (
    MeasurementConfig,
    MeasurementProvider,
    MeasurementResult,
)


# =============================================================================
# memory_store 测试
# =============================================================================

class TestEvolutionMemory:
    """测试EvolutionMemory数据类"""

    def test_memory_to_dict(self):
        """测试Memory转字典"""
        memory = EvolutionMemory(
            id="test-id",
            memory_type="gene",
            content={"code": "test"},
        )
        result = memory.to_dict()
        assert result["id"] == "test-id"
        assert result["memory_type"] == "gene"
        assert result["success"] is True

    def test_memory_from_dict(self):
        """测试从字典创建Memory"""
        data = {
            "id": "test-id",
            "memory_type": "gene",
            "content": {"code": "test"},
            "context": {"key": "value"},
            "success": False,
            "score": 0.3,
            "tags": ["tag1"],
            "created_at": 123456.0,
            "accessed_at": 123457.0,
            "access_count": 5,
            "metadata": {"meta": "data"},
        }
        memory = EvolutionMemory.from_dict(data)
        assert memory.id == "test-id"
        assert memory.success is False
        assert memory.score == 0.3

    def test_memory_from_dict_with_defaults(self):
        """测试带默认值的from_dict"""
        data = {
            "id": "test-id",
            "memory_type": "gene",
            "content": {},
        }
        memory = EvolutionMemory.from_dict(data)
        assert memory.success is True
        assert memory.score == 0.5
        assert memory.tags == []


class TestMemoryStore:
    """测试MemoryStore核心功能"""

    @pytest.fixture
    def temp_store(self):
        """创建临时存储的MemoryStore"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MemoryConfig(storage_path=tmpdir)
            store = MemoryStore(config=config)
            yield store

    def test_store_creates_memory(self, temp_store):
        """测试存储记忆"""
        memory = temp_store.store(
            memory_type="gene",
            content={"code": "def foo(): pass"},
            tags=["python"],
        )
        assert memory.id is not None
        assert memory.memory_type == "gene"

    def test_get_existing_memory(self, temp_store):
        """测试获取存在的记忆"""
        stored = temp_store.store(memory_type="gene", content={})
        retrieved = temp_store.get(stored.id)
        assert retrieved is not None
        assert retrieved.id == stored.id

    def test_get_nonexistent_memory(self, temp_store):
        """测试获取不存在的记忆"""
        result = temp_store.get("non-existent-id")
        assert result is None

    def test_search_by_type(self, temp_store):
        """测试按类型搜索"""
        temp_store.store(memory_type="gene", content={})
        temp_store.store(memory_type="attempt", content={})
        results = temp_store.search(memory_type="gene")
        assert all(r.memory_type == "gene" for r in results)

    def test_search_by_tags(self, temp_store):
        """测试按标签搜索"""
        temp_store.store(memory_type="gene", content={}, tags=["python", "test"])
        temp_store.store(memory_type="gene", content={}, tags=["java"])
        results = temp_store.search(tags=["python"])
        assert all("python" in r.tags for r in results)

    def test_search_by_success(self, temp_store):
        """测试按成功状态搜索"""
        temp_store.store(memory_type="gene", content={}, success=True)
        temp_store.store(memory_type="gene", content={}, success=False)
        results = temp_store.search(success=True)
        assert all(r.success is True for r in results)

    def test_search_by_min_score(self, temp_store):
        """测试按最低分数搜索"""
        temp_store.store(memory_type="gene", content={}, score=0.3)
        temp_store.store(memory_type="gene", content={}, score=0.8)
        results = temp_store.search(min_score=0.7)
        assert all(r.score >= 0.7 for r in results)

    def test_get_successful_patterns(self, temp_store):
        """测试获取成功模式"""
        temp_store.store(memory_type="gene", content={}, success=True, score=0.8)
        temp_store.store(memory_type="gene", content={}, success=False, score=0.3)
        patterns = temp_store.get_successful_patterns(min_score=0.7)
        assert len(patterns) == 1
        assert patterns[0].success is True

    def test_get_failed_attempts(self, temp_store):
        """测试获取失败尝试"""
        temp_store.store(memory_type="attempt", content={}, success=False)
        temp_store.store(memory_type="attempt", content={}, success=True)
        attempts = temp_store.get_failed_attempts()
        assert all(not r.success for r in attempts)

    def test_update_score(self, temp_store):
        """测试更新分数"""
        memory = temp_store.store(memory_type="gene", content={})
        result = temp_store.update_score(memory.id, success=True, delta=0.2)
        assert result is True
        updated = temp_store.get(memory.id)
        assert updated.success is True

    def test_update_nonexistent_score(self, temp_store):
        """测试更新不存在记忆的分数"""
        result = temp_store.update_score("non-existent", success=True)
        assert result is False

    def test_delete_memory(self, temp_store):
        """测试删除记忆"""
        memory = temp_store.store(memory_type="gene", content={})
        result = temp_store.delete(memory.id)
        assert result is True
        assert temp_store.get(memory.id) is None

    def test_delete_nonexistent_memory(self, temp_store):
        """测试删除不存在的记忆"""
        result = temp_store.delete("non-existent")
        assert result is False

    def test_cleanup_old_memories(self):
        """测试旧记忆清理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MemoryConfig(storage_path=tmpdir, max_memories=2)
            store = MemoryStore(config=config)
            # 存储3个记忆，超过max_memories
            for i in range(3):
                store.store(memory_type="gene", content={"index": i})
            # 应该清理掉一个
            assert len(store._memories) <= 2

    def test_get_stats(self, temp_store):
        """测试获取统计信息"""
        temp_store.store(memory_type="gene", content={}, success=True)
        temp_store.store(memory_type="attempt", content={}, success=False)
        stats = temp_store.get_stats()
        assert stats["total_memories"] == 2
        assert "gene" in stats["by_type"]
        assert "attempt" in stats["by_type"]

    def test_clear_all_memories(self, temp_store):
        """测试清空所有记忆"""
        temp_store.store(memory_type="gene", content={})
        temp_store.store(memory_type="gene", content={})
        count = temp_store.clear()
        assert count == 2
        assert len(temp_store._memories) == 0


# =============================================================================
# selection_engine 测试
# =============================================================================

class TestSelectionConfig:
    """测试SelectionConfig配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = SelectionConfig()
        assert config.selection_strategy == "pareto"
        assert config.elite_ratio == 0.1
        assert config.min_fitness_threshold == 0.3

    def test_custom_config(self):
        """测试自定义配置"""
        config = SelectionConfig(
            selection_strategy="tournament",
            elite_ratio=0.2,
            min_fitness_threshold=0.5,
        )
        assert config.selection_strategy == "tournament"
        assert config.elite_ratio == 0.2


class TestEvaluatedVariant:
    """测试EvaluatedVariant类"""

    def test_variant_id_from_attribute(self):
        """测试从属性获取ID"""
        mock_variant = MagicMock()
        mock_variant.id = "variant-123"
        ev = EvaluatedVariant(variant=mock_variant, fitness=MagicMock())
        assert ev.id == "variant-123"

    def test_variant_id_from_object(self):
        """测试从对象获取ID"""
        class SimpleVariant:
            pass
        obj = SimpleVariant()
        ev = EvaluatedVariant(variant=obj, fitness=MagicMock())
        assert ev.id == str(id(obj))

    def test_variant_default_values(self):
        """测试默认值"""
        ev = EvaluatedVariant(variant=MagicMock(), fitness=MagicMock())
        assert ev.dominated is False
        assert ev.pareto_rank == 0
        assert ev.crowd_distance == 0.0


class TestSelectionEngine:
    """测试SelectionEngine选择引擎"""

    def test_evaluate_empty_variants(self):
        """测试评估空变体列表"""
        engine = SelectionEngine()
        result = engine.evaluate_variants([])
        assert result == []

    def test_evaluate_single_variant(self):
        """测试评估单个变体"""
        engine = SelectionEngine()
        mock_variant = MagicMock()
        mock_variant.id = "v1"
        mock_variant.predicted_fitness = None
        mock_variant.risk_level = "low"
        mock_variant.confidence = 0.8
        
        result = engine.evaluate_variants([mock_variant])
        assert len(result) == 1
        assert result[0].variant == mock_variant

    def test_evaluate_multiple_variants(self):
        """测试评估多个变体"""
        engine = SelectionEngine()
        variants = []
        for i in range(3):
            mock_variant = MagicMock()
            mock_variant.id = f"v{i}"
            mock_variant.predicted_fitness = None
            mock_variant.risk_level = "low"
            mock_variant.confidence = 0.5 + i * 0.1
            variants.append(mock_variant)
        
        result = engine.evaluate_variants(variants)
        assert len(result) == 3

    def test_get_variant_code_from_modified_code(self):
        """测试从modified_code获取代码"""
        engine = SelectionEngine()
        mock_variant = MagicMock()
        mock_variant.modified_code = "def foo(): pass"
        code = engine._get_variant_code(mock_variant)
        assert code == "def foo(): pass"

    def test_get_variant_code_from_dict(self):
        """测试从字典获取代码"""
        engine = SelectionEngine()
        variant = {"modified_code": "def bar(): pass"}
        code = engine._get_variant_code(variant)
        assert code == "def bar(): pass"

    def test_get_variant_code_empty(self):
        """测试从空变体获取代码"""
        engine = SelectionEngine()
        variant = {}
        code = engine._get_variant_code(variant)
        assert code == ""

    def test_dominates_strict(self):
        """测试支配关系"""
        engine = SelectionEngine()
        
        ev_a = EvaluatedVariant(
            variant=MagicMock(),
            fitness=MagicMock(correctness=0.9, performance=0.8, stability=0.7, code_quality=0.9)
        )
        ev_b = EvaluatedVariant(
            variant=MagicMock(),
            fitness=MagicMock(correctness=0.7, performance=0.6, stability=0.5, code_quality=0.6)
        )
        
        assert engine._dominates(ev_a, ev_b) is True
        assert engine._dominates(ev_b, ev_a) is False

    def test_dominates_equal(self):
        """测试相等时不支配"""
        engine = SelectionEngine()
        
        ev_a = EvaluatedVariant(
            variant=MagicMock(),
            fitness=MagicMock(correctness=0.5, performance=0.5, stability=0.5, code_quality=0.5)
        )
        ev_b = EvaluatedVariant(
            variant=MagicMock(),
            fitness=MagicMock(correctness=0.5, performance=0.5, stability=0.5, code_quality=0.5)
        )
        
        assert engine._dominates(ev_a, ev_b) is False

    def test_select_best_no_variants(self):
        """测试选择最佳变体但无变体"""
        engine = SelectionEngine()
        result = engine.select_best([])
        assert result is None

    def test_select_best_returns_first_when_all_equal(self):
        """测试所有变体相等时返回第一个"""
        engine = SelectionEngine(config=SelectionConfig(min_fitness_threshold=0.0))
        variants = []
        for i in range(3):
            mock_variant = MagicMock()
            mock_variant.id = f"v{i}"
            fitness = MagicMock()
            fitness.overall = 0.5
            fitness.correctness = 0.5
            ev = EvaluatedVariant(variant=mock_variant, fitness=fitness, dominated=False, pareto_rank=0)
            variants.append(ev)
        
        result = engine.select_best(variants)
        assert result is not None

    def test_select_elites_zero_count(self):
        """测试选择0个精英"""
        engine = SelectionEngine()
        result = engine.select_elites([], 0)
        assert result == []

    def test_select_elites_normal(self):
        """测试正常选择精英"""
        engine = SelectionEngine()
        variants = []
        for i in range(5):
            v = MagicMock()
            v.id = f"v{i}"
            v.fitness.overall = 0.5 + i * 0.1
            v.crowd_distance = i
            ev = EvaluatedVariant(variant=v, fitness=v.fitness)
            variants.append(ev)
        
        elites = engine.select_elites(variants, 2)
        assert len(elites) == 2

    def test_get_evaluation_history(self):
        """测试获取评估历史"""
        engine = SelectionEngine()
        mock_variant = MagicMock()
        mock_variant.id = "v1"
        mock_variant.predicted_fitness = None
        mock_variant.risk_level = "low"
        mock_variant.confidence = 0.5
        
        engine.evaluate_variants([mock_variant])
        history = engine.get_evaluation_history()
        assert len(history) == 1

    def test_get_stats(self):
        """测试获取统计信息"""
        engine = SelectionEngine(config=SelectionConfig(selection_strategy="tournament"))
        stats = engine.get_stats()
        assert stats["strategy"] == "tournament"
        assert "total_evaluated" in stats


# =============================================================================
# measurement 测试
# =============================================================================

class TestMeasurementConfig:
    """测试MeasurementConfig配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = MeasurementConfig()
        assert config.repo_path == "."
        assert config.quality_gate_enabled is True
        assert config.measurement_timeout == 300

    def test_custom_config(self):
        """测试自定义配置"""
        config = MeasurementConfig(
            repo_path="/custom/path",
            test_command="make test",
            coverage_threshold=0.8,
        )
        assert config.repo_path == "/custom/path"
        assert config.coverage_threshold == 0.8


class TestMeasurementResult:
    """测试MeasurementResult类"""

    def test_to_dict(self):
        """测试转字典"""
        result = MeasurementResult(
            correctness=0.9,
            performance=0.8,
            stability=0.7,
            code_quality=0.85,
            overall=0.82,
        )
        data = result.to_dict()
        assert data["correctness"] == 0.9
        assert data["overall"] == 0.82

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "correctness": 0.85,
            "performance": 0.75,
            "stability": 0.9,
            "code_quality": 0.8,
            "overall": 0.82,
            "details": {"key": "value"},
            "timestamp": 123456.0,
        }
        result = MeasurementResult.from_dict(data)
        assert result.correctness == 0.85
        assert result.overall == 0.82

    def test_bool_true(self):
        """测试布尔转换为True"""
        result = MeasurementResult(overall=0.6)
        assert bool(result) is True

    def test_bool_false(self):
        """测试布尔转换为False"""
        result = MeasurementResult(overall=0.4)
        assert bool(result) is False


class TestMeasurementProvider:
    """测试MeasurementProvider测量提供者"""

    def test_measure_all(self):
        """测试完整测量"""
        def mock_runner(cmd, cwd=".", timeout=300):
            return 0, "10 passed", ""
        
        provider = MeasurementProvider(runner=mock_runner)
        result = provider.measure_all()
        
        assert isinstance(result, MeasurementResult)
        assert result.correctness >= 0
        assert result.overall >= 0

    def test_measure_correctness_with_failures(self):
        """测试正确性测量含失败"""
        def mock_runner(cmd, cwd=".", timeout=300):
            return 1, "5 passed, 3 failed", ""
        
        provider = MeasurementProvider(runner=mock_runner)
        correctness = provider._measure_correctness()
        assert correctness < 1.0

    def test_measure_correctness_with_exception(self):
        """测试正确性测量异常"""
        def failing_runner(cmd, cwd=".", timeout=300):
            raise Exception("Runner failed")
        
        provider = MeasurementProvider(runner=failing_runner)
        correctness = provider._measure_correctness()
        assert correctness == 0.5  # 默认值

    def test_measure_performance_improved(self):
        """测试性能测量改善"""
        def mock_runner(cmd, cwd=".", timeout=300):
            return 0, "", ""
        
        provider = MeasurementProvider(runner=mock_runner)
        # 添加历史记录模拟改进
        provider._history.append(MeasurementResult(overall=0.7))
        provider._history.append(MeasurementResult(overall=0.8))
        
        performance = provider._measure_performance()
        assert performance >= 0.7

    def test_measure_stability(self):
        """测试稳定性测量"""
        def mock_runner(cmd, cwd=".", timeout=300):
            return 0, "", ""
        
        provider = MeasurementProvider(runner=mock_runner)
        # 添加历史记录
        provider._history.append(MeasurementResult(correctness=0.9))
        provider._history.append(MeasurementResult(correctness=0.8))
        provider._history.append(MeasurementResult(correctness=0.3))  # 低正确性
        
        stability = provider._measure_stability()
        assert stability < 1.0

    def test_check_quality_gate_disabled(self):
        """测试质量门禁禁用"""
        config = MeasurementConfig(quality_gate_enabled=False)
        provider = MeasurementProvider(config=config)
        result = MeasurementResult(correctness=0.1, overall=0.1)
        
        assert provider.check_quality_gate(result) is True

    def test_check_quality_gate_low_correctness(self):
        """测试质量门禁低正确性"""
        provider = MeasurementProvider()
        result = MeasurementResult(correctness=0.3, overall=0.8)
        
        assert provider.check_quality_gate(result) is False

    def test_check_quality_gate_low_overall(self):
        """测试质量门禁低总分"""
        config = MeasurementConfig(coverage_threshold=0.8)
        provider = MeasurementProvider(config=config)
        result = MeasurementResult(correctness=0.9, overall=0.5)
        
        assert provider.check_quality_gate(result) is False

    def test_get_history(self):
        """测试获取历史"""
        provider = MeasurementProvider()
        provider._history.append(MeasurementResult(overall=0.7))
        provider._history.append(MeasurementResult(overall=0.8))
        
        history = provider.get_history()
        assert len(history) == 2

    def test_get_latest(self):
        """测试获取最新结果"""
        provider = MeasurementProvider()
        provider._history.append(MeasurementResult(overall=0.7))
        provider._history.append(MeasurementResult(overall=0.8))
        
        latest = provider.get_latest()
        assert latest is not None
        assert latest.overall == 0.8

    def test_get_latest_empty(self):
        """测试获取最新但无历史"""
        provider = MeasurementProvider()
        latest = provider.get_latest()
        assert latest is None

    def test_compare_results(self):
        """测试比较结果"""
        provider = MeasurementProvider()
        baseline = MeasurementResult(
            correctness=0.7,
            performance=0.6,
            stability=0.8,
            code_quality=0.75,
            overall=0.72,
        )
        current = MeasurementResult(
            correctness=0.8,
            performance=0.7,
            stability=0.85,
            code_quality=0.8,
            overall=0.78,
        )
        
        diff = provider.compare(baseline, current)
        # 使用近似比较避免浮点数精度问题
        assert abs(diff["correctness_delta"] - 0.1) < 0.001
        assert abs(diff["overall_delta"] - 0.06) < 0.001

    def test_is_improved(self):
        """测试判断是否改进"""
        provider = MeasurementProvider()
        baseline = MeasurementResult(overall=0.7)
        current = MeasurementResult(overall=0.8)
        
        assert provider.is_improved(baseline, current) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
