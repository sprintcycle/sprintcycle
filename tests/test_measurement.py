"""
MeasurementProvider 测试
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from sprintcycle.evolution.measurement import (
    MeasurementProvider,
    MeasurementResult,
)


class TestMeasurementResult:
    """MeasurementResult 数据类测试"""

    def test_basic_creation(self):
        """测试基本构造"""
        result = MeasurementResult(
            correctness=0.9,
            performance=0.8,
            stability=0.85,
            code_quality=0.75,
            overall=0.82,
        )
        assert result.correctness == 0.9
        assert result.performance == 0.8
        assert result.stability == 0.85
        assert result.code_quality == 0.75
        assert result.overall == 0.82

    def test_to_dict(self):
        """测试转换为字典"""
        result = MeasurementResult(
            correctness=0.9,
            performance=0.8,
            overall=0.82,
        )
        d = result.to_dict()
        assert d["correctness"] == 0.9
        assert d["performance"] == 0.8
        assert d["overall"] == 0.82
        assert "details" in d
        assert "timestamp" in d

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "correctness": 0.85,
            "performance": 0.9,
            "stability": 0.8,
            "code_quality": 0.75,
            "overall": 0.82,
            "details": {"test": "data"},
            "timestamp": 1234567890.0,
        }
        result = MeasurementResult.from_dict(data)
        assert result.correctness == 0.85
        assert result.performance == 0.9
        assert result.details == {"test": "data"}
        assert result.timestamp == 1234567890.0

    def test_from_dict_defaults(self):
        """测试从字典创建使用默认值"""
        result = MeasurementResult.from_dict({})
        assert result.correctness == 0.0
        assert result.performance == 0.0
        assert result.overall == 0.0
        assert result.details == {}

    def test_bool_true(self):
        """测试 __bool__ 返回 True"""
        result = MeasurementResult(overall=0.6)
        assert bool(result) is True

    def test_bool_false(self):
        """测试 __bool__ 返回 False"""
        result = MeasurementResult(overall=0.4)
        assert bool(result) is False

    def test_bool_edge_case(self):
        """测试 __bool__ 边界情况"""
        result = MeasurementResult(overall=0.5)
        assert bool(result) is True


class TestMeasurementProvider:
    """MeasurementProvider 测试"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        provider = MeasurementProvider(repo_path="/test/path")
        assert provider.repo_path == "/test/path"
        assert provider.quality_gate_enabled is True
        assert provider.measurement_timeout == 300

    def test_custom_test_command(self):
        """测试自定义测试命令"""
        provider = MeasurementProvider(
            repo_path=".",
            test_command="python -m pytest tests/ --fast",
        )
        assert provider.test_command == "python -m pytest tests/ --fast"

    def test_custom_timeout(self):
        """测试自定义超时"""
        provider = MeasurementProvider(measurement_timeout=600)
        assert provider.measurement_timeout == 600

    def test_coverage_threshold(self):
        """测试覆盖率阈值"""
        provider = MeasurementProvider(coverage_threshold=0.8)
        assert provider.coverage_threshold == 0.8

    def test_quality_gate_disabled(self):
        """测试质量门禁用"""
        provider = MeasurementProvider(quality_gate_enabled=False)
        assert provider.quality_gate_enabled is False

    def test_with_runner(self):
        """测试自定义 runner"""
        mock_runner = MagicMock(return_value=(0, "passed", ""))
        provider = MeasurementProvider(runner=mock_runner)
        assert provider._runner == mock_runner

    def test_default_runner(self):
        """测试默认 runner"""
        provider = MeasurementProvider()
        result = provider._runner("echo test", cwd=".", timeout=10)
        assert result[0] == 0
        assert "test" in result[1]

    def test_default_runner_timeout(self):
        """测试默认 runner 超时"""
        provider = MeasurementProvider()
        result = provider._runner("sleep 100", cwd=".", timeout=1)
        assert result[0] == -1
        assert "timed out" in result[2]

    def test_get_history_empty(self):
        """测试空历史记录"""
        provider = MeasurementProvider()
        history = provider.get_history()
        assert history == []

    def test_get_latest_empty(self):
        """测试最新结果为空"""
        provider = MeasurementProvider()
        latest = provider.get_latest()
        assert latest is None

    def test_check_quality_gate_disabled(self):
        """测试质量门禁用状态"""
        provider = MeasurementProvider(quality_gate_enabled=False)
        result = MeasurementResult(overall=0.0)
        assert provider.check_quality_gate(result) is True

    def test_check_quality_gate_low_correctness(self):
        """测试质量门低正确率"""
        provider = MeasurementProvider(quality_gate_enabled=True)
        result = MeasurementResult(correctness=0.3, overall=0.5)
        assert provider.check_quality_gate(result) is False

    def test_check_quality_gate_low_overall(self):
        """测试质量门低总分"""
        provider = MeasurementProvider(
            quality_gate_enabled=True,
            coverage_threshold=0.8,
        )
        result = MeasurementResult(correctness=0.8, overall=0.5)
        assert provider.check_quality_gate(result) is False

    def test_check_quality_gate_pass(self):
        """测试质量门通过"""
        provider = MeasurementProvider(
            quality_gate_enabled=True,
            coverage_threshold=0.5,
        )
        result = MeasurementResult(correctness=0.8, overall=0.6)
        assert provider.check_quality_gate(result) is True

    def test_compare(self):
        """测试比较"""
        provider = MeasurementProvider()
        baseline = MeasurementResult(correctness=0.7, performance=0.6, overall=0.65)
        current = MeasurementResult(correctness=0.8, performance=0.7, overall=0.75)
        delta = provider.compare(baseline, current)
        assert abs(delta["correctness_delta"] - 0.1) < 0.001
        assert abs(delta["performance_delta"] - 0.1) < 0.001
        assert abs(delta["overall_delta"] - 0.1) < 0.001

    def test_is_improved_true(self):
        """测试改进检测 - 改进"""
        provider = MeasurementProvider()
        baseline = MeasurementResult(overall=0.6)
        current = MeasurementResult(overall=0.7)
        assert provider.is_improved(baseline, current) is True

    def test_is_improved_false(self):
        """测试改进检测 - 未改进"""
        provider = MeasurementProvider()
        baseline = MeasurementResult(overall=0.7)
        current = MeasurementResult(overall=0.6)
        assert provider.is_improved(baseline, current) is False

    def test_measure_all(self):
        """测试测量所有指标"""
        mock_runner = MagicMock(return_value=(0, "10 passed", ""))
        provider = MeasurementProvider(runner=mock_runner)
        result = provider.measure_all()
        assert isinstance(result, MeasurementResult)
        assert 0.0 <= result.correctness <= 1.0
        assert 0.0 <= result.performance <= 1.0
        assert 0.0 <= result.stability <= 1.0
        assert 0.0 <= result.code_quality <= 1.0
        assert 0.0 <= result.overall <= 1.0

    def test_get_correctness_details(self):
        """测试获取正确率详情"""
        provider = MeasurementProvider()
        details = provider._get_correctness_details()
        assert "history_length" in details

    def test_get_quality_details(self):
        """测试获取质量详情"""
        provider = MeasurementProvider()
        details = provider._get_quality_details()
        assert isinstance(details, dict)

    def test_measure_correctness_passed(self):
        """测试正确率测量 - 通过"""
        mock_runner = MagicMock(return_value=(0, "5 passed", ""))
        provider = MeasurementProvider(runner=mock_runner)
        correctness = provider._measure_correctness()
        assert correctness == 1.0

    def test_measure_correctness_failed(self):
        """测试正确率测量 - 失败"""
        mock_runner = MagicMock(return_value=(1, "0 passed, 5 failed", ""))
        provider = MeasurementProvider(runner=mock_runner)
        correctness = provider._measure_correctness()
        assert correctness == 0.0

    def test_measure_correctness_exception(self):
        """测试正确率测量 - 异常"""
        mock_runner = MagicMock(side_effect=Exception("Test error"))
        provider = MeasurementProvider(runner=mock_runner)
        correctness = provider._measure_correctness()
        assert correctness == 0.5

    def test_measure_performance_no_history(self):
        """测试性能测量 - 无历史"""
        provider = MeasurementProvider()
        performance = provider._measure_performance()
        assert performance == 0.7

    def test_measure_performance_with_history(self):
        """测试性能测量 - 有历史"""
        mock_runner = MagicMock(return_value=(0, "passed", ""))
        provider = MeasurementProvider(runner=mock_runner)
        provider._history = [
            MeasurementResult(overall=0.6),
            MeasurementResult(overall=0.7),
        ]
        performance = provider._measure_performance()
        assert performance >= 0.7

    def test_measure_stability_all_pass(self):
        """测试稳定性测量 - 全通过"""
        provider = MeasurementProvider()
        provider._history = [
            MeasurementResult(correctness=0.9),
            MeasurementResult(correctness=0.9),
            MeasurementResult(correctness=0.9),
        ]
        stability = provider._measure_stability()
        assert stability == 1.0

    def test_measure_stability_with_failures(self):
        """测试稳定性测量 - 有失败"""
        provider = MeasurementProvider()
        provider._history = [
            MeasurementResult(correctness=0.3),
            MeasurementResult(correctness=0.3),
            MeasurementResult(correctness=0.3),
        ]
        stability = provider._measure_stability()
        assert stability < 1.0

    def test_measure_code_quality(self):
        """测试代码质量测量"""
        mock_runner = MagicMock(return_value=(0, "", ""))
        provider = MeasurementProvider(runner=mock_runner)
        quality = provider._measure_code_quality()
        assert quality == 0.7

    def test_measure_code_quality_exception(self):
        """测试代码质量测量 - 异常"""
        mock_runner = MagicMock(side_effect=Exception("Test error"))
        provider = MeasurementProvider(runner=mock_runner)
        quality = provider._measure_code_quality()
        assert quality == 0.5
