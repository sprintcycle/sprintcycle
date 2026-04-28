"""
SprintCycle 资源监控模块
运行时 CPU/内存追踪、异常告警机制
"""

import os
import threading
import time
import psutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .state_manager import StateScope, get_state_manager


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceSnapshot:
    """资源快照"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float = 0
    disk_io_write_mb: float = 0
    network_sent_mb: float = 0
    network_recv_mb: float = 0
    thread_count: int = 0
    process_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_available_mb": self.memory_available_mb,
            "disk_io_read_mb": self.disk_io_read_mb,
            "disk_io_write_mb": self.disk_io_write_mb,
            "network_sent_mb": self.network_sent_mb,
            "network_recv_mb": self.network_recv_mb,
            "thread_count": self.thread_count,
            "process_count": self.process_count
        }


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "message": self.message,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp
        }


@dataclass
class AlertConfig:
    """告警配置"""
    cpu_threshold: float = 80.0      # CPU 使用率阈值
    memory_threshold: float = 80.0   # 内存使用率阈值
    memory_mb_threshold: float = 4096  # 内存绝对值阈值(MB)
    disk_threshold: float = 90.0     # 磁盘使用率阈值
    

class ResourceMonitor:
    """
    资源监控器
    
    功能:
    - CPU 使用率追踪
    - 内存使用追踪
    - 磁盘 I/O 监控
    - 网络 I/O 监控
    - 异常告警机制
    """
    
    def __init__(self, config: Optional[AlertConfig] = None, interval: float = 1.0):
        self._config = config or AlertConfig()
        self._interval = interval
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._snapshots: List[ResourceSnapshot] = []
        self._alerts: List[Alert] = []
        self._alert_history: List[Alert] = []
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._max_snapshots = 1000
        self._max_alerts = 100
        self._process = psutil.Process(os.getpid())
        self._last_disk_io = self._process.io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._lock = threading.RLock()
        self._state_manager = get_state_manager()
    
    def start(self) -> None:
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                snapshot = self._collect_snapshot()
                
                with self._lock:
                    self._snapshots.append(snapshot)
                    if len(self._snapshots) > self._max_snapshots:
                        self._snapshots = self._snapshots[-self._max_snapshots:]
                
                # 检查告警
                self._check_alerts(snapshot)
                
                # 更新状态
                self._update_state(snapshot)
                
            except Exception as e:
                print(f"Resource monitor error: {e}")
            
            time.sleep(self._interval)
    
    def _collect_snapshot(self) -> ResourceSnapshot:
        """收集资源快照"""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        
        # 进程内存
        process_mem = self._process.memory_info()
        
        # 磁盘 I/O
        try:
            io_counters = self._process.io_counters()
            disk_read_mb = (io_counters.read_bytes - self._last_disk_io.read_bytes) / (1024 * 1024)
            disk_write_mb = (io_counters.write_bytes - self._last_disk_io.write_bytes) / (1024 * 1024)
            self._last_disk_io = io_counters
        except:
            disk_read_mb = 0
            disk_write_mb = 0
        
        # 网络 I/O
        try:
            net_io = psutil.net_io_counters()
            net_sent_mb = (net_io.bytes_sent - self._last_net_io.bytes_sent) / (1024 * 1024)
            net_recv_mb = (net_io.bytes_recv - self._last_net_io.bytes_recv) / (1024 * 1024)
            self._last_net_io = net_io
        except:
            net_sent_mb = 0
            net_recv_mb = 0
        
        return ResourceSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu,
            memory_percent=mem.percent,
            memory_used_mb=process_mem.rss / (1024 * 1024),
            memory_available_mb=mem.available / (1024 * 1024),
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=net_sent_mb,
            network_recv_mb=net_recv_mb,
            thread_count=threading.active_count(),
            process_count=len(self._process.children(recursive=True)) + 1
        )
    
    def _check_alerts(self, snapshot: ResourceSnapshot) -> None:
        """检查告警"""
        alerts = []
        
        # CPU 告警
        if snapshot.cpu_percent > self._config.cpu_threshold:
            alerts.append(Alert(
                level=AlertLevel.WARNING if snapshot.cpu_percent < 95 else AlertLevel.CRITICAL,
                message=f"CPU 使用率过高: {snapshot.cpu_percent:.1f}%",
                metric="cpu_percent",
                value=snapshot.cpu_percent,
                threshold=self._config.cpu_threshold
            ))
        
        # 内存告警
        if snapshot.memory_percent > self._config.memory_threshold:
            alerts.append(Alert(
                level=AlertLevel.WARNING if snapshot.memory_percent < 95 else AlertLevel.CRITICAL,
                message=f"内存使用率过高: {snapshot.memory_percent:.1f}%",
                metric="memory_percent",
                value=snapshot.memory_percent,
                threshold=self._config.memory_threshold
            ))
        
        if snapshot.memory_used_mb > self._config.memory_mb_threshold:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                message=f"进程内存过高: {snapshot.memory_used_mb:.1f}MB",
                metric="memory_used_mb",
                value=snapshot.memory_used_mb,
                threshold=self._config.memory_mb_threshold
            ))
        
        # 处理告警
        for alert in alerts:
            self._alerts.append(alert)
            self._alert_history.append(alert)
            
            if len(self._alert_history) > self._max_alerts:
                self._alert_history = self._alert_history[-self._max_alerts:]
            
            # 调用回调
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"Alert callback error: {e}")
    
    def _update_state(self, snapshot: ResourceSnapshot) -> None:
        """更新状态"""
        self._state_manager.set(StateScope.RESOURCE, "latest_snapshot", snapshot.to_dict())
        self._state_manager.set(StateScope.RESOURCE, "cpu_percent", snapshot.cpu_percent)
        self._state_manager.set(StateScope.RESOURCE, "memory_percent", snapshot.memory_percent)
        self._state_manager.set(StateScope.RESOURCE, "memory_used_mb", snapshot.memory_used_mb)
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加告警回调"""
        self._alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """移除告警回调"""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)
    
    def get_latest_snapshot(self) -> Optional[ResourceSnapshot]:
        """获取最新快照"""
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None
    
    def get_snapshots(self, limit: int = 100) -> List[ResourceSnapshot]:
        """获取快照列表"""
        with self._lock:
            return list(self._snapshots[-limit:])
    
    def get_alerts(self, limit: int = 50) -> List[Alert]:
        """获取告警列表"""
        with self._lock:
            return list(self._alerts[-limit:])
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        with self._lock:
            return list(self._alert_history[-limit:])
    
    def clear_alerts(self) -> None:
        """清除当前告警"""
        with self._lock:
            self._alerts.clear()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成资源报告"""
        snapshots = self.get_snapshots(limit=100)
        
        if not snapshots:
            return {"status": "no_data"}
        
        cpu_values = [s.cpu_percent for s in snapshots]
        mem_values = [s.memory_percent for s in snapshots]
        mem_mb_values = [s.memory_used_mb for s in snapshots]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "period": {
                "start": snapshots[0].timestamp,
                "end": snapshots[-1].timestamp,
                "duration_seconds": len(snapshots) * self._interval
            },
            "cpu": {
                "current": cpu_values[-1],
                "mean": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "current_percent": mem_values[-1],
                "current_mb": mem_mb_values[-1],
                "mean_percent": sum(mem_values) / len(mem_values),
                "max_percent": max(mem_values),
                "max_mb": max(mem_mb_values)
            },
            "threads": {
                "current": snapshots[-1].thread_count,
                "max": max(s.thread_count for s in snapshots)
            },
            "alerts": {
                "total": len(self._alert_history),
                "critical": len([a for a in self._alert_history if a.level == AlertLevel.CRITICAL]),
                "warning": len([a for a in self._alert_history if a.level == AlertLevel.WARNING])
            }
        }
    
    def save_report(self, path: Path) -> None:
        """保存报告到文件"""
        import json
        data = {
            "report": self.generate_report(),
            "snapshots": [s.to_dict() for s in self.get_snapshots()],
            "alerts": [a.to_dict() for a in self.get_alert_history()]
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 全局资源监控器
_resource_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor
