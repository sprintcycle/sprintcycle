"""
监控模块单元测试
"""
import pytest


class TestMonitoringImport:
    """监控模块导入测试"""

    def test_metrics_import(self):
        """测试 MetricsCollector 可正常导入"""
        from sprintcycle.monitoring.metrics import MetricsCollector
        assert MetricsCollector is not None

    def test_dashboard_import(self):
        """测试 dashboard 模块可正常导入"""
        from sprintcycle.monitoring import dashboard
        assert hasattr(dashboard, 'ExecutionResponse')
        assert hasattr(dashboard, 'StatsResponse')

    def test_module_all(self):
        """测试 __all__ 导出"""
        from sprintcycle.monitoring import __all__ as all_exports
        assert 'MetricsCollector' in all_exports
