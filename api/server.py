"""SprintCycle API Server - FastAPI"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from pathlib import Path

from sprintcycle.core.engine import SprintCycleEngine
from sprintcycle.core.config import SprintCycleConfig

app = FastAPI(
    title="SprintCycle API",
    description="自进化敏捷开发团队框架",
    version="0.4.4",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局引擎实例
_engine: Optional[SprintCycleEngine] = None


def get_engine() -> SprintCycleEngine:
    global _engine
    if _engine is None:
        _engine = SprintCycleEngine()
    return _engine


# ========== 请求模型 ==========

class ProjectStartRequest(BaseModel):
    project_name: str
    prd_path: str
    sprint_configs: Optional[List[Dict[str, Any]]] = None
    project_type: str = "full_stack"


class KnowledgeAddRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None


class VerifyRequest(BaseModel):
    project_type: str = "full_stack"


# ========== API 端点 ==========

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "SprintCycle API",
        "version": "0.4.4",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/projects/start")
async def start_project(request: ProjectStartRequest, background_tasks: BackgroundTasks):
    """启动项目开发"""
    engine = get_engine()
    
    # 检查 PRD 文件
    if not Path(request.prd_path).exists():
        raise HTTPException(status_code=400, detail=f"PRD文件不存在: {request.prd_path}")
    
    # 后台执行
    result = await engine.start(
        project_name=request.project_name,
        prd_path=request.prd_path,
        sprint_configs=request.sprint_configs,
        project_type=request.project_type,
    )
    
    return {"status": "started", "result": result}


@app.get("/api/projects/status")
async def get_status():
    """获取项目状态"""
    engine = get_engine()
    status = await engine.get_status()
    stats = await engine.get_statistics()
    return {"status": status, "statistics": stats}


@app.post("/api/projects/pause")
async def pause_project():
    """暂停项目"""
    engine = get_engine()
    await engine.pause()
    return {"status": "paused"}


@app.post("/api/projects/resume")
async def resume_project():
    """恢复项目"""
    engine = get_engine()
    result = await engine.resume()
    return {"status": "resumed", "result": result}


@app.post("/api/verify")
async def verify_project(request: VerifyRequest):
    """执行验证"""
    engine = get_engine()
    result = await engine.verify(request.project_type)
    return result


@app.get("/api/knowledge")
async def list_knowledge(limit: int = 10):
    """获取知识库列表"""
    engine = get_engine()
    stats = await engine.get_statistics()
    return stats.get("knowledge", {})


@app.get("/api/knowledge/search")
async def search_knowledge(query: str, limit: int = 5):
    """搜索知识库"""
    engine = get_engine()
    results = await engine.search_knowledge(query, limit)
    return {"query": query, "results": results}


@app.post("/api/knowledge")
async def add_knowledge(request: KnowledgeAddRequest):
    """添加知识条目"""
    engine = get_engine()
    entry_id = await engine.add_knowledge(
        title=request.title,
        content=request.content,
        tags=request.tags,
    )
    return {"id": entry_id, "status": "created"}


@app.get("/api/evolution/recommendations")
async def get_recommendations():
    """获取改进建议"""
    engine = get_engine()
    recs = await engine.get_recommendations()
    return {"recommendations": recs}


@app.get("/api/evolution/statistics")
async def get_evolution_stats():
    """获取进化统计"""
    engine = get_engine()
    stats = await engine.get_statistics()
    return stats.get("evolution", {})


@app.post("/api/evolution/{record_id}/generate-knowledge")
async def generate_knowledge_from_evolution(record_id: str):
    """从进化记录生成知识"""
    engine = get_engine()
    knowledge = await engine.generate_knowledge_from_evolution(record_id)
    if knowledge is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"knowledge": knowledge}


@app.get("/api/statistics")
async def get_all_statistics():
    """获取全部统计信息"""
    engine = get_engine()
    stats = await engine.get_statistics()
    return stats
