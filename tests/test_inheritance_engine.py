"""
InheritanceEngine 测试套件
"""

import json
import os
import re
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sprintcycle.evolution.inheritance_engine import (
    InheritanceEngine,
    InheritanceGene,
    EvolutionCycle,
    CodeVariant,
    FitnessScore,
    GeneMemoryStore,
    InheritanceError,
)
from sprintcycle.evolution.types import GeneType


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_storage():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def make_mock_llm_json():
    """Mock LLM 返回正确 JSON 字符串（无 json.dumps 包装）"""
    def _make_response(prompt):
        return '{"description": "添加 try-except 错误处理", "context_tags": ["错误处理", "稳定性"], "content": "try:\\n    pass\\nexcept Exception as e:\\n    pass"}'
    return _make_response


def make_mock_llm_text():
    """Mock LLM 返回纯文本"""
    def _make_response(prompt):
        return "这个改进添加了错误处理，使用 try-except 块。\n\ndef foo():\n    try:\n        pass\n    except:\n        pass"
    return _make_response


@pytest.fixture
def sample_cycle():
    return EvolutionCycle(
        id="cycle_001",
        sprint_id="sprint_001",
        goal="添加错误处理",
        success=True,
        best_variant=CodeVariant(
            id="var_001",
            cycle_id="cycle_001",
            original_code="def foo():\n    return 42",
            modified_code="def foo():\n    try:\n        return 42\n    except Exception as e:\n        print(e)\n        return None",
            diff_content="+try:\n+    return 42\n+except Exception as e:\n+    print(e)\n+    return None",
            fitness_score=FitnessScore(correctness=0.9, performance=0.8, stability=0.7),
            selected=True,
        ),
    )


@pytest.fixture
def sample_cycle_no_success():
    return EvolutionCycle(
        id="cycle_002",
        sprint_id="sprint_001",
        goal="性能优化",
        success=False,
        best_variant=None,
    )


@pytest.fixture
def engine_with_genes(temp_storage):
    engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
    gene1 = InheritanceGene(
        id="gene_test_1", gene_type=GeneType.CODE, content="try-except block",
        description="错误处理模式", context_tags=["错误处理", "稳定性"],
        success_count=5, fail_count=1, use_count=6, avg_fitness=0.8,
    )
    gene2 = InheritanceGene(
        id="gene_test_2", gene_type=GeneType.CODE, content="cache decorator",
        description="性能缓存", context_tags=["性能优化"],
        success_count=2, fail_count=2, use_count=4, avg_fitness=0.5,
    )
    gene3 = InheritanceGene(
        id="gene_test_3", gene_type=GeneType.CODE, content="readability improvement",
        description="可读性改进", context_tags=["可读性"],
        success_count=3, fail_count=0, use_count=3, avg_fitness=0.9,
    )
    engine.memory.store_gene(gene1)
    engine.memory.store_gene(gene2)
    engine.memory.store_gene(gene3)
    return engine


# =============================================================================
# Model Tests
# =============================================================================

class TestFitnessScore:
    def test_default_values(self):
        fs = FitnessScore()
        assert fs.correctness == 0.5
        assert fs.performance == 0.5

    def test_to_dict(self):
        fs = FitnessScore(correctness=0.9, performance=0.8)
        d = fs.to_dict()
        assert d["correctness"] == 0.9

    def test_from_dict(self):
        d = {"correctness": 0.7, "performance": 0.6, "stability": 0.5, "code_quality": 0.4}
        fs = FitnessScore.from_dict(d)
        assert fs.correctness == 0.7

    def test_avg(self):
        fs = FitnessScore(correctness=0.8, performance=0.6, stability=0.4, code_quality=0.2)
        assert fs.avg() == 0.5


class TestCodeVariant:
    def test_to_dict(self):
        variant = CodeVariant(
            id="var_001", cycle_id="cycle_001",
            original_code="a = 1", modified_code="a = 2",
            fitness_score=FitnessScore(correctness=0.9),
        )
        d = variant.to_dict()
        assert d["id"] == "var_001"
        assert d["fitness_score"]["correctness"] == 0.9


