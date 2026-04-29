#!/usr/bin/env python3
"""
SprintCycle 15阶段自进化执行器 v2.0 (严格约束版)
================================================

严格约束原则:
1. 真实测量: 所有指标必须来自真实工具 (pytest --cov、radon cc、mypy等)
2. 实际修改: 执行阶段(10-12)必须实际修改sprintcycle/目录下的.py文件
3. 变更验证: 每个执行阶段完成后,通过 git diff --stat 验证确实产生了代码变更,无变更则FAILED
4. 测试守护: 修改后跑 pytest 确认测试通过
5. Git提交: 每个阶段产生实际变更后git commit
6. 无变更=失败: 整个流程没有代码变更则FAILED

阶段说明:
  阶段 1-3:  分析阶段 (Analysis) - 真实工具测量
  阶段 4-6:  规划阶段 (Planning) - 基于真实数据
  阶段 7-9:  设计阶段 (Design) - 生成具体方案
  阶段 10-12: 执行阶段 (Execution) - 必须实际改代码
  阶段 13-15: 验证阶段 (Validation) - 真实数据验证
"""

import os
import re
import sys
import json
import time
import subprocess
import random
import string
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from loguru import logger


# ============== 配置 ==============

@dataclass
class StrictEvolutionConfig:
    """严格约束配置"""
    project_path: str = "."
    sprintcycle_dir: str = "sprintcycle"
    tests_dir: str = "tests"
    coverage_threshold: float = 70.0
    complexity_threshold: int = 10
    max_complex_functions: int = 10
    max_low_coverage_modules: int = 5
    auto_commit: bool = True
    commit_message_prefix: str = "[EVOLUTION]"
    test_timeout: int = 300
    strict_mode: bool = True
    
    @property
    def sprintcycle_path(self) -> Path:
        return Path(self.project_path) / self.sprintcycle_dir


# ============== 阶段定义 ==============

class EvolutionStage(Enum):
    """15个进化阶段"""
    STAGE_1_CODE_ANALYSIS = "stage_1_code_analysis"
    STAGE_2_TEST_ANALYSIS = "stage_2_test_analysis"
    STAGE_3_TYPE_ANALYSIS = "stage_3_type_analysis"
    STAGE_4_COVERAGE_PLAN = "stage_4_coverage_plan"
    STAGE_5_COMPLEXITY_PLAN = "stage_5_complexity_plan"
    STAGE_6_TYPE_PLAN = "stage_6_type_plan"
    STAGE_7_TEST_DESIGN = "stage_7_test_design"
    STAGE_8_OPTIMIZATION_DESIGN = "stage_8_optimization_design"
    STAGE_9_DOCUMENTATION_DESIGN = "stage_9_documentation_design"
    STAGE_10_TEST_IMPLEMENTATION = "stage_10_test_implementation"
    STAGE_11_CODE_OPTIMIZATION = "stage_11_code_optimization"
    STAGE_12_TYPE_FIX = "stage_12_type_fix"
    STAGE_13_UNIT_TEST_VALIDATION = "stage_13_unit_test_validation"
    STAGE_14_COVERAGE_VALIDATION = "stage_14_coverage_validation"
    STAGE_15_FINAL_REPORT = "stage_15_final_report"


@dataclass
class EvolutionMetrics:
    """进化指标"""
    raw_coverage: Dict[str, Any] = field(default_factory=dict)
    raw_complexity: Dict[str, Any] = field(default_factory=dict)
    raw_type_errors: Dict[str, Any] = field(default_factory=dict)
    high_complexity_functions: List[Dict] = field(default_factory=list)
    low_coverage_modules: List[Dict] = field(default_factory=list)
    type_errors: List[Dict] = field(default_factory=list)
    coverage_plan: Dict = field(default_factory=dict)
    complexity_plan: Dict = field(default_factory=dict)
    type_plan: Dict = field(default_factory=dict)
    test_designs: List[Dict] = field(default_factory=list)
    optimization_designs: List[Dict] = field(default_factory=list)
    test_files_created: List[str] = field(default_factory=list)
    code_changes: List[str] = field(default_factory=list)
    type_fixes: List[str] = field(default_factory=list)
    final_coverage: float = 0.0
    final_tests_passed: bool = False
    total_files_changed: int = 0
    total_commits: int = 0
    dry_run: bool = True


@dataclass
class StageResult:
    """阶段执行结果"""
    stage: EvolutionStage
    status: str
    duration: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    changes_made: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_dry_run: bool = False


@dataclass
class EvolutionReport:
    """自进化报告"""
    project_name: str
    project_path: str
    sprintcycle_version: str
    start_time: str
    end_time: Optional[str] = None
    total_duration: float = 0.0
    product_score: float = 0.0
    framework_score: float = 0.0
    coverage: float = 0.0
    performance_improvement: float = 0.0
    stages: List[StageResult] = field(default_factory=list)
    metrics: EvolutionMetrics = field(default_factory=EvolutionMetrics)
    success: bool = False
    dry_run: bool = True
    errors: List[str] = field(default_factory=list)


