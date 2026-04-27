"""SprintChain - 多 Sprint 链式管理器"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

from ..models.sprint import Sprint, SprintConfig, SprintStatus


class SprintChainStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SprintChainConfig:
    project_name: str
    prd_path: str
    sprint_configs: List[SprintConfig]
    auto_progress: bool = True
    max_retries: int = 3


class SprintChain:
    """多 Sprint 链式管理器"""
    
    def __init__(self, config: SprintChainConfig, chorus=None, kb=None, evo=None):
        self.config = config
        self.chorus = chorus
        self.kb = kb
        self.evo = evo
        self.status = SprintChainStatus.PENDING
        self.sprints = [Sprint(index=i, name=c.name, goals=c.goals) 
                        for i, c in enumerate(config.sprint_configs)]
        self.current_idx = 0
        self.started_at = None
    
    async def start(self) -> Dict[str, Any]:
        self.status = SprintChainStatus.RUNNING
        self.started_at = datetime.now()
        return await self._run_current()
    
    async def _run_current(self) -> Dict[str, Any]:
        if self.current_idx >= len(self.sprints):
            self.status = SprintChainStatus.COMPLETED
            return {"status": "completed", "summary": self._summary()}
        
        sprint = self.sprints[self.current_idx]
        sprint.status = SprintStatus.EXECUTING
        sprint.started_at = datetime.now()
        
        print(f"\n🚀 Sprint {self.current_idx+1}/{len(self.sprints)}: {sprint.name}")
        print(f"   Goals: {', '.join(sprint.goals)}")
        
        # 注入知识
        if self.kb and self.config.knowledge_injection:
            knowledge = await self.kb.retrieve_for_sprint(
                self.config.project_name, sprint.goals)
            print(f"📚 注入 {len(knowledge)} 条知识")
        
        # 执行
        if self.chorus:
            result = await self.chorus.execute_sprint(sprint, self.config.prd_path)
            sprint.verification_result = result
        
        sprint.status = SprintStatus.COMPLETED
        sprint.completed_at = datetime.now()
        self.current_idx += 1
        
        if self.config.auto_progress:
            return await self._run_current()
        return {"status": "paused", "current": sprint.name}
    
    def _summary(self) -> dict:
        return {"total": len(self.sprints), "completed": self.current_idx}
    
    async def pause(self): self.status = SprintChainStatus.PAUSED
    async def resume(self):
        self.status = SprintChainStatus.RUNNING
        return await self._run_current()
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "progress": {"current": self.current_idx, "total": len(self.sprints)},
            "current_sprint": self.sprints[self.current_idx].to_dict() if self.current_idx < len(self.sprints) else None
        }
