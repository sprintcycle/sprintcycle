"""
SprintCycle Integrations Module

集成模块，用于将 SprintCycle 与其他系统/框架集成。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class EvolutionTrigger:
    """进化触发器定义"""
    name: str
    condition: str
    threshold: Optional[Dict[str, Any]] = None
    enabled: bool = True
    
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """评估触发条件是否满足"""
        # Simple evaluation for now
        if not self.condition:
            return False
        return True


class SprintEvolutionIntegration:
    """SprintCycle 进化集成器"""
    
    DEFAULT_TARGETS = [
        "sprintcycle/config/",
        "sprintcycle/evolution/",
    ]
    
    def __init__(self, config=None):
        """
        初始化集成器
        
        Args:
            config: RuntimeConfig 实例
        """
        from sprintcycle.config.runtime_config import RuntimeConfig
        self.config = config or RuntimeConfig()
        self.evolution_history: List[Dict[str, Any]] = []
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """获取进化状态"""
        return {
            "history_count": len(self.evolution_history),
            "evolution_enabled": getattr(self.config, 'evolution_enabled', True),
            "default_targets": self.DEFAULT_TARGETS,
        }
    
    def trigger_after_sprint(
        self,
        sprint_metrics: Dict[str, Any],
        targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Sprint 完成后触发进化检查
        
        Args:
            sprint_metrics: Sprint 指标
            targets: 目标路径列表
            
        Returns:
            触发结果
        """
        targets = targets or self.DEFAULT_TARGETS
        evolved_count = 0
        
        for target in targets:
            # 简单检查目标是否存在
            import os
            if os.path.exists(target):
                evolved_count += 1
        
        return {
            "evolved": evolved_count,
            "history_count": len(self.evolution_history),
            "sprint_number": sprint_metrics.get("sprint_number", 0),
        }
    
    def __repr__(self) -> str:
        return f"SprintEvolutionIntegration(history={len(self.evolution_history)})"
