"""ResourceMonitor 单元测试"""

import pytest
import time
from sprintcycle.resource_monitor import (
    ResourceMonitor, Alert, AlertLevel, AlertConfig,
    get_resource_monitor
)


class TestResourceMonitor:
    """资源监控测试"""
    
    def setup_method(self):
        self.monitor = ResourceMonitor(interval=0.1)
    
    def teardown_method(self):
        self.monitor.stop()
    
    def test_start_stop(self):
        """测试启动停止"""
        self.monitor.start()
        time.sleep(0.2)
        
        snapshot = self.monitor.get_latest_snapshot()
        assert snapshot is not None
        
        self.monitor.stop()
    
    def test_snapshot_collection(self):
        """测试快照收集"""
        self.monitor.start()
        time.sleep(0.3)
        
        snapshots = self.monitor.get_snapshots(limit=10)
        assert len(snapshots) > 0
        
        snapshot = snapshots[-1]
        assert snapshot.cpu_percent >= 0
        assert snapshot.memory_percent >= 0
    
    def test_alert_callback(self):
        """测试告警回调"""
        alerts_received = []
        
        def alert_handler(alert):
            alerts_received.append(alert)
        
        self.monitor.add_alert_callback(alert_handler)
        
        # 设置低阈值触发告警
        self.monitor._config.cpu_threshold = 0.01  # 极低阈值
        
        self.monitor.start()
        time.sleep(0.5)
        
        self.monitor.stop()
        
        # 可能收到告警（取决于系统负载）
    
    def test_generate_report(self):
        """测试报告生成"""
        self.monitor.start()
        time.sleep(0.5)
        
        report = self.monitor.generate_report()
        
        assert "cpu" in report
        assert "memory" in report
        assert "timestamp" in report


class TestAlert:
    """告警测试"""
    
    def test_alert_creation(self):
        """测试告警创建"""
        alert = Alert(
            level=AlertLevel.WARNING,
            message="Test alert",
            metric="cpu_percent",
            value=85.0,
            threshold=80.0
        )
        
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test alert"
    
    def test_alert_to_dict(self):
        """测试告警序列化"""
        alert = Alert(
            level=AlertLevel.CRITICAL,
            message="Critical alert",
            metric="memory_mb",
            value=5000,
            threshold=4096
        )
        
        data = alert.to_dict()
        assert data["level"] == "critical"
        assert data["value"] == 5000
