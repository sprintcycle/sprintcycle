"""Benchmark 单元测试"""

import pytest
import time
from sprintcycle.benchmark import (
    BenchmarkSuite, BenchmarkResult, 
    get_benchmark_suite, get_performance_monitor
)


class TestBenchmarkSuite:
    """基准测试套件测试"""
    
    def setup_method(self):
        self.suite = BenchmarkSuite(name="test_suite")
    
    def test_add_benchmark(self):
        """测试添加基准测试"""
        def dummy_func():
            time.sleep(0.001)
            return 42
        
        result = self.suite.add_benchmark("dummy", dummy_func, iterations=5)
        
        assert result.name == "dummy"
        assert result.iterations == 5
        assert result.duration_mean > 0
    
    def test_set_threshold(self):
        """测试设置阈值"""
        self.suite.set_threshold("test_bench", 0.1)
        assert self.suite.thresholds["test_bench"] == 0.1
    
    def test_check_regression_pass(self):
        """测试回归检测通过"""
        result = BenchmarkResult(
            name="fast",
            iterations=10,
            duration_total=0.1,
            duration_mean=0.01,
            duration_median=0.01,
            duration_std=0.001,
            duration_min=0.008,
            duration_max=0.015,
            rps=100
        )
        
        self.suite.set_threshold("fast", 0.5)  # 高阈值
        passed, msg = self.suite.check_regression(result)
        
        assert passed is True
    
    def test_check_regression_fail(self):
        """测试回归检测失败"""
        result = BenchmarkResult(
            name="slow",
            iterations=10,
            duration_total=1.0,
            duration_mean=0.1,
            duration_median=0.1,
            duration_std=0.01,
            duration_min=0.08,
            duration_max=0.12,
            rps=10
        )
        
        self.suite.set_threshold("slow", 0.05)  # 低阈值
        passed, msg = self.suite.check_regression(result)
        
        assert passed is False
    
    def test_generate_report(self):
        """测试生成报告"""
        def dummy():
            time.sleep(0.001)
        
        self.suite.add_benchmark("test", dummy, iterations=3)
        self.suite.set_threshold("test", 1.0)
        
        report = self.suite.generate_report()
        
        assert "suite_name" in report
        assert "summary" in report
        assert "results" in report


class TestPerformanceMonitor:
    """性能监控测试"""
    
    def setup_method(self):
        self.monitor = get_performance_monitor()
    
    def test_timer(self):
        """测试计时器"""
        self.monitor.start_timer("test_op")
        time.sleep(0.01)
        duration = self.monitor.stop_timer("test_op")
        
        assert duration is not None
        assert duration >= 0.01
    
    def test_record(self):
        """测试记录"""
        self.monitor.record("metric1", 42.5)
        self.monitor.record("metric1", 43.5)
        
        stats = self.monitor.get_stats("metric1")
        assert stats["count"] == 2
        assert stats["mean"] == 43.0
