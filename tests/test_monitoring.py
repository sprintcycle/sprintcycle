"""
Tests for Monitoring Module - 监控模块测试

Coverage targets:
- sprintcycle/monitoring/dashboard.py
- sprintcycle/monitoring/metrics.py
"""

import pytest
from datetime import datetime, timedelta

from sprintcycle.monitoring.metrics import MetricsCollector, MetricPoint, ExecutionRecord


class TestMetricsCollector:
    """MetricsCollector tests"""

    def test_basic_creation(self):
        collector = MetricsCollector(retention_hours=24)
        assert collector.retention == timedelta(hours=24)

    def test_record_execution_start(self):
        collector = MetricsCollector(retention_hours=1)
        record = collector.record_execution_start(
            execution_id="exec-1",
            name="test-execution",
            agent_type="coder",
        )
        assert record.id == "exec-1"
        assert record.name == "test-execution"
        assert record.agent_type == "coder"
        assert record.status.value == "running"

    def test_record_execution_end(self):
        collector = MetricsCollector(retention_hours=1)
        collector.record_execution_start("exec-1", "test", "coder")
        from sprintcycle.execution.sprint_types import ExecutionStatus
        result = collector.record_execution_end("exec-1", ExecutionStatus.SUCCESS)
        assert result is not None
        assert result.status == ExecutionStatus.SUCCESS
        assert result.end_time is not None

    def test_record_execution_end_not_found(self):
        collector = MetricsCollector(retention_hours=1)
        result = collector.record_execution_end("nonexistent", None)
        assert result is None


class TestMetricPoint:
    """MetricPoint tests"""

    def test_basic_creation(self):
        point = MetricPoint(
            name="test_metric",
            value=42.0,
            timestamp=datetime.now(),
        )
        assert point.name == "test_metric"
        assert point.value == 42.0


class TestExecutionRecord:
    """ExecutionRecord tests"""

    def test_basic_creation(self):
        record = ExecutionRecord(
            id="exec-1",
            name="test",
            agent_type="coder",
        )
        assert record.id == "exec-1"
        assert record.agent_type == "coder"

    def test_duration_calculation(self):
        record = ExecutionRecord(
            id="exec-1",
            name="test",
            agent_type="coder",
            start_time=datetime.now(),
        )
        assert record.duration == 0.0