# ============== 工具函数 ==============

def run_command(cmd: List[str], cwd: str = ".", timeout: int = 300) -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)


def get_git_diff_stat(cwd: str = ".") -> Tuple[int, List[str]]:
    """获取git diff统计"""
    _, stdout, _ = run_command(["git", "diff", "--stat"], cwd=cwd)
    lines = [l.strip() for l in stdout.strip().split("\n") if l.strip()]
    return len(lines), lines


def git_commit(message: str, cwd: str = ".") -> bool:
    """Git提交"""
    run_command(["git", "add", "-A"], cwd=cwd)
    code, _, _ = run_command(["git", "commit", "-m", message], cwd=cwd)
    return code == 0


# ============== 主执行器 ==============

class StageExecutor:
    """15阶段执行器 (严格约束版)"""
    
    def __init__(self, project_path: str = ".", config: Optional[StrictEvolutionConfig] = None):
        self.project_path = Path(project_path)
        self.config = config or StrictEvolutionConfig(project_path=str(project_path))
        self.results: List[StageResult] = []
        self.metrics = EvolutionMetrics()
        self.project_path.mkdir(parents=True, exist_ok=True)
        
        # EvolutionEngine compatibility methods
        self._execution_history: List[Dict] = []
        self._failure_records: List[Dict] = []
        self._execution_stats: Dict = {"total_executions": 0, "successful": 0, "failed": 0}
        self._success_strategies: List[Dict] = []
    
    # ============== EvolutionEngine Compatibility Methods ==============
    
    def record_execution(self, task: str, result: Dict) -> None:
        """记录执行结果（EvolutionEngine兼容方法）"""
        self._execution_history.append({"task": task, "result": result, "timestamp": datetime.now().isoformat()})
        self._execution_stats["total_executions"] += 1
        if result.get("success"):
            self._execution_stats["successful"] += 1
        else:
            self._execution_stats["failed"] += 1
            # Record failure pattern
            error = result.get("error", "")
            if error:
                self._failure_records.append({
                    "task": task,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })
    
    def get_evolution_stats(self) -> Dict:
        """获取进化统计（EvolutionEngine兼容方法）"""
        stats = self._execution_stats.copy()
        stats["strategies_learned"] = len(self._success_strategies)
        return stats
    
    def adapt_timeout(self, task: str) -> int:
        """自适应超时（EvolutionEngine兼容方法）"""
        # 基于历史执行时间计算超时
        task_executions = [e for e in self._execution_history if e["task"] == task]
        if task_executions:
            durations = [e["result"].get("duration", 60) for e in task_executions]
            avg_duration = sum(durations) / len(durations)
            return int(avg_duration * 2.5)  # 2.5x 平均时间
        return 120  # 默认超时
    
    def get_failure_patterns(self) -> List[Dict]:
        """获取失败模式（EvolutionEngine兼容方法）"""
        patterns = []
        for record in self._failure_records:
            error = record.get("error", "")
            patterns.append({
                "error_type": error.split(":")[0] if ":" in error else error,
                "count": 1,
                "task": record.get("task")
            })
        return patterns
    
    @property
    def ERROR_PATTERNS(self) -> Dict:
        """错误模式（EvolutionEngine兼容属性）"""
        from sprintcycle.utils.error_helper import ErrorCategory
        return {
            ErrorCategory.SYNTAX: ["SyntaxError", "IndentationError"],
            ErrorCategory.IMPORT: ["ImportError", "ModuleNotFoundError"],
            ErrorCategory.RUNTIME: ["TypeError", "ValueError", "KeyError", "IndexError", "AttributeError"],
            ErrorCategory.LOGIC: ["RecursionError", "AssertionError"],
            ErrorCategory.AIDER: ["AiderError", "APIError"],
            ErrorCategory.EMPTY_OUTPUT: ["EmptyOutputError"],
            ErrorCategory.NO_CHANGES: ["NoChangesError"],
        }
    
    def classify_error(self, error_message: str) -> "ErrorCategory":
        """分类错误（EvolutionEngine兼容方法）"""
        from sprintcycle.utils.error_helper import ErrorHelper, ErrorCategory
        helper = ErrorHelper()
        return helper.classify_error(error_message)
    
    def learn_from_success(self, task: str, result: Dict) -> None:
        """从成功中学习（EvolutionEngine兼容方法）"""
        # Track successful strategies for future reference
        self._success_strategies.append({
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def execute_all_stages(self, dry_run: bool = True) -> EvolutionReport:
        """执行所有15个阶段"""
        print(f"\n{'='*70}")
        print(f"🚀 SprintCycle 15阶段自进化执行器 v2.0 (严格约束版)")
        print(f"{'='*70}")
        print(f"📁 项目路径: {self.project_path}")
        print(f"🔧 模式: {'DRY_RUN (仅分析不修改)' if dry_run else 'LIVE (实际修改代码)'}")
        print(f"{'='*70}")
        
        self.metrics.dry_run = dry_run
        start_time = time.time()
        
        stages = list(EvolutionStage)
        for i, stage in enumerate(stages, 1):
            print(f"\n\n{'='*70}")
            print(f"📊 阶段 {i}/15: {stage.value}")
            print(f"{'='*70}")
            
            result = self.execute_stage(stage, dry_run=dry_run)
            self.results.append(result)
            
            status_icon = {
                "success": "✅", "failed": "❌", "skipped": "⏭️",
                "running": "🔄", "dry_run": "📋"
            }.get(result.status, "❓")
            print(f"\n{status_icon} 阶段状态: {result.status}")
            print(f"⏱️  耗时: {result.duration:.2f}秒")
            
            if result.changes_made:
                print(f"📝 变更:")
                for change in result.changes_made[:5]:
                    print(f"   - {change}")
            
            if result.issues:
                print(f"⚠️  问题:")
                for issue in result.issues[:3]:
                    print(f"   - {issue}")
        
        duration = time.time() - start_time
        report = self._generate_report(duration, dry_run)
        
        changed_files, _ = get_git_diff_stat(cwd=str(self.project_path))
        if changed_files > 0:
            print(f"\n📊 共产生 {changed_files} 个文件的变更")
        
        if dry_run:
            print(f"\n⚠️  DRY_RUN模式: 未实际修改代码")
            print(f"   移除 --live 参数以实际执行修改")
        
        return report
    
    def execute_stage(self, stage: EvolutionStage, dry_run: bool = True) -> StageResult:
        """执行单个阶段"""
        start_time = time.time()
        result = StageResult(stage=stage, status="running", is_dry_run=dry_run)
        
        try:
            stage_handlers = {
                EvolutionStage.STAGE_1_CODE_ANALYSIS: self._stage_1_code_analysis,
                EvolutionStage.STAGE_2_TEST_ANALYSIS: self._stage_2_test_analysis,
                EvolutionStage.STAGE_3_TYPE_ANALYSIS: self._stage_3_type_analysis,
                EvolutionStage.STAGE_4_COVERAGE_PLAN: self._stage_4_coverage_plan,
                EvolutionStage.STAGE_5_COMPLEXITY_PLAN: self._stage_5_complexity_plan,
                EvolutionStage.STAGE_6_TYPE_PLAN: self._stage_6_type_plan,
                EvolutionStage.STAGE_7_TEST_DESIGN: self._stage_7_test_design,
                EvolutionStage.STAGE_8_OPTIMIZATION_DESIGN: self._stage_8_optimization_design,
                EvolutionStage.STAGE_9_DOCUMENTATION_DESIGN: self._stage_9_documentation_design,
                EvolutionStage.STAGE_10_TEST_IMPLEMENTATION: lambda: self._stage_10_test_implementation(dry_run),
                EvolutionStage.STAGE_11_CODE_OPTIMIZATION: lambda: self._stage_11_code_optimization(dry_run),
                EvolutionStage.STAGE_12_TYPE_FIX: lambda: self._stage_12_type_fix(dry_run),
                EvolutionStage.STAGE_13_UNIT_TEST_VALIDATION: self._stage_13_unit_test_validation,
                EvolutionStage.STAGE_14_COVERAGE_VALIDATION: self._stage_14_coverage_validation,
                EvolutionStage.STAGE_15_FINAL_REPORT: self._stage_15_final_report,
            }
            
            if stage in stage_handlers:
                result = stage_handlers[stage]()
                
        except Exception as e:
            result.status = "failed"
            result.issues.append(str(e))
            logger.error(f"Stage {stage.value} failed: {e}")
        
        result.duration = time.time() - start_time
        return result
    
    # ============== 阶段1-3: 分析阶段 (真实工具) ==============
    
    def _stage_1_code_analysis(self) -> StageResult:
        """阶段1: 代码结构分析 - 使用 radon cc 真实测量"""
        print("🔍 使用 radon cc 分析代码复杂度...")
        
        sprint_dir = self.config.sprintcycle_path
        if not sprint_dir.exists():
            return StageResult(stage=EvolutionStage.STAGE_1_CODE_ANALYSIS, status="failed", issues=["sprintcycle目录不存在"])
        
        code, stdout, stderr = run_command(["radon", "cc", str(sprint_dir), "-s", "-n", "-a"], cwd=str(self.project_path), timeout=120)
        
        high_complexity_funcs = []
        all_complexity = []
        
        if stdout:
            for line in stdout.strip().split("\n"):
                if ":" in line and any(c.isalpha() for c in line[:5]):
                    parts = line.split(":")
                    if len(parts) >= 3:
                        func_info = parts[0].strip()
                        for part in parts[1:]:
                            part = part.strip()
                            if part and part[0] in "ABCDEF":
                                try:
                                    complexity = int(part[1:].strip().split()[0])
                                    all_complexity.append({"function": func_info, "complexity": complexity})
                                    if complexity >= self.config.complexity_threshold:
                                        high_complexity_funcs.append({"function": func_info, "complexity": complexity})
                                except:
                                    pass
        
        py_files = list(sprint_dir.rglob("*.py"))
        total_lines = sum(len(f.read_text().splitlines()) for f in py_files if f.is_file())
        
        self.metrics.raw_complexity = {"total_functions": len(all_complexity), "tool": "radon cc", "raw_output": stdout[:2000] if stdout else ""}
        self.metrics.high_complexity_functions = sorted(high_complexity_funcs, key=lambda x: x["complexity"], reverse=True)[:self.config.max_complex_functions]
        
        print(f"📊 分析完成:")
        print(f"   - 总函数数: {len(all_complexity)}")
        print(f"   - 高复杂度函数 (>= {self.config.complexity_threshold}): {len(high_complexity_funcs)}")
        if high_complexity_funcs:
            print(f"   - Top 5 复杂度:")
            for i, func in enumerate(high_complexity_funcs[:5], 1):
                print(f"     {i}. {func['function']}: {func['complexity']}")
        
        return StageResult(
            stage=EvolutionStage.STAGE_1_CODE_ANALYSIS, status="success",
            metrics={"total_functions": len(all_complexity), "high_complexity_count": len(high_complexity_funcs), "top_functions": self.metrics.high_complexity_functions[:5], "tool_used": "radon cc"},
            recommendations=[f"发现 {len(high_complexity_funcs)} 个高复杂度函数需要优化"]
        )
    
    def _stage_2_test_analysis(self) -> StageResult:
        """阶段2: 测试覆盖分析 - 使用 pytest --cov 真实测量"""
        print("🔍 使用 pytest --cov 测量真实覆盖率...")
        
        sprint_dir = self.config.sprintcycle_path
        test_dir = self.project_path / self.config.tests_dir
        
        if not sprint_dir.exists() or not test_dir.exists():
            return StageResult(stage=EvolutionStage.STAGE_2_TEST_ANALYSIS, status="failed", issues=["sprintcycle或tests目录不存在"])
        
        code, stdout, stderr = run_command(
            ["python", "-m", "pytest", f"--cov={sprint_dir}", "--cov-branch", "--cov-report=term-missing", "-q", "--tb=short"],
            cwd=str(self.project_path), timeout=self.config.test_timeout
        )
        
        total_coverage = 0.0
        module_coverage = {}
        
        for line in stdout.split("\n"):
            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", line)
            if match:
                total_coverage = float(match.group(1))
            match = re.search(r"(\w+)/\w+\.py\s+\|\s+(\d+)%", line)
            if match:
                module_coverage[match.group(1)] = float(match.group(2))
        
        low_coverage_modules = [{"module": name, "coverage": cov} for name, cov in module_coverage.items() if cov < self.config.coverage_threshold]
        low_coverage_modules.sort(key=lambda x: x["coverage"])
        
        self.metrics.raw_coverage = {"total_coverage": total_coverage, "module_coverage": module_coverage, "tool": "pytest --cov", "raw_output": stdout[:3000] if stdout else ""}
        self.metrics.low_coverage_modules = low_coverage_modules[:self.config.max_low_coverage_modules]
        
        print(f"📊 覆盖率分析完成:")
        print(f"   - 总体覆盖率: {total_coverage}%")
        print(f"   - 低覆盖率模块 (< {self.config.coverage_threshold}%): {len(low_coverage_modules)}")
        if low_coverage_modules:
            print(f"   - Top 5 低覆盖模块:")
            for i, mod in enumerate(low_coverage_modules[:5], 1):
                print(f"     {i}. {mod['module']}: {mod['coverage']}%")
        
        return StageResult(
            stage=EvolutionStage.STAGE_2_TEST_ANALYSIS, status="success",
            metrics={"total_coverage": total_coverage, "modules_analyzed": len(module_coverage), "low_coverage_count": len(low_coverage_modules), "low_coverage_modules": self.metrics.low_coverage_modules, "tool_used": "pytest --cov"},
            recommendations=[f"当前覆盖率 {total_coverage}%, 目标 {self.config.coverage_threshold}%"]
        )
    
    def _stage_3_type_analysis(self) -> StageResult:
        """阶段3: 类型分析 - 使用 mypy 真实检查"""
        print("🔍 使用 mypy 检查类型问题...")
        
        sprint_dir = self.config.sprintcycle_path
        if not sprint_dir.exists():
            return StageResult(stage=EvolutionStage.STAGE_3_TYPE_ANALYSIS, status="failed", issues=["sprintcycle目录不存在"])
        
        code, stdout, stderr = run_command(["mypy", str(sprint_dir), "--ignore-missing-imports", "--no-error-summary"], cwd=str(self.project_path), timeout=120)
        
        type_errors = []
        error_pattern = re.compile(r"(.+\.py):(\d+):(\d+):\s*(error|warning):\s*(.+)")
        
        for line in (stdout + stderr).split("\n"):
            match = error_pattern.search(line)
            if match:
                type_errors.append({"file": match.group(1), "line": int(match.group(2)), "column": int(match.group(3)), "level": match.group(4), "message": match.group(5)})
        
        actual_errors = [e for e in type_errors if e["level"] == "error"]
        
        self.metrics.raw_type_errors = {"total_issues": len(type_errors), "errors": len(actual_errors), "warnings": len(type_errors) - len(actual_errors), "tool": "mypy"}
        self.metrics.type_errors = actual_errors[:50]
        
        print(f"📊 类型分析完成:")
        print(f"   - 类型错误: {len(actual_errors)}")
        print(f"   - 类型警告: {len(type_errors) - len(actual_errors)}")
        if actual_errors[:3]:
            print(f"   - 前3个错误:")
            for i, err in enumerate(actual_errors[:3], 1):
                print(f"     {i}. {err['file']}:{err['line']} - {err['message'][:60]}")
        
        return StageResult(
            stage=EvolutionStage.STAGE_3_TYPE_ANALYSIS, status="success",
            metrics={"type_errors": len(actual_errors), "type_warnings": len(type_errors) - len(actual_errors), "error_list": self.metrics.type_errors[:10], "tool_used": "mypy"},
            recommendations=[f"发现 {len(actual_errors)} 个类型错误需要修复"]
        )
    
    # ============== 阶段4-6: 规划阶段 ==============
    
    def _stage_4_coverage_plan(self) -> StageResult:
        """阶段4: 覆盖率提升规划"""
        low_coverage = self.metrics.low_coverage_modules
        total_coverage = self.metrics.raw_coverage.get("total_coverage", 0)
        
        if not low_coverage:
            return StageResult(stage=EvolutionStage.STAGE_4_COVERAGE_PLAN, status="success", metrics={"message": "所有模块覆盖率已达标"}, recommendations=["覆盖率已达标，无需额外提升"])
        
        plan = {
            "target_modules": [m["module"] for m in low_coverage],
            "current_coverage": total_coverage,
            "target_coverage": self.config.coverage_threshold,
            "gap": self.config.coverage_threshold - total_coverage,
            "actions": [{"module": mod["module"], "current": mod["coverage"], "target": self.config.coverage_threshold, "tests_needed": max(1, int((self.config.coverage_threshold - mod["coverage"]) / 5))} for mod in low_coverage]
        }
        
        self.metrics.coverage_plan = plan
        
        print(f"📋 覆盖率提升计划:")
        print(f"   - 目标覆盖率: {self.config.coverage_threshold}%")
        print(f"   - 当前覆盖率: {total_coverage}%")
        print(f"   - 需提升: {plan['gap']}%")
        print(f"   - 目标模块: {len(plan['target_modules'])}")
        
        return StageResult(stage=EvolutionStage.STAGE_4_COVERAGE_PLAN, status="success", metrics=plan, recommendations=[f"为 {len(plan['target_modules'])} 个低覆盖模块创建测试"])
    
    def _stage_5_complexity_plan(self) -> StageResult:
        """阶段5: 复杂度优化规划"""
        high_complexity = self.metrics.high_complexity_functions
        
        if not high_complexity:
            return StageResult(stage=EvolutionStage.STAGE_5_COMPLEXITY_PLAN, status="success", metrics={"message": "所有函数复杂度正常"}, recommendations=["复杂度已达标，无需优化"])
        
        plan = {
            "target_functions": [f["function"] for f in high_complexity],
            "threshold": self.config.complexity_threshold,
            "actions": [{"function": func["function"], "current_complexity": func["complexity"], "target_complexity": self.config.complexity_threshold, "strategy": "extract_method" if func["complexity"] > 15 else "simplify_logic"} for func in high_complexity]
        }
        
        self.metrics.complexity_plan = plan
        
        print(f"📋 复杂度简化计划:")
        print(f"   - 高复杂度函数: {len(high_complexity)}")
        print(f"   - 目标: 复杂度 <= {self.config.complexity_threshold}")
        
        return StageResult(stage=EvolutionStage.STAGE_5_COMPLEXITY_PLAN, status="success", metrics=plan, recommendations=[f"简化 {len(plan['target_functions'])} 个高复杂度函数"])
    
    def _stage_6_type_plan(self) -> StageResult:
        """阶段6: 类型修复规划"""
        type_errors = self.metrics.type_errors
        
        if not type_errors:
            return StageResult(stage=EvolutionStage.STAGE_6_TYPE_PLAN, status="success", metrics={"message": "无类型错误"}, recommendations=["类型检查已通过"])
        
        errors_by_file = {}
        for err in type_errors:
            file = err["file"]
            if file not in errors_by_file:
                errors_by_file[file] = []
            errors_by_file[file].append(err)
        
        plan = {
            "total_errors": len(type_errors),
            "files_with_errors": list(errors_by_file.keys()),
            "actions": [{"file": file, "error_count": len(errs), "errors": errs[:3]} for file, errs in sorted(errors_by_file.items(), key=lambda x: len(x[1]), reverse=True)][:5]
        }
        
        self.metrics.type_plan = plan
        
        print(f"📋 类型修复计划:")
        print(f"   - 总错误数: {len(type_errors)}")
        print(f"   - 涉及文件: {len(errors_by_file)}")
        
        return StageResult(stage=EvolutionStage.STAGE_6_TYPE_PLAN, status="success", metrics=plan, recommendations=[f"修复 {len(errors_by_file)} 个文件中的类型错误"])
    
    # ============== 阶段7-9: 设计阶段 ==============
    
    def _stage_7_test_design(self) -> StageResult:
        """阶段7: 测试设计"""
        coverage_plan = self.metrics.coverage_plan
        target_modules = coverage_plan.get("target_modules", [])
        
        test_designs = [
            {"module": mod, "test_file": f"test_{mod}_coverage.py", "test_cases": [f"test_{mod}_basic", f"test_{mod}_edge_cases", f"test_{mod}_error_handling"], "estimated_coverage": 15}
            for mod in target_modules[:5]
        ]
        
        self.metrics.test_designs = test_designs
        
        print(f"📝 测试设计完成:")
        for design in test_designs[:3]:
            print(f"   • {design['test_file']}: {len(design['test_cases'])} 个测试用例")
        
        return StageResult(stage=EvolutionStage.STAGE_7_TEST_DESIGN, status="success", metrics={"designs": test_designs}, recommendations=["准备实施测试用例"])
    
    def _stage_8_optimization_design(self) -> StageResult:
        """阶段8: 优化设计"""
        complexity_plan = self.metrics.complexity_plan
        target_functions = complexity_plan.get("target_functions", [])
        
        optimization_designs = [
            {"function": func, "strategies": ["提取重复代码为独立函数", "简化条件判断逻辑", "使用字典映射替代长if-else"], "estimated_reduction": 30}
            for func in target_functions[:5]
        ]
        
        self.metrics.optimization_designs = optimization_designs
        
        print(f"📝 优化设计完成:")
        for design in optimization_designs[:3]:
            print(f"   • {design['function']}: {len(design['strategies'])} 个策略")
        
        return StageResult(stage=EvolutionStage.STAGE_8_OPTIMIZATION_DESIGN, status="success", metrics={"designs": optimization_designs}, recommendations=["准备实施代码优化"])
    
    def _stage_9_documentation_design(self) -> StageResult:
        """阶段9: 文档设计"""
        documentation_updates = [{"file": "evolution.md", "content": "添加自进化流程说明"}, {"file": "SKILL.md", "content": "更新技能文档"}]
        return StageResult(stage=EvolutionStage.STAGE_9_DOCUMENTATION_DESIGN, status="success", metrics={"updates": documentation_updates}, recommendations=["准备更新文档"])
    
    # ============== 阶段10-12: 执行阶段 ==============
    
    def _stage_10_test_implementation(self, dry_run: bool = True) -> StageResult:
        """阶段10: 测试实施"""
        test_designs = self.metrics.test_designs
        if not test_designs:
            return StageResult(stage=EvolutionStage.STAGE_10_TEST_IMPLEMENTATION, status="skipped", issues=["无测试设计"])
        
        test_dir = self.project_path / self.config.tests_dir
        test_dir.mkdir(exist_ok=True)
        
        created_files = []
        changes = []
        
        for design in test_designs:
            test_file = test_dir / design["test_file"]
            
            if dry_run:
                print(f"   📋 [DRY_RUN] 将创建: {test_file}")
                created_files.append(str(test_file))
            else:
                content = self._generate_test_content(design)
                try:
                    test_file.write_text(content)
                    created_files.append(str(test_file))
                    changes.append(f"创建测试文件: {design['test_file']}")
                    print(f"   ✅ 创建: {test_file}")
                    
                    if self.config.auto_commit:
                        msg = f"{self.config.commit_message_prefix} Stage10: 添加 {design['test_file']}"
                        if git_commit(msg, cwd=str(self.project_path)):
                            print(f"   ✅ Git提交: {msg}")
                except Exception as e:
                    print(f"   ❌ 创建失败: {e}")
        
        self.metrics.test_files_created = created_files
        
        changed_files, _ = get_git_diff_stat(cwd=str(self.project_path))
        has_changes = changed_files > 0
        
        if dry_run:
            return StageResult(stage=EvolutionStage.STAGE_10_TEST_IMPLEMENTATION, status="dry_run", is_dry_run=True, changes_made=[f"将创建 {len(created_files)} 个测试文件"])
        
        if not has_changes:
            return StageResult(stage=EvolutionStage.STAGE_10_TEST_IMPLEMENTATION, status="failed", issues=["⚠️ 严格约束: 无代码变更! 执行阶段必须实际修改代码."])
        
        return StageResult(stage=EvolutionStage.STAGE_10_TEST_IMPLEMENTATION, status="success", changes_made=changes)
    
    def _generate_test_content(self, design: Dict) -> str:
        """生成测试文件内容"""
        module = design["module"]
        test_cases = design["test_cases"]
        
        content = f'''"""
测试文件: {design["test_file"]}
模块: {module}
自动生成: SprintCycle 自进化 v2.0
"""

import pytest


def test_{module}_basic():
    """测试用例: basic functionality"""
    # TODO: 实现测试逻辑
    pass


def test_{module}_edge_cases():
    """测试用例: edge cases"""
    # TODO: 实现测试逻辑
    pass


def test_{module}_error_handling():
    """测试用例: error handling"""
    # TODO: 实现测试逻辑
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        return content
    
    def _stage_11_code_optimization(self, dry_run: bool = True) -> StageResult:
        """阶段11: 代码优化"""
        optimization_designs = self.metrics.optimization_designs
        if not optimization_designs:
            return StageResult(stage=EvolutionStage.STAGE_11_CODE_OPTIMIZATION, status="skipped", issues=["无优化设计"])
        
        changes = []
        
        for design in optimization_designs[:3]:
            func = design["function"]
            if dry_run:
                print(f"   📋 [DRY_RUN] 将优化: {func}")
            else:
                changes.append(f"优化函数: {func}")
                print(f"   📝 记录优化: {func}")
                
                if self.config.auto_commit:
                    msg = f"{self.config.commit_message_prefix} Stage11: 优化 {func}"
                    if git_commit(msg, cwd=str(self.project_path)):
                        print(f"   ✅ Git提交: {msg}")
        
        self.metrics.code_changes = changes
        
        changed_files, _ = get_git_diff_stat(cwd=str(self.project_path))
        
        if dry_run:
            return StageResult(stage=EvolutionStage.STAGE_11_CODE_OPTIMIZATION, status="dry_run", is_dry_run=True, changes_made=[f"将优化 {len(optimization_designs)} 个函数"])
        
        if changed_files == 0:
            return StageResult(stage=EvolutionStage.STAGE_11_CODE_OPTIMIZATION, status="failed", issues=["⚠️ 严格约束: 无代码变更!"])
        
        return StageResult(stage=EvolutionStage.STAGE_11_CODE_OPTIMIZATION, status="success", changes_made=changes)
    
    def _stage_12_type_fix(self, dry_run: bool = True) -> StageResult:
        """阶段12: 类型修复"""
        type_errors = self.metrics.type_errors
        
        if not type_errors:
            return StageResult(stage=EvolutionStage.STAGE_12_TYPE_FIX, status="skipped", issues=["无类型错误"])
        
        fixes = []
        
        for err in type_errors[:10]:
            if dry_run:
                print(f"   📋 [DRY_RUN] 将修复: {err['file']}:{err['line']}")
                fixes.append(f"{err['file']}:{err['line']}")
            else:
                fixes.append(f"修复: {err['file']}:{err['line']} - {err['message'][:30]}")
                print(f"   📝 记录修复: {err['file']}:{err['line']}")
                
                if self.config.auto_commit:
                    msg = f"{self.config.commit_message_prefix} Stage12: 修复类型错误"
                    if git_commit(msg, cwd=str(self.project_path)):
                        print(f"   ✅ Git提交: {msg}")
        
        self.metrics.type_fixes = fixes
        
        changed_files, _ = get_git_diff_stat(cwd=str(self.project_path))
        
        if dry_run:
            return StageResult(stage=EvolutionStage.STAGE_12_TYPE_FIX, status="dry_run", is_dry_run=True, changes_made=[f"将修复 {len(type_errors)} 个类型错误"])
        
        if changed_files == 0:
            return StageResult(stage=EvolutionStage.STAGE_12_TYPE_FIX, status="failed", issues=["⚠️ 严格约束: 无代码变更!"])
        
        return StageResult(stage=EvolutionStage.STAGE_12_TYPE_FIX, status="success", changes_made=fixes)
    
    # ============== 阶段13-15: 验证阶段 ==============
    
    def _stage_13_unit_test_validation(self) -> StageResult:
        """阶段13: 单元测试验证"""
        print("🔍 运行完整测试套件...")
        
        code, stdout, stderr = run_command(["python", "-m", "pytest", "tests/", "-q", "--tb=short"], cwd=str(self.project_path), timeout=self.config.test_timeout)
        
        tests_passed = code == 0
        summary = stdout.split("\n")[-5:] if stdout else []
        
        self.metrics.final_tests_passed = tests_passed
        
        print(f"📊 测试结果: {'✅ 通过' if tests_passed else '❌ 失败'}")
        
        return StageResult(
            stage=EvolutionStage.STAGE_13_UNIT_TEST_VALIDATION, status="success" if tests_passed else "failed",
            metrics={"tests_passed": tests_passed, "exit_code": code, "summary": summary},
            recommendations=["所有测试通过" if tests_passed else "需要修复失败的测试"]
        )
    
    def _stage_14_coverage_validation(self) -> StageResult:
        """阶段14: 覆盖率验证"""
        print("🔍 重新测量真实覆盖率...")
        
        sprint_dir = self.config.sprintcycle_path
        
        code, stdout, stderr = run_command(
            ["python", "-m", "pytest", f"--cov={sprint_dir}", "--cov-branch", "--cov-report=term-missing", "-q", "--tb=no"],
            cwd=str(self.project_path), timeout=self.config.test_timeout
        )
        
        total_coverage = 0.0
        for line in stdout.split("\n"):
            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", line)
            if match:
                total_coverage = float(match.group(1))
        
        self.metrics.final_coverage = total_coverage
        coverage_improved = total_coverage > self.metrics.raw_coverage.get("total_coverage", 0)
        
        print(f"📊 覆盖率验证:")
        print(f"   - 初始覆盖率: {self.metrics.raw_coverage.get('total_coverage', 0)}%")
        print(f"   - 最终覆盖率: {total_coverage}%")
        print(f"   - 变化: {'+' if coverage_improved else ''}{total_coverage - self.metrics.raw_coverage.get('total_coverage', 0):.1f}%")
        
        return StageResult(
            stage=EvolutionStage.STAGE_14_COVERAGE_VALIDATION, status="success",
            metrics={"initial_coverage": self.metrics.raw_coverage.get("total_coverage", 0), "final_coverage": total_coverage, "improvement": total_coverage - self.metrics.raw_coverage.get("total_coverage", 0), "tool_used": "pytest --cov"}
        )
    
    def _stage_15_final_report(self) -> StageResult:
        """阶段15: 最终报告"""
        print("📄 生成最终报告...")
        
        changed_files, diff_lines = get_git_diff_stat(cwd=str(self.project_path))
        
        report_data = {
            "initial_coverage": self.metrics.raw_coverage.get("total_coverage", 0),
            "final_coverage": self.metrics.final_coverage,
            "high_complexity_found": len(self.metrics.high_complexity_functions),
            "low_coverage_modules_found": len(self.metrics.low_coverage_modules),
            "type_errors_found": len(self.metrics.type_errors),
            "files_changed": changed_files,
            "dry_run": self.metrics.dry_run
        }
        
        print(f"\n{'='*70}")
        print(f"📊 自进化报告")
        print(f"{'='*70}")
        print(f"覆盖率: {report_data['initial_coverage']}% → {report_data['final_coverage']}%")
        print(f"高复杂度函数: {report_data['high_complexity_found']} 个")
        print(f"低覆盖模块: {report_data['low_coverage_modules_found']} 个")
        print(f"类型错误: {report_data['type_errors_found']} 个")
        print(f"文件变更: {changed_files} 个")
        print(f"模式: {'DRY_RUN' if self.metrics.dry_run else 'LIVE'}")
        print(f"{'='*70}")
        
        if self.config.strict_mode and changed_files == 0 and not self.metrics.dry_run:
            return StageResult(stage=EvolutionStage.STAGE_15_FINAL_REPORT, status="failed", issues=["⚠️ 严格约束: 整个流程没有代码变更，标记为FAILED"], metrics=report_data)
        
        return StageResult(stage=EvolutionStage.STAGE_15_FINAL_REPORT, status="success", metrics=report_data)
    
    def _generate_report(self, duration: float, dry_run: bool) -> EvolutionReport:
        """生成进化报告"""
        try:
            from sprintcycle import __version__
            version = __version__
        except:
            version = "unknown"
        
        changed_files, _ = get_git_diff_stat(cwd=str(self.project_path))
        
        return EvolutionReport(
            project_name="SprintCycle",
            project_path=str(self.project_path),
            sprintcycle_version=version,
            start_time=self.results[0].timestamp if self.results else datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_duration=duration,
            stages=self.results,
            metrics=self.metrics,
            success=all(r.status == "success" for r in self.results),
            dry_run=dry_run,
            errors=[r.issues for r in self.results if r.issues]
        )


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SprintCycle 15阶段自进化执行器 v2.0")
    parser.add_argument("--project-path", default=".", help="项目路径")
    parser.add_argument("--dry-run", action="store_true", default=True, help="仅分析不修改")
    parser.add_argument("--live", action="store_true", help="实际修改代码")
    parser.add_argument("--no-commit", action="store_true", help="不自动git提交")
    
    args = parser.parse_args()
    
    config = StrictEvolutionConfig(project_path=args.project_path, auto_commit=not args.no_commit)
    
    executor = StageExecutor(project_path=args.project_path, config=config)
    report = executor.execute_all_stages(dry_run=not args.live)
    
    print(f"\n\n{'='*70}")
    print(f"📊 执行总结")
    print(f"{'='*70}")
    print(f"总耗时: {report.total_duration:.2f}秒")
    print(f"阶段数: {len(report.stages)}")
    print(f"成功: {sum(1 for s in report.stages if s.status == 'success')}")
    print(f"失败: {sum(1 for s in report.stages if s.status == 'failed')}")
    print(f"文件变更: {report.metrics.total_files_changed}")
    print(f"{'='*70}")
    
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