class TestEvolutionCycle:
    def test_to_dict_no_variant(self):
        cycle = EvolutionCycle(id="cycle_001", sprint_id="sprint_001", goal="test")
        d = cycle.to_dict()
        assert d["id"] == "cycle_001"
        assert d["best_variant"] is None

    def test_to_dict_with_variant(self, sample_cycle):
        d = sample_cycle.to_dict()
        assert d["success"] is True
        assert d["best_variant"]["id"] == "var_001"


class TestInheritanceGene:
    def test_success_rate_zero_uses(self):
        gene = InheritanceGene(id="gene_1", gene_type=GeneType.CODE, content="test")
        assert gene.success_rate == 0.0

    def test_success_rate_all_success(self):
        gene = InheritanceGene(id="gene_1", gene_type=GeneType.CODE, content="test",
                               success_count=10, fail_count=0)
        assert gene.success_rate == 1.0

    def test_success_rate_mixed(self):
        gene = InheritanceGene(id="gene_1", gene_type=GeneType.CODE, content="test",
                               success_count=3, fail_count=1)
        assert gene.success_rate == 0.75

    def test_total_uses(self):
        gene = InheritanceGene(id="gene_1", gene_type=GeneType.CODE, content="test", use_count=5)
        assert gene.total_uses == 5

    def test_to_dict(self):
        gene = InheritanceGene(id="gene_1", gene_type=GeneType.CODE, content="test",
                               context_tags=["优化"], success_count=2, fail_count=1)
        d = gene.to_dict()
        assert d["id"] == "gene_1"
        assert d["success_rate"] == 2 / 3

    def test_from_dict(self):
        data = {
            "id": "gene_from", "gene_type": "code", "content": "test content",
            "description": "test desc", "context_tags": ["tag1"],
            "success_count": 2, "fail_count": 0, "use_count": 2, "avg_fitness": 0.8,
            "parent_ids": [], "created_at": datetime.now().isoformat(),
        }
        gene = InheritanceGene.from_dict(data)
        assert gene.id == "gene_from"
        assert gene.success_rate == 1.0

    def test_to_gene(self):
        gene = InheritanceGene(id="gene_1", gene_type=GeneType.CODE, content="test",
                               context_tags=["错误处理"], success_count=5, fail_count=1)
        std_gene = gene.to_gene()
        assert std_gene.id == "gene_1"
        assert std_gene.metadata["context_tags"] == ["错误处理"]


# =============================================================================
# Memory Store Tests
# =============================================================================

class TestGeneMemoryStore:
    def test_store_and_get(self, temp_storage):
        store = GeneMemoryStore(storage_path=temp_storage)
        gene = InheritanceGene(id="store_test_gene", gene_type=GeneType.CODE, content="test")
        store.store_gene(gene)
        retrieved = store.get_gene("store_test_gene")
        assert retrieved is not None
        assert retrieved.id == "store_test_gene"

    def test_search_genes(self, temp_storage):
        store = GeneMemoryStore(storage_path=temp_storage)
        gene1 = InheritanceGene(id="g1", gene_type=GeneType.CODE, content="c1",
                                context_tags=["性能"], success_count=5, fail_count=0)
        gene2 = InheritanceGene(id="g2", gene_type=GeneType.CODE, content="c2",
                                context_tags=["可读性"], success_count=2, fail_count=1)
        store.store_gene(gene1)
        store.store_gene(gene2)
        results = store.search_genes(["性能"])
        assert len(results) == 1
        assert results[0].id == "g1"

    def test_update_gene_stats(self, temp_storage):
        store = GeneMemoryStore(storage_path=temp_storage)
        gene = InheritanceGene(id="stats_gene", gene_type=GeneType.CODE, content="test",
                               success_count=1, fail_count=1)
        store.store_gene(gene)
        store.update_gene_stats("stats_gene", success=True, fitness=0.9)
        updated = store.get_gene("stats_gene")
        assert updated.success_count == 2
        # avg_fitness = (0.5 + 0.9) / 2 = 0.7
        assert abs(updated.avg_fitness - 0.7) < 0.001

    def test_delete_gene(self, temp_storage):
        store = GeneMemoryStore(storage_path=temp_storage)
        gene = InheritanceGene(id="del_gene", gene_type=GeneType.CODE, content="test")
        store.store_gene(gene)
        assert store.delete_gene("del_gene") is True
        assert store.get_gene("del_gene") is None

    def test_get_all_genes(self, temp_storage):
        store = GeneMemoryStore(storage_path=temp_storage)
        for i in range(3):
            gene = InheritanceGene(id=f"all_gene_{i}", gene_type=GeneType.CODE, content="test")
            store.store_gene(gene)
        assert len(store.get_all_genes()) == 3


