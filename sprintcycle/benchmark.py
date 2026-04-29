"""
SprintCycle 性能基准测试套件
建立性能回归检测机制
"""

import json
import time
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict

from .state_manager import StateScope, get_state_manager


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    duration_total: float
    duration_mean: float
    duration_median: float
    duration_std: float
    duration_min: float
    duration_max: float
    rps: float  # requests per second
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "duration_total": self.duration_total,
            "duration_mean": self.duration_mean,
            "duration_median": self.duration_median,
            "duration_std": self.duration_std,
            "duration_min": self.duration_min,
            "duration_max": self.duration_max,
            "rps": self.rps,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class BenchmarkSuite:
    """基准测试套件"""
    name: str
    thresholds: Dict[str, float] = field(default_factory=dict)
    baseline: Dict[str, Dict[str, float]] = field(default_factory=dict)
    results: List[BenchmarkResult] = field(default_factory=list)
    history: Dict[str, List[BenchmarkResult]] = field(default_factory=dict)
    
    def add_benchmark(self, name: str, func: Callable, iterations: int = 10, 
                      warmup: int = 2, metadata: Optional[Dict[str, Any]] = None) -> BenchmarkResult:
        """添加并运行基准测试"""
        # 预热
        for _ in range(warmup):
            func()
        
        # 运行测试
        durations = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            durations.append(end - start)
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            duration_total=sum(durations),
            duration_mean=statistics.mean(durations),
            duration_median=statistics.median(durations),
            duration_std=statistics.stdev(durations) if len(durations) > 1 else 0,
            duration_min=min(durations),
            duration_max=max(durations),
            rps=iterations / sum(durations) if sum(durations) > 0 else 0,
            metadata=metadata or {}
        )
        
        self.results.append(result)
        
        if name not in self.history:
            self.history[name] = []
        self.history[name].append(result)
        
        return result
    
    def set_threshold(self, benchmark_name: str, max_duration: float) -> None:
        """设置基准阈值"""
        self.thresholds[benchmark_name] = max_duration
    
    def set_baseline(self, benchmark_name: str, baseline: Dict[str, float]) -> None:
        """设置基准数据"""
        self.baseline[benchmark_name] = baseline
    
    def check_regression(self, result: BenchmarkResult) -> Tuple[bool, str]:
        """检查性能回归"""
        # 检查阈值
        if result.name in self.thresholds:
            threshold = self.thresholds[result.name]
            if result.duration_mean > threshold:
                return False, f"Duration {result.duration_mean:.4f}s exceeds threshold {threshold:.4f}s"
        
        # 检查基准对比
        if result.name in self.baseline:
            baseline = self.baseline[result.name]
            if "mean" in baseline:
                regression_pct = (result.duration_mean - baseline["mean"]) / baseline["mean"] * 100
                if regression_pct > 10:  # 10% 回归容忍度
                    return False, f"Regression {regression_pct:.1f}% vs baseline"
        
        return True, "OK"
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            "suite_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_benchmarks": len(self.results),
                "passed": sum(1 for r in self.results if self.check_regression(r)[0]),
                "failed": sum(1 for r in self.results if not self.check_regression(r)[0])
            },
            "results": [r.to_dict() for r in self.results],
            "recommendations": []
        }
        
        # 生成建议
        for result in self.results:
            passed, msg = self.check_regression(result)
            if not passed:
                report["recommendations"].append({
                    "benchmark": result.name,
                    "issue": msg,
                    "current": result.duration_mean,
                    "suggestion": f"Optimize {result.name} (current: {result.duration_mean:.4f}s)"
                })
        
        return report
    
    def save_results(self, path: Path) -> None:
        """保存结果到文件"""
        data = {
            "suite_name": self.name,
            "results": [r.to_dict() for r in self.results],
            "history": {k: [r.to_dict() for r in v] for k, v in self.history.items()},
            "timestamp": datetime.now().isoformat()
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_baseline(self, path: Path) -> None:
        """加载基准数据"""
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if "baseline" in data:
            self.baseline = data["baseline"]


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, float] = {}
        self._state_manager = get_state_manager()
    
    def start_timer(self, name: str) -> None:
        self._timers[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> Optional[float]:
        if name in self._timers:
            duration = time.perf_counter() - self._timers[name]
            self._metrics[name].append(duration)
            del self._timers[name]
            
            # 更新状态
            self._state_manager.set(StateScope.RESOURCE, f"perf.{name}", {
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
            return duration
        return None
    
    def record(self, name: str, value: float) -> None:
        self._metrics[name].append(value)
        self._state_manager.set(StateScope.RESOURCE, f"perf.{name}", {
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_stats(self, name: str) -> Dict[str, float]:
        if name not in self._metrics or not self._metrics[name]:
            return {}
        
        values = self._metrics[name]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        return {name: self.get_stats(name) for name in self._metrics}


# 全局基准测试套件
_default_suite: Optional[BenchmarkSuite] = None
_perf_monitor: Optional[PerformanceMonitor] = None


def get_benchmark_suite(name: str = "default") -> BenchmarkSuite:
    global _default_suite
    if _default_suite is None:
        _default_suite = BenchmarkSuite(name=name)
    return _default_suite


def get_performance_monitor() -> PerformanceMonitor:
    global _perf_monitor
    if _perf_monitor is None:
        _perf_monitor = PerformanceMonitor()
    return _perf_monitor
