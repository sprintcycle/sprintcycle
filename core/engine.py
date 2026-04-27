"""SprintCycle 核心引擎 v2.0"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .config import SprintCycleConfig, load_config
from .sprint_chain import SprintChain, SprintChainConfig
from .knowledge_base import KnowledgeBase
from .evolution_engine import EvolutionEngine
from .verifier import FiveSourceVerifier
from .router import VerificationRouter
from ..models.sprint import SprintConfig
from ..adapters.chorus_adapter import ChorusAdapter
from ..utils.ai import create_ai_provider


class SprintCycleEngine:
    """SprintCycle 主引擎 v2.0"""
    
    def __init__(self, config: Optional[SprintCycleConfig] = None, config_path: str = "config.yaml"):
        self.config = config or load_config(config_path)
        
        # 核心组件
        self.kb = KnowledgeBase(f"{self.config.project_name}_knowledge.json")
        self.evo = EvolutionEngine(f"{self.config.project_name}_evolution.json")
        self.chorus = ChorusAdapter(self.config.chorus)
        self.verifier = FiveSourceVerifier()
        self.router = VerificationRouter(self.verifier)
        self.ai = create_ai_provider(self.config.ai)
        
        self.chain: Optional[SprintChain] = None
    
    async def start(
        self,
        project_name: str,
        prd_path: str,
        sprint_configs: Optional[List[dict]] = None,
        project_type: str = "full_stack",
    ) -> Dict[str, Any]:
        """启动项目开发"""
        # 默认Sprint配置
        if not sprint_configs:
            sprint_configs = [
                {"name": "Sprint 1 - 基础架构", "goals": ["项目骨架", "核心模块"]},
                {"name": "Sprint 2 - 功能开发", "goals": ["核心功能", "API开发"]},
                {"name": "Sprint 3 - 测试完善", "goals": ["测试", "文档"]},
            ]
        
        configs = [SprintConfig(name=s["name"], goals=s["goals"]) for s in sprint_configs]
        
        chain_config = SprintChainConfig(
            project_name=project_name,
            prd_path=prd_path,
            sprint_configs=configs,
            auto_progress=self.config.auto_progress,
        )
        
        self.chain = SprintChain(
            config=chain_config,
            chorus=self.chorus,
            kb=self.kb,
            evo=self.evo,
        )
        
        return await self.chain.start()
    
    async def verify(self, project_type: str = "full_stack") -> Dict[str, Any]:
        """执行验证"""
        return await self.router.route(project_type)
    
    async def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        if not self.chain:
            return {"status": "not_started"}
        return self.chain.get_status()
    
    async def pause(self):
        if self.chain:
            await self.chain.pause()
    
    async def resume(self):
        if self.chain:
            return await self.chain.resume()
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[dict]:
        """搜索知识库"""
        results = await self.kb.search(query, limit=limit)
        return [r.to_dict() for r in results]
    
    async def add_knowledge(self, title: str, content: str, tags: List[str] = None) -> str:
        """添加知识"""
        from ..models.knowledge import KnowledgeEntry, KnowledgeType
        entry = KnowledgeEntry(title=title, content=content, tags=tags or [])
        return await self.kb.add_entry(entry)
    
    async def get_recommendations(self) -> List[dict]:
        """获取改进建议"""
        return await self.evo.get_recommendations()
    
    async def generate_knowledge_from_evolution(self, record_id: str) -> Optional[dict]:
        """从进化记录生成知识"""
        return await self.evo.generate_knowledge(record_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "knowledge": await self.kb.get_statistics(),
            "evolution": await self.evo.get_statistics(),
            "chain": self.chain.get_status() if self.chain else None,
        }
    
    async def ai_generate(self, prompt: str, system: str = None) -> str:
        """AI生成"""
        return await self.ai.generate(prompt, system)