# =============================================================================
# Gene Extraction Tests
# =============================================================================

class TestGeneExtraction:
    def test_extract_genes_success(self, temp_storage, sample_cycle):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        genes = engine.extract_genes(sample_cycle)
        assert len(genes) == 1
        gene = genes[0]
        assert gene.description == "添加 try-except 错误处理"
        assert "错误处理" in gene.context_tags
        assert gene.gene_type == GeneType.CODE

    def test_extract_genes_no_success(self, temp_storage, sample_cycle_no_success):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        genes = engine.extract_genes(sample_cycle_no_success)
        assert genes == []

    def test_extract_genes_empty_cycle(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        cycle = EvolutionCycle(id="empty", sprint_id="sp", goal="test", success=True)
        genes = engine.extract_genes(cycle)
        assert genes == []

    def test_extract_genes_stored(self, temp_storage, sample_cycle):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        engine.extract_genes(sample_cycle)
        pool = engine.get_gene_pool()
        assert len(pool) == 1
        assert pool[0].metadata.get("source_cycle_id") == "cycle_001"


# =============================================================================
# Gene Selection Tests
# =============================================================================

class TestGeneSelection:
    def test_select_by_targets(self, engine_with_genes):
        genes = engine_with_genes.select_genes_for_variation(["错误处理", "稳定性"])
        assert len(genes) > 0
        assert genes[0].id == "gene_test_1"

    def test_select_empty_targets(self, engine_with_genes):
        genes = engine_with_genes.select_genes_for_variation([])
        assert len(genes) == 3
        assert genes[0].id == "gene_test_3"

    def test_select_no_match(self, engine_with_genes):
        genes = engine_with_genes.select_genes_for_variation(["完全不匹配的标签"])
        assert len(genes) > 0

    def test_select_updates_use_count(self, engine_with_genes):
        before = engine_with_genes.get_gene("gene_test_1").use_count
        engine_with_genes.select_genes_for_variation(["错误处理"])
        after = engine_with_genes.get_gene("gene_test_1").use_count
        assert after == before + 1


# =============================================================================
# Gene Result Recording Tests
# =============================================================================

class TestGeneResultRecording:
    def test_record_success(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="result_gene", gene_type=GeneType.CODE, content="test",
                               success_count=1, fail_count=0)
        engine.memory.store_gene(gene)
        engine.record_gene_result("result_gene", success=True, fitness=0.9)
        updated = engine.get_gene("result_gene")
        assert updated.success_count == 2

    def test_record_failure(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="fail_gene", gene_type=GeneType.CODE, content="test",
                               success_count=1, fail_count=1)
        engine.memory.store_gene(gene)
        engine.record_gene_result("fail_gene", success=False)
        updated = engine.get_gene("fail_gene")
        assert updated.fail_count == 2

    def test_record_nonexistent_gene(self, temp_storage, caplog):
        engine = InheritanceEngine(storage_path=temp_storage)
        engine.record_gene_result("nonexistent", success=True)
        assert "not found" in caplog.text


# =============================================================================
# Gene Pruning Tests
# =============================================================================

class TestGenePruning:
    def test_prune_low_success_rate(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="prune_gene", gene_type=GeneType.CODE, content="test",
                               success_count=1, fail_count=3, use_count=4)
        engine.memory.store_gene(gene)
        pruned = engine.prune_genes(min_success_rate=0.3, min_uses=3)
        assert pruned == 1
        assert engine.get_gene("prune_gene") is None

    def test_prune_high_success_rate_kept(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="keep_gene", gene_type=GeneType.CODE, content="test",
                               success_count=5, fail_count=1, use_count=6)
        engine.memory.store_gene(gene)
        pruned = engine.prune_genes(min_success_rate=0.3, min_uses=3)
        assert pruned == 0
        assert engine.get_gene("keep_gene") is not None

    def test_prune_below_min_uses(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="new_gene", gene_type=GeneType.CODE, content="test",
                               success_count=0, fail_count=2, use_count=2)
        engine.memory.store_gene(gene)
        pruned = engine.prune_genes(min_success_rate=0.3, min_uses=3)
        assert pruned == 0

    def test_prune_zero_success_rate(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="zero_gene", gene_type=GeneType.CODE, content="test",
                               success_count=0, fail_count=5, use_count=5)
        engine.memory.store_gene(gene)
        pruned = engine.prune_genes(min_success_rate=0.3, min_uses=3)
        assert pruned == 1

    def test_prune_custom_thresholds(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = InheritanceGene(id="thresh_gene", gene_type=GeneType.CODE, content="test",
                               success_count=1, fail_count=1, use_count=2)
        engine.memory.store_gene(gene)
        pruned = engine.prune_genes(min_success_rate=0.3, min_uses=3)
        assert pruned == 0


# =============================================================================
# LLM Parsing Tests
# =============================================================================

class TestLLMParsing:
    def test_parse_json_block(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        output = '{"description": "性能缓存", "context_tags": ["性能"], "content": "@lru_cache"}'
        gene = engine._parse_gene(output, "cycle_x")
        assert gene is not None
        assert gene.description == "性能缓存"
        assert "性能" in gene.context_tags

    def test_parse_plain_json(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        output = '{"description": "plain json", "context_tags": ["t1"], "content": "x"}'
        gene = engine._parse_gene(output, "cycle_z")
        assert gene is not None
        assert gene.description == "plain json"

    def test_parse_text_fallback(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        output = "这个改进添加了错误处理。\n\n关键词：错误处理\ndef foo():\n    try:\n        pass\n    except:\n        pass"
        gene = engine._parse_gene(output, "cycle_w")
        assert gene is not None
        assert "错误处理" in gene.context_tags

    def test_parse_empty_output(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        gene = engine._parse_gene("", "cycle_empty")
        assert gene is not None

    def test_parse_invalid_json(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        output = "这不是有效的JSON { broken"
        gene = engine._parse_gene(output, "cycle_broken")
        assert gene is not None

    def test_extract_tags(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        text = "这个改进涉及性能优化和错误处理"
        tags = engine._extract_tags(text)
        assert "性能优化" in tags or "性能" in tags

    def test_extract_content_code_block(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        text = "描述\n```python\ndef foo():\n    return 1\n```\n更多"
        content = engine._extract_content(text)
        assert "def foo" in content

    def test_extract_content_indented(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage)
        text = "描述\n    def bar():\n        pass\n    class Test:\n        pass"
        content = engine._extract_content(text)
        assert "def bar" in content


# =============================================================================
# Integration Tests
# =============================================================================

class TestInheritanceEngineIntegration:
    def test_full_workflow(self, temp_storage, sample_cycle):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        genes = engine.extract_genes(sample_cycle)
        assert len(genes) == 1
        selected = engine.select_genes_for_variation(["错误处理"])
        assert len(selected) >= 1
        gene_id = genes[0].id
        engine.record_gene_result(gene_id, success=True, fitness=0.85)
        updated = engine.get_gene(gene_id)
        assert updated.success_count == 1

    def test_stats(self, temp_storage, sample_cycle):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        engine.extract_genes(sample_cycle)
        stats = engine.get_stats()
        assert stats["total_genes"] == 1
        assert "avg_success_rate" in stats

    def test_multiple_cycles(self, temp_storage):
        engine = InheritanceEngine(storage_path=temp_storage, llm_call_fn=make_mock_llm_json())
        for i in range(3):
            cycle = EvolutionCycle(
                id=f"cycle_{i}", sprint_id="sp", goal="test", success=True,
                best_variant=CodeVariant(
                    id=f"var_{i}", cycle_id=f"cycle_{i}",
                    original_code="x = 1", modified_code=f"x = {i}",
                    fitness_score=FitnessScore(correctness=0.5 + i * 0.1),
                ),
            )
            engine.extract_genes(cycle)
        assert len(engine.get_gene_pool()) == 3
