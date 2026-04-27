"""Chorus 适配器 - 与 Chorus 执行层交互"""

import asyncio
from typing import Dict, Any, List
from pathlib import Path
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class ChorusAdapter:
    """Chorus 适配器 - MCP/HTTP 双模式"""
    
    def __init__(self, config):
        self.base_url = getattr(config, 'base_url', 'http://localhost:3000')
        self.timeout = getattr(config, 'timeout', 300)
        self.api_key = getattr(config, 'api_key', None)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def create_session(self, project_id: str, sprint_name: str) -> str:
        """创建 Chorus Session"""
        resp = await self.client.post(
            f"{self.base_url}/api/sessions",
            json={"project_id": project_id, "name": sprint_name}
        )
        resp.raise_for_status()
        return resp.json()["session_id"]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def create_proposal(
        self, session_id: str, prd: str, goals: List[str], knowledge: List = None
    ) -> str:
        """创建开发提案"""
        content = f"# PRD\n{prd}\n\n# Sprint Goals\n"
        content += "\n".join(f"- {g}" for g in goals)
        
        if knowledge:
            content += "\n\n# 相关知识\n"
            for k in knowledge[:5]:
                content += f"- **{k.title}**: {k.content[:100]}...\n"
        
        resp = await self.client.post(
            f"{self.base_url}/api/sessions/{session_id}/proposals",
            json={"content": content}
        )
        resp.raise_for_status()
        return resp.json()["proposal_id"]
    
    async def approve_proposal(self, proposal_id: str, auto_approve: bool = True) -> List[str]:
        """批准提案并获取任务"""
        resp = await self.client.post(
            f"{self.base_url}/api/proposals/{proposal_id}/approve",
            json={"auto_approve": auto_approve}
        )
        resp.raise_for_status()
        return resp.json().get("task_ids", [])
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取 Session 状态"""
        resp = await self.client.get(f"{self.base_url}/api/sessions/{session_id}")
        resp.raise_for_status()
        return resp.json()
    
    async def execute_sprint(self, sprint, prd_path: str) -> Dict[str, Any]:
        """执行完整 Sprint"""
        # 1. 创建 Session
        session_id = await self.create_session(sprint.name, sprint.name)
        sprint.session_id = session_id
        print(f"   ✅ Session: {session_id}")
        
        # 2. 加载 PRD
        prd = ""
        if Path(prd_path).exists():
            prd = Path(prd_path).read_text(encoding="utf-8")
        
        # 3. 创建 Proposal
        proposal_id = await self.create_proposal(session_id, prd, sprint.goals)
        sprint.proposal_id = proposal_id
        print(f"   📝 Proposal: {proposal_id}")
        
        # 4. 批准并执行
        task_ids = await self.approve_proposal(proposal_id)
        sprint.task_ids = task_ids
        print(f"   🔧 Tasks: {len(task_ids)} 个")
        
        # 5. 等待完成
        for i in range(60):  # 最多 30 分钟
            status = await self.get_session_status(session_id)
            if status.get("status") == "completed":
                print(f"   ✅ 执行完成")
                return {"success": True, "tasks": task_ids, "session_id": session_id}
            if status.get("status") == "failed":
                print(f"   ❌ 执行失败: {status.get('error')}")
                return {"success": False, "error": status.get("error")}
            await asyncio.sleep(30)
        
        return {"success": False, "error": "timeout", "session_id": session_id}
    
    async def health_check(self) -> bool:
        """检查 Chorus 是否可用"""
        try:
            resp = await self.client.get(f"{self.base_url}/health")
            return resp.status_code == 200
        except:
            return False
