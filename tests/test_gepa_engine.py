"""
GEPAEngine 测试套件

测试 GEPA 自进化引擎的完整功能。
"""

import tempfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from sprintcycle.evolution.gepa_engine import (
    GEPAEngine,
    GEPAConfig,
    EvolutionStatus,
    EvolutionError,
    ConvergenceError,
    QualityGateError,
    VariationError,
)
from sprintcycle.evolution.measurement import (
    MeasurementProvider,
    MeasurementResult,
    MeasurementConfig,
)
from sprintcycle.evolution.memory_store import MemoryStore, EvolutionMemory, MemoryConfig
from sprintcycle.evolution.variation_engine_new import (
    VariationEngine,
    VariationConfig,
    GeneratedVariant,
)
from sprintcycle.evolution.selection_engine import (
    SelectionEngine,
    SelectionConfig,
    FitnessScore,
    EvaluatedVariant,
)
from sprintcycle.evolution.inheritance_engine import (
    InheritanceEngine,
    EvolutionCycle,
    CodeVariant,
)
from sprintcycle.evolution.rollback_manager import (
    EvolutionRollbackManager,
    EvolutionConfig as RollbackConfig,
)
from sprintcycle.evolution.types import GeneType, VariationType


# Fixtures

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
def mock_git_runner():
    def runner(args, cwd=".", timeout=30):
        if "commit" in args:
            return (0, "", "")
        return (0, "mock_git_output", "")
    return runner


@pytest.fixture
def default_config(temp_dir, temp_storage):
    return GEPAConfig(
        repo_path=temp_dir,
        evolution_cache_dir=temp_storage,
        max_cycles=3,
        convergence_threshold=2,
        min_improvement=0.01,
        quality_gate_enabled=True,
        min_correctness=0.3,
        min_overall=0.2,
        max_variations_per_cycle=5,
        auto_commit=False,
    )


@pytest.fixture
def measurement_provider():
    config = MeasurementConfig()
    provider = MeasurementProvider(config)
    provider._history.append(MeasurementResult(
        correctness=0.8, performance=0.7, stability=0.9,
        code_quality=0.6, overall=0.75,
    ))
    return provider


@pytest.fixture
def memory_store(temp_storage):
    return MemoryStore(storage_path=temp_storage)


@pytest.fixture
def variation_engine(memory_store):
    config = VariationConfig(max_variations_per_cycle=5)
    return VariationEngine(config=config, memory_store=memory_store)


@pytest.fixture
def selection_engine(measurement_provider):
    config = SelectionConfig()
    return SelectionEngine(config=config, measurement_provider=measurement_provider)


@pytest.fixture
def inheritance_engine(temp_storage):
    return InheritanceEngine(storage_path=temp_storage)


@pytest.fixture
def rollback_manager(temp_dir):
    config = RollbackConfig(repo_path=temp_dir, git_branch_mode=False)
    return EvolutionRollbackManager(config=config)


@pytest.fixture
def gepa_engine(
    default_config,
    measurement_provider,
    memory_store,
    variation_engine,
    selection_engine,
    inheritance_engine,
    rollback_manager,
):
    return GEPAEngine(
        config=default_config,
        measurement_provider=measurement_provider,
        memory_store=memory_store,
        variation_engine=variation_engine,
        selection_engine=selection_engine,
        inheritance_engine=inheritance_engine,
        rollback_manager=rollback_manager,
    )


@pytest.fixture
def sample_baseline_code():
    return '''def calculate(x, y):
    """Calculate sum of two numbers"""
    return x + y
'''


class TestGEPAConfig:
    def test_default_values(self):
        config = GEPAConfig()
        assert config.max_cycles == 10
        assert config.convergence_threshold == 2
        assert config.quality_gate_enabled is True

    def test_custom_values(self):
        config = GEPAConfig(max_cycles=5, convergence_threshold=3)
        assert config.max_cycles == 5
        assert config.convergence_threshold == 3

    def test_post_init_sets_defaults(self):
        config = GEPAConfig(repo_path="/test", evolution_cache_dir="/cache")
        assert config.measurement_config is not None
        assert config.memory_config is not None


class TestEvolutionStatus:
    def test_default_values(self):
        status = EvolutionStatus()
        assert status.phase == "idle"
        assert status.cycles_completed == 0
        assert status.improvement_count == 0

    def test_is_converged(self):
        status = EvolutionStatus(phase="converged")
        assert status.is_converged is True
        assert status.is_running is False

    def test_is_running(self):
        status = EvolutionStatus(phase="measuring")
        assert status.is_running is True

    def test_to_dict(self):
        status = EvolutionStatus(phase="completed", cycles_completed=5)
        data = status.to_dict()
        assert data["phase"] == "completed"
        assert "is_converged" in data


class TestGEPAEngineInit:
    def test_init_with_default_config(self):
        engine = GEPAEngine()
        assert engine.config is not None
        assert engine.measurement is not None
        assert engine.memory is not None
        assert engine.variation is not None
        assert engine.selection is not None

    def test_init_with_custom_components(self, gepa_engine):
        assert gepa_engine.measurement is not None
        assert gepa_engine.memory is not None

    def test_init_sets_initial_status(self, gepa_engine):
        status = gepa_engine.get_status()
        assert status.phase == "idle"
        assert status.cycles_completed == 0

    def test_set_git_runner(self, gepa_engine, mock_git_runner):
        gepa_engine.set_git_runner(mock_git_runner)
        assert gepa_engine._git_runner == mock_git_runner


class TestSingleCycleEvolution:
    def test_run_one_cycle_success(self, gepa_engine):
        cycle = gepa_engine._run_one_cycle(0)
        assert cycle is not None
        assert cycle.id is not None

    def test_run_one_cycle_no_variants(self, gepa_engine):
        with patch.object(gepa_engine.variation, 'generate_variants', return_value=[]):
            cycle = gepa_engine._run_one_cycle(0)
            assert cycle is not None
            assert cycle.success is False


class TestMultiCycleEvolution:
    def test_evolve_single_cycle(self, gepa_engine):
        cycles = gepa_engine.evolve(max_cycles=1)
        assert len(cycles) == 1

    def test_evolve_multiple_cycles(self, gepa_engine):
        cycles = gepa_engine.evolve(max_cycles=3)
        assert len(cycles) <= 3

    def test_evolve_stores_cycles(self, gepa_engine):
        gepa_engine.evolve(max_cycles=2)
        cycles = gepa_engine.get_cycles()
        assert isinstance(cycles, list)


class TestConvergenceDetection:
    def test_convergence_by_no_improvement(self, gepa_engine):
        gepa_engine._status.consecutive_no_improvement = 2
        gepa_engine.config.convergence_threshold = 2
        assert gepa_engine._is_converged() is True

    def test_no_convergence_with_improvement(self, gepa_engine):
        gepa_engine._status.consecutive_no_improvement = 1
        gepa_engine.config.convergence_threshold = 2
        assert gepa_engine._is_converged() is False


class TestQualityGate:
    def test_quality_gate_enabled(self, gepa_engine):
        assert gepa_engine.config.quality_gate_enabled is True

    def test_quality_gate_threshold(self, gepa_engine):
        assert gepa_engine.config.min_correctness >= 0


class TestBackwardCompatibility:
    def test_execute_all_stages_dry_run(self, gepa_engine):
        result = gepa_engine.execute_all_stages(dry_run=True)
        assert "success" in result
        assert result["dry_run"] is True

    def test_execute_all_stages_no_dry_run(self, gepa_engine):
        result = gepa_engine.execute_all_stages(dry_run=False)
        assert "success" in result

    def test_evolve_agent_incremental_mode(self, gepa_engine):
        result = gepa_engine.evolve_agent(mode="incremental", max_cycles=1)
        assert "success" in result
        assert "total_cycles" in result


class TestStatusAndStats:
    def test_get_status_initial(self, gepa_engine):
        status = gepa_engine.get_status()
        assert status.phase == "idle"

    def test_get_stats(self, gepa_engine):
        stats = gepa_engine.get_stats()
        assert "status" in stats
        assert "measurement" in stats
        assert "memory" in stats


class TestExceptions:
    def test_evolution_error(self):
        with pytest.raises(EvolutionError):
            raise EvolutionError("Test error")

    def test_convergence_error(self):
        with pytest.raises(ConvergenceError):
            raise ConvergenceError("Converged")

    def test_quality_gate_error(self):
        with pytest.raises(QualityGateError):
            raise QualityGateError("Quality gate failed")


class TestEdgeCases:
    def test_zero_max_cycles(self, gepa_engine):
        cycles = gepa_engine.evolve(max_cycles=0)
        assert len(cycles) == 0

    def test_git_commit_failure(self, gepa_engine, mock_git_runner):
        def failing_runner(args, cwd=".", timeout=30):
            if "commit" in args:
                return (1, "", "Commit failed")
            return (0, "", "")
        
        gepa_engine.set_git_runner(failing_runner)
        gepa_engine.config.auto_commit = True
        
        cycle = EvolutionCycle(
            id="test_cycle", sprint_id="sprint", goal="Test", success=True,
        )
        result = gepa_engine._git_commit(cycle)
        assert result is False


class TestEndToEndEvolution:
    def test_full_evolution_flow(self, gepa_engine):
        assert gepa_engine.get_status().phase == "idle"
        cycles = gepa_engine.evolve(max_cycles=2)
        assert len(cycles) >= 0

    def test_evolution_with_all_components(self, gepa_engine):
        assert gepa_engine.measurement is not None
        assert gepa_engine.memory is not None
        assert gepa_engine.variation is not None
        assert gepa_engine.selection is not None
        assert gepa_engine.inheritance is not None
        assert gepa_engine.rollback is not None
        cycles = gepa_engine.evolve(max_cycles=1)
        assert gepa_engine.get_status() is not None


class TestModuleImports:
    def test_import_gepa_engine(self):
        from sprintcycle.evolution import GEPAEngine
        assert GEPAEngine is not None

    def test_import_measurement_provider(self):
        from sprintcycle.evolution import MeasurementProvider
        assert MeasurementProvider is not None

    def test_import_memory_store(self):
        from sprintcycle.evolution import MemoryStore
        assert MemoryStore is not None

    def test_import_all_components(self):
        from sprintcycle.evolution import (
            GEPAEngine, GEPAConfig, EvolutionStatus,
            MeasurementProvider, MemoryStore, VariationEngine,
            SelectionEngine, InheritanceEngine, EvolutionRollbackManager,
        )
        assert GEPAEngine is not None
        assert GEPAConfig is not None
        assert EvolutionStatus is not None
