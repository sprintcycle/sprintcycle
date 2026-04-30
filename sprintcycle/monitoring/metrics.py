"""
监控指标收集器 - SprintCycle 监控核心

功能：
1. 执行指标收集
2. 性能指标追踪
3. 统计数据聚合
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class ExecutionRecord:
    """执行记录"""
    id: str
    name: str
    agent_type: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_running(self) -> bool:
        return self.status == ExecutionStatus.RUNNING
    
    @property
    def is_complete(self) -> bool:
        return self.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": round(self.duration, 3),
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


class MetricsCollector:
    """
    指标收集器
    
    收集和聚合 SprintCycle 执行过程中的各种指标：
    1. 执行成功率
    2. 执行耗时
    3. 任务吞吐量
    4. Agent 性能
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        初始化指标收集器
        
        Args:
            retention_hours: 数据保留时间（小时）
        """
        self.retention = timedelta(hours=retention_hours)
        
        # 执行记录
        self._executions: Dict[str, ExecutionRecord] = {}
        self._execution_order: List[str] = []
        
        # 指标数据
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        
        # 计数器
        self._counters: Dict[str, float] = defaultdict(float)
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 启动清理任务
        asyncio.create_task(self._cleanup_loop())
    
    def record_execution_start(
        self,
        execution_id: str,
        name: str,
        agent_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutionRecord:
        """记录执行开始"""
        record = ExecutionRecord(
            id=execution_id,
            name=name,
            agent_type=agent_type,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self._executions[execution_id] = record
        self._execution_order.append(execution_id)
        
        logger.debug(f"Execution started: {execution_id}")
        return record
    
    def record_execution_end(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error: Optional[str] = None
    ) -> Optional[ExecutionRecord]:
        """记录执行结束"""
        record = self._executions.get(execution_id)
        if not record:
            logger.warning(f"Execution not found: {execution_id}")
            return None
        
        record.status = status
        record.end_time = datetime.now()
        record.duration = (record.end_time - record.start_time).total_seconds()
        record.error = error
        
        # 记录成功/失败指标
        metric_name = f"execution_{status.value}"
        self._increment_counter(metric_name, 1)
        
        if record.agent_type:
            self._increment_counter(f"execution_by_type_{record.agent_type}_{status.value}", 1)
        
        logger.debug(f"Execution ended: {execution_id}, status={status.value}, duration={record.duration:.3f}s")
        return record
    
    def record_execution(self, result: Dict[str, Any]) -> None:
        """记录执行结果（兼容接口）"""
        execution_id = result.get("id") or result.get("execution_id") or f"exec-{int(time.time() * 1000)}"
        name = result.get("name", execution_id)
        agent_type = result.get("agent_type", result.get("agent", "unknown"))
        status_str = result.get("status", "success")
        
        try:
            status = ExecutionStatus(status_str)
        except ValueError:
            status = ExecutionStatus.SUCCESS if result.get("success", True) else ExecutionStatus.FAILED
        
        record = self.record_execution_start(execution_id, name, agent_type)
        
        if status == ExecutionStatus.RUNNING:
            record.status = ExecutionStatus.SUCCESS if result.get("success", True) else ExecutionStatus.FAILED
            record.end_time = datetime.now()
            record.duration = (record.end_time - record.start_time).total_seconds()
        
        record.error = result.get("error")
        record.metadata = result.get("metadata", {})
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录指标"""
        point = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            labels=labels or {}
        )
        
        self._metrics[name].append(point)
    
    def _increment_counter(self, name: str, value: float = 1) -> None:
        """增加计数器"""
        self._counters[name] += value
    
    def get_counter(self, name: str) -> float:
        """获取计数器值"""
        return self._counters.get(name, 0)
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器"""
        self.record_metric(name, duration, MetricType.TIMER, labels)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        exec_status = self._calc_execution_status()
        duration_stats = self._calc_duration_stats()
        agent_stats = self._calc_agent_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "executions": exec_status,
            "duration": duration_stats,
            "counters": dict(self._counters),
            "agent_stats": agent_stats,
            "recent_executions": self._get_recent_executions(),
        }

    def _calc_execution_status(self) -> Dict[str, Any]:
        """计算执行状态统计"""
        records = list(self._executions.values())
        total = len(records)
        
        status_counts = {
            status: sum(1 for r in records if r.status == status)
            for status in ExecutionStatus
        }
        
        non_running = total - status_counts.get(ExecutionStatus.RUNNING, 0)
        success_rate = (
            status_counts.get(ExecutionStatus.SUCCESS, 0) / non_running * 100
            if non_running > 0 else 100.0
        )
        
        return {
            "total": total,
            "success": status_counts.get(ExecutionStatus.SUCCESS, 0),
            "failed": status_counts.get(ExecutionStatus.FAILED, 0),
            "running": status_counts.get(ExecutionStatus.RUNNING, 0),
            "success_rate": round(success_rate, 2),
        }

    def _calc_duration_stats(self) -> Dict[str, float]:
        """计算耗时统计"""
        durations = [r.duration for r in self._executions.values() if r.is_complete]
        
        if not durations:
            return {"avg": 0, "min": 0, "max": 0}
        
        return {
            "avg": round(sum(durations) / len(durations), 3),
            "min": round(min(durations), 3),
            "max": round(max(durations), 3),
        }

    def _calc_agent_stats(self) -> Dict[str, Any]:
        """计算Agent类型统计"""
        agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"success": 0, "failed": 0, "total_duration": 0.0, "count": 0})
        
        for record in self._executions.values():
            if not record.is_complete:
                continue
            
            agent_type = record.agent_type or "unknown"
            stats = agent_stats[agent_type]
            
            if record.status == ExecutionStatus.SUCCESS:
                stats["success"] += 1
            else:
                stats["failed"] += 1
            stats["total_duration"] += record.duration
            stats["count"] += 1
        
        result = {}
        for agent_type, stats in agent_stats.items():
            if stats["count"] > 0:
                result[agent_type] = {
                    "avg_duration": round(stats["total_duration"] / stats["count"], 3),
                    "success_rate": round(stats["success"] / stats["count"] * 100, 2),
                }
        
        return result

    def _get_recent_executions(self) -> List[Dict[str, Any]]:
        """获取最近执行记录"""
        return [
            self._executions[eid].to_dict()
            for eid in self._execution_order[-10:][::-1]
            if eid in self._executions
        ]



    def get_executions(
        self,
        status: Optional[ExecutionStatus] = None,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取执行记录"""
        records = list(self._executions.values())
        
        if status:
            records = [r for r in records if r.status == status]
        
        if agent_type:
            records = [r for r in records if r.agent_type == agent_type]
        
        # 按时间倒序
        records.sort(key=lambda r: r.start_time, reverse=True)
        
        return [r.to_dict() for r in records[:limit]]
    
    async def _cleanup_loop(self) -> None:
        """定期清理过期数据"""
        while True:
            try:
                await asyncio.sleep(self.retention.total_seconds() / 2)
                await self._cleanup()
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")
    
    async def _cleanup(self) -> None:
        """清理过期数据"""
        cutoff = datetime.now() - self.retention
        
        async with self._lock:
            # 清理执行记录
            expired_ids = [
                eid for eid, record in self._executions.items()
                if record.start_time < cutoff
            ]
            
            for eid in expired_ids:
                del self._executions[eid]
            
            # 清理指标数据
            for metric_name in list(self._metrics.keys()):
                self._metrics[metric_name] = [
                    p for p in self._metrics[metric_name]
                    if p.timestamp > cutoff
                ]
            
            # 清理执行顺序记录
            valid_ids = set(self._executions.keys())
            self._execution_order = [
                eid for eid in self._execution_order
                if eid in valid_ids
            ]
            
            if expired_ids:
                logger.debug(f"Cleaned up {len(expired_ids)} expired execution records")


# 全局指标收集器
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """设置全局指标收集器"""
    global _global_collector
    _global_collector = collector


__all__ = [
    "ExecutionStatus",
    "MetricType",
    "ExecutionRecord",
    "MetricPoint",
    "MetricsCollector",
    "get_metrics_collector",
    "set_metrics_collector",
]
