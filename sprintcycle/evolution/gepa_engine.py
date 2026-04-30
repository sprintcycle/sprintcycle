"""
GEPAEngine - GEPA 自进化引擎主控引擎

SprintCycle GEPA 自进化引擎的统一入口。
替代原有的 SelfEvolutionAgent + StageExecutor。

核心流程：
1. 测量 (Measurement): 评估当前代码质量
2. 变异 (Variation): 生成代码变体
3. 选择 (Selection): 评估并选择最优变体
4. 遗传 (Inheritance): 提取成功模式作为基因
5. 回滚 (Rollback): 确认最优变体，回滚其他

这是 GEPA 自进化引擎的核心组件（Phase 5）。
"""

import logging
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from sprintcycle.evolution.measurement import MeasurementProvider, MeasurementResult, MeasurementConfig
from sprintcycle.evolution.types import FitnessScore
from sprintcycle.evolution.memory_store import MemoryStore, MemoryConfig, EvolutionMemory
from sprintcycle.evolution.variation_engine_new import VariationEngine, VariationConfig, GeneratedVariant
from sprintcycle.evolution.selection_engine import SelectionEngine, SelectionConfig, EvaluatedVariant
from sprintcycle.evolution.inheritance_engine import (
    InheritanceEngine,
    EvolutionCycle,
    CodeVariant,
    InheritanceGene,
)
from sprintcycle.evolution.rollback_manager import EvolutionRollbackManager, EvolutionConfig as RollbackConfig

logger = logging.getLogger(__name__)


class EvolutionError(Exception):
    """进化引擎异常基类"""
    pass


class ConvergenceError(EvolutionError):
    """收敛检测异常"""
    pass


class QualityGateError(EvolutionError):
    """质量门控失败"""
    pass


class VariationError(EvolutionError):
    """变异生成失败"""
    pass


@dataclass
class GEPAConfig:
    """GEPA 引擎配置"""
    max_cycles: int = 10
    convergence_threshold: int = 2
    min_improvement: float = 0.01
    quality_gate_enabled: bool = True
    min_correctness: float = 0.5
    min_overall: float = 0.4
    max_variations_per_cycle: int = 5
    auto_commit: bool = True
    commit_message_template: str = "[EVOLUTION] {cycle_id}: {improvement_summary}"
    measurement_config: Optional[MeasurementConfig] = None
    memory_config: Optional[MemoryConfig] = None
    variation_config: Optional[VariationConfig] = None
    selection_config: Optional[SelectionConfig] = None
    rollback_config: Optional[RollbackConfig] = None
    repo_path: str = "."
    evolution_cache_dir: str = "./evolution_cache"
    
    def __post_init__(self):
        if not self.measurement_config:
            self.measurement_config = MeasurementConfig(repo_path=self.repo_path)
        if not self.memory_config:
            self.memory_config = MemoryConfig(storage_path=f"{self.evolution_cache_dir}/memory")
        if not self.variation_config:
            self.variation_config = VariationConfig(max_variations_per_cycle=self.max_variations_per_cycle)
        if not self.selection_config:
            self.selection_config = SelectionConfig()
        if not self.rollback_config:
            self.rollback_config = RollbackConfig(repo_path=self.repo_path)


@dataclass
class EvolutionStatus:
    """进化状态"""
    phase: str = "idle"
    cycles_completed: int = 0
    total_cycles: int = 0
    current_cycle_id: Optional[str] = None
    baseline_fitness: float = 0.0
    current_fitness: float = 0.0
    improvement_count: int = 0
    consecutive_no_improvement: int = 0
    last_improvement_cycle: Optional[str] = None
    genes_extracted: int = 0
    variants_generated: int = 0
    variants_selected: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def is_converged(self) -> bool:
        return self.phase == "converged"
    
    @property
    def is_running(self) -> bool:
        return self.phase not in ("idle", "converged", "failed")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "cycles_completed": self.cycles_completed,
            "total_cycles": self.total_cycles,
            "current_cycle_id": self.current_cycle_id,
            "baseline_fitness": self.baseline_fitness,
            "current_fitness": self.current_fitness,
            "improvement_count": self.improvement_count,
            "consecutive_no_improvement": self.consecutive_no_improvement,
            "last_improvement_cycle": self.last_improvement_cycle,
            "genes_extracted": self.genes_extracted,
            "variants_generated": self.variants_generated,
            "variants_selected": self.variants_selected,
            "errors": self.errors,
            "is_converged": self.is_converged,
            "is_running": self.is_running,
        }


class GEPAEngine:
    """
    SprintCycle GEPA 自进化引擎 — 统一入口
    """
    
    def __init__(
        self,
        config: Optional[GEPAConfig] = None,
        measurement_provider: Optional[MeasurementProvider] = None,
        memory_store: Optional[MemoryStore] = None,
        variation_engine: Optional[VariationEngine] = None,
        selection_engine: Optional[SelectionEngine] = None,
        inheritance_engine: Optional[InheritanceEngine] = None,
        rollback_manager: Optional[EvolutionRollbackManager] = None,
    ):
        self.config = config or GEPAConfig()
        
        self.measurement = measurement_provider or MeasurementProvider(
            config=self.config.measurement_config
        )
        self.memory = memory_store or MemoryStore(
            config=self.config.memory_config
        )
        self.variation = variation_engine or VariationEngine(
            config=self.config.variation_config,
            memory_store=self.memory,
        )
        self.selection = selection_engine or SelectionEngine(
            config=self.config.selection_config,
            measurement_provider=self.measurement,
        )
        self.inheritance = inheritance_engine or InheritanceEngine(
            storage_path=self.config.evolution_cache_dir,
        )
        self.rollback = rollback_manager or EvolutionRollbackManager(
            config=self.config.rollback_config,
        )
        
        self._status = EvolutionStatus()
        self._cycles: List[EvolutionCycle] = []
        self._baseline: Optional[MeasurementResult] = None
        self._git_runner: Optional[Callable[..., Tuple[int, str, str]]] = None
    
    def set_git_runner(self, runner: Callable[..., Tuple[int, str, str]]) -> None:
        self._git_runner = runner
        if hasattr(self.rollback, "_git_runner"):
            self.rollback._git_runner = runner
    
    def evolve(self, max_cycles: Optional[int] = None) -> List[EvolutionCycle]:
        max_cycles = max_cycles if max_cycles is not None else self.config.max_cycles
        
        logger.info(f"Starting GEPA evolution: max_cycles={max_cycles}")
        self._status = EvolutionStatus(
            total_cycles=max_cycles,
            phase="idle",
            started_at=time.time(),
        )
        self._cycles = []
        
        try:
            self._status.phase = "measuring"
            self._baseline = self.measurement.measure_all()
            self._status.baseline_fitness = self._baseline.overall
            
            logger.info(f"Baseline fitness: {self._baseline.overall:.3f}")
            
            for cycle_num in range(max_cycles):
                self._status.cycles_completed = cycle_num
                
                if self._is_converged():
                    logger.info("Convergence detected, stopping evolution")
                    self._status.phase = "converged"
                    break
                
                cycle = self._run_one_cycle(cycle_num)
                self._cycles.append(cycle)
                
                if cycle.success:
                    self._status.improvement_count += 1
                    self._status.consecutive_no_improvement = 0
                    self._status.last_improvement_cycle = cycle.id
                    self._baseline = self.measurement.measure_all()
                    self._status.current_fitness = self._baseline.overall
                else:
                    self._status.consecutive_no_improvement += 1
                
                if cycle.success:
                    self._status.phase = "inheriting"
                    genes = self.inheritance.extract_genes(cycle)
                    self._status.genes_extracted += len(genes)
                    logger.info(f"Extracted {len(genes)} genes from cycle {cycle.id}")
                
                if self.config.auto_commit and cycle.success:
                    self._git_commit(cycle)
                
                logger.info(
                    f"Cycle {cycle_num + 1}/{max_cycles} completed: "
                    f"success={cycle.success}, fitness={self._baseline.overall:.3f}"
                )
            
            if self._status.cycles_completed >= max_cycles:
                logger.info(f"Reached max cycles: {max_cycles}")
            
            self._status.phase = "idle"
            self._status.completed_at = time.time()
            
        except Exception as e:
            logger.exception(f"Evolution failed: {e}")
            self._status.phase = "failed"
            self._status.errors.append(str(e))
            raise
        
        return self._cycles
    
    def _run_one_cycle(self, cycle_num: int) -> EvolutionCycle:
        cycle_id = f"evo_cycle_{int(time.time())}_{cycle_num}"
        
        self._status.current_cycle_id = cycle_id
        self._status.phase = "varying"
        
        logger.info(f"Running cycle {cycle_id}")
        
        try:
            baseline_code = self._get_baseline_code()
            variants = self.variation.generate_variants(
                baseline=baseline_code,
                goal="优化代码质量和性能",
                max_count=self.config.max_variations_per_cycle,
            )
            self._status.variants_generated += len(variants)
            
            if not variants:
                logger.warning(f"No variants generated in cycle {cycle_id}")
                return EvolutionCycle(
                    id=cycle_id,
                    sprint_id="default",
                    goal="优化代码",
                    success=False,
                    metadata={"error": "no_variants_generated"},
                )
        except Exception as e:
            logger.warning(f"Variation failed: {e}")
            raise VariationError(f"Failed to generate variants: {e}")
        
        self._status.phase = "selecting"
        evaluated = self.selection.evaluate_variants(variants, self._baseline)
        best = self.selection.select_best(evaluated, self._baseline)
        
        if not best:
            logger.warning(f"No best variant selected in cycle {cycle_id}")
            return EvolutionCycle(
                id=cycle_id,
                sprint_id="default",
                goal="优化代码",
                success=False,
                variants=self._variants_to_codevariants(variants, cycle_id),
                metadata={"error": "no_variant_selected"},
            )
        
        self._status.variants_selected += 1
        
        if self.config.quality_gate_enabled:
            if best.fitness.correctness < self.config.min_correctness:
                raise QualityGateError(
                    f"Quality gate failed: correctness={best.fitness.correctness}"
                )
            if best.fitness.overall < self.config.min_overall:
                raise QualityGateError(
                    f"Quality gate failed: overall={best.fitness.overall}"
                )
        
        self._status.phase = "committed"
        variant_id = best.id
        
        try:
            # Register all variants with rollback manager first
            for v in variants:
                try:
                    self.rollback.prepare_variant(v.id)
                except Exception as e:
                    logger.debug(f"Variant {v.id} prepare skipped: {e}")
            self.rollback.commit_variant(variant_id)
            for v in variants:
                if v.id != variant_id:
                    try:
                        self.rollback.rollback_variant(v.id)
                    except Exception as e:
                        logger.debug(f"Variant {v.id} rollback skipped: {e}")
        except Exception as e:
            logger.warning(f"Rollback handling issue: {e}")
        
        best_codevariant = CodeVariant(
            id=best.id,
            cycle_id=cycle_id,
            original_code=self._get_variant_original(best),
            modified_code=self._get_variant_modified(best),
            diff_content=self._compute_diff(
                self._get_variant_original(best),
                self._get_variant_modified(best),
            ),
            fitness_score=FitnessScore(
                correctness=best.fitness.correctness,
                performance=best.fitness.performance,
                stability=best.fitness.stability,
                code_quality=best.fitness.code_quality,
            ),
            selected=True,
        )
        
        cycle = EvolutionCycle(
            id=cycle_id,
            sprint_id="default",
            goal="优化代码质量和性能",
            success=True,
            best_variant=best_codevariant,
            variants=self._variants_to_codevariants(variants, cycle_id),
            improvement_rate=best.fitness.overall - (
                self._baseline.overall if self._baseline else 0
            ),
        )
        
        self._store_cycle_memory(cycle)
        
        return cycle
    
    def _is_converged(self) -> bool:
        if self._status.consecutive_no_improvement >= self.config.convergence_threshold:
            return True
        
        if self._baseline and len(self._cycles) >= 2:
            recent_improvements = []
            for i in range(max(0, len(self._cycles) - self.config.convergence_threshold), len(self._cycles)):
                if i > 0:
                    curr = self._cycles[i]
                    if curr.improvement_rate > self.config.min_improvement:
                        recent_improvements.append(True)
                    else:
                        recent_improvements.append(False)
            
            if recent_improvements and not any(recent_improvements):
                return True
        
        return False
    
    def execute_all_stages(
        self,
        dry_run: bool = True,
        goal: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(f"execute_all_stages: dry_run={dry_run}, goal={goal}")
        
        try:
            baseline = self.measurement.measure_all()
            code = self._get_baseline_code()
            variants = self.variation.generate_variants(
                baseline=code,
                goal=goal or "优化代码",
            )
            evaluated = self.selection.evaluate_variants(variants, baseline)
            best = self.selection.select_best(evaluated, baseline)
            
            result = {
                "success": True,
                "baseline": baseline.to_dict(),
                "variants_count": len(variants),
                "best_variant": best.variant.id if best else None,
                "best_fitness": best.fitness.to_dict() if best else None,
                "dry_run": dry_run,
                "cycles": self._cycles,
            }
            
            if not dry_run and best:
                self.rollback.commit_variant(best.id)
            
            return result
            
        except Exception as e:
            logger.exception(f"execute_all_stages failed: {e}")
            return {"success": False, "error": str(e)}
    
    def evolve_agent(
        self,
        mode: str = "incremental",
        max_cycles: int = 1,
        goal: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        logger.info(f"evolve_agent: mode={mode}, max_cycles={max_cycles}")
        
        original_config = self.config
        
        if mode == "aggressive":
            self.config.max_variations_per_cycle = 10
            self.config.convergence_threshold = 5
        elif mode == "conservative":
            self.config.max_variations_per_cycle = 3
            self.config.convergence_threshold = 1
            self.config.quality_gate_enabled = True
            self.config.min_correctness = 0.7
        
        try:
            cycles = self.evolve(max_cycles=max_cycles)
            successful = [c for c in cycles if c.success]
            
            return {
                "success": len(successful) > 0,
                "total_cycles": len(cycles),
                "successful_cycles": len(successful),
                "improvement_count": self._status.improvement_count,
                "genes_extracted": self._status.genes_extracted,
                "final_fitness": self._status.current_fitness,
                "converged": self._status.is_converged,
                "cycles": [c.to_dict() for c in cycles],
            }
            
        finally:
            self.config = original_config
    
    def get_status(self) -> EvolutionStatus:
        return self._status
    
    def get_cycles(self) -> List[EvolutionCycle]:
        return self._cycles.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "status": self._status.to_dict(),
            "measurement": {"history_length": len(self.measurement.get_history())},
            "memory": self.memory.get_stats(),
            "selection": self.selection.get_stats(),
            "rollback": self.rollback.get_stats(),
        }
    
    def _get_baseline_code(self) -> str:
        return "def example():\n    return 42"
    
    def _get_variant_original(self, evaluated: EvaluatedVariant) -> str:
        variant = evaluated.variant
        if hasattr(variant, "original_code"):
            return variant.original_code
        elif hasattr(variant, "original_content"):
            return variant.original_content
        return ""
    
    def _get_variant_modified(self, evaluated: EvaluatedVariant) -> str:
        variant = evaluated.variant
        if hasattr(variant, "modified_code"):
            return variant.modified_code
        elif hasattr(variant, "modified_content"):
            return variant.modified_content
        return ""
    
    def _compute_diff(self, original: str, modified: str) -> str:
        if not original or not modified:
            return ""
        
        original_lines = original.split("\n")
        modified_lines = modified.split("\n")
        
        diff_lines = []
        for i, (old, new) in enumerate(zip(original_lines, modified_lines)):
            if old != new:
                diff_lines.append(f"- {old}")
                diff_lines.append(f"+ {new}")
            else:
                diff_lines.append(f"  {old}")
        
        if len(modified_lines) > len(original_lines):
            for line in modified_lines[len(original_lines):]:
                diff_lines.append(f"+ {line}")
        elif len(original_lines) > len(modified_lines):
            for line in original_lines[len(modified_lines):]:
                diff_lines.append(f"- {line}")
        
        return "\n".join(diff_lines)
    
    def _variants_to_codevariants(
        self,
        variants: List[GeneratedVariant],
        cycle_id: str,
    ) -> List[CodeVariant]:
        return [
            CodeVariant(
                id=v.id,
                cycle_id=cycle_id,
                original_code=v.original_code,
                modified_code=v.modified_code,
                diff_content=self._compute_diff(v.original_code, v.modified_code),
                metadata={"strategy": v.strategy.value, "risk": v.risk_level},
            )
            for v in variants
        ]
    
    def _store_cycle_memory(self, cycle: EvolutionCycle) -> None:
        try:
            if cycle.best_variant and cycle.success:
                self.memory.store(
                    memory_type="gene",
                    content={
                        "cycle_id": cycle.id,
                        "code": cycle.best_variant.modified_code,
                        "diff": cycle.best_variant.diff_content,
                    },
                    context={"goal": cycle.goal},
                    success=True,
                    score=cycle.best_variant.fitness_score.avg()
                          if cycle.best_variant.fitness_score else 0.5,
                    tags=["evolution", "success", cycle.goal],
                )
            
            self.memory.store(
                memory_type="cycle",
                content=cycle.to_dict(),
                context={"goal": cycle.goal},
                success=cycle.success,
                score=cycle.improvement_rate,
            )
        except Exception as e:
            logger.warning(f"Failed to store cycle memory: {e}")
    
    def _git_commit(self, cycle: EvolutionCycle) -> bool:
        if not self.config.auto_commit:
            return False
        
        try:
            improvement = cycle.improvement_rate
            summary = f"improvement={improvement:.3f}"
            
            if cycle.best_variant:
                summary = cycle.best_variant.modified_code[:50].replace("\n", " ")
            
            message = self.config.commit_message_template.format(
                cycle_id=cycle.id,
                improvement_summary=summary,
            )
            
            if self._git_runner:
                rc, stdout, stderr = self._git_runner(
                    ["commit", "-am", message],
                    cwd=self.config.repo_path,
                )
            else:
                result = subprocess.run(
                    ["git", "commit", "-am", message],
                    cwd=self.config.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                rc = result.returncode
            
            if rc == 0:
                logger.info(f"Git commit: {message}")
                return True
            else:
                logger.warning(f"Git commit failed (rc={rc})")
                return False
                
        except Exception as e:
            logger.warning(f"Git commit failed: {e}")
            return False
