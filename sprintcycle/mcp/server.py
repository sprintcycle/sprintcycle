"""
MCP (Model Context Protocol) 服务端

FastAPI 实现，提供统一的意图处理接口
"""

import asyncio
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IntentRequest(BaseModel):
    """意图请求"""
    intent: str = Field(..., description="用户意图描述")
    project: Optional[str] = Field(None, description="项目路径")
    target: Optional[str] = Field(None, description="目标文件")
    mode: str = Field("auto", description="执行模式: auto|evolution|normal|fix|test")
    constraints: List[str] = Field(default_factory=[], description="约束条件")
    dry_run: bool = Field(False, description="仅生成 PRD，不执行")


class IntentResponse(BaseModel):
    """意图响应"""
    success: bool = Field(..., description="是否成功")
    action: Optional[str] = Field(None, description="识别的动作类型")
    prd_yaml: Optional[str] = Field(None, description="生成的 PRD (YAML)")
    result: Optional[dict] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")


class StatusResponse(BaseModel):
    """状态响应"""
    version: str = "0.6.0"
    mode: str = "PRD 驱动"
    status: str = "running"


class RunPRDRequest(BaseModel):
    """执行 PRD 文件请求"""
    prd_file: str = Field(..., description="PRD 文件路径")
    dry_run: bool = Field(False, description="仅验证 PRD，不执行")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 SprintCycle MCP Server 启动")
    yield
    logger.info("👋 SprintCycle MCP Server 关闭")


app = FastAPI(
    title="SprintCycle MCP Server",
    description="Model Context Protocol 服务端 - 统一意图处理接口",
    version="0.6.0",
    lifespan=lifespan,
)


@app.post("/intent", response_model=IntentResponse)
async def process_intent(request: IntentRequest) -> IntentResponse:
    """处理意图 - 统一入口"""
    try:
        from sprintcycle.intent.parser import IntentParser
        from sprintcycle.prd.generator import PRDGenerator
        from sprintcycle.scheduler.dispatcher import TaskDispatcher, ExecutionStatus
        
        # 解析意图
        parser = IntentParser()
        parsed = parser.parse(
            request.intent,
            project=request.project,
            target=request.target,
            mode=request.mode,
            constraints=request.constraints,
        )
        
        # 生成 PRD
        generator = PRDGenerator()
        prd = generator.generate(parsed)
        prd_yaml = prd.to_yaml()
        
        if request.dry_run:
            return IntentResponse(
                success=True,
                action=parsed.action.value,
                prd_yaml=prd_yaml,
                result={"mode": "dry-run", "message": "PRD 已生成，未执行"},
            )
        
        # 执行
        dispatcher = TaskDispatcher()
        sprint_results = await dispatcher.execute_prd(prd, max_concurrent=3)
        
        success = all(
            r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
            for r in sprint_results
        )
        completed_sprints = sum(
            1 for r in sprint_results
            if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
        )
        completed_tasks = sum(r.success_count for r in sprint_results)
        
        return IntentResponse(
            success=success,
            action=parsed.action.value,
            prd_yaml=prd_yaml,
            result={
                "completed_sprints": completed_sprints,
                "total_sprints": len(sprint_results),
                "completed_tasks": completed_tasks,
                "total_tasks": prd.total_tasks,
            },
        )
        
    except Exception as e:
        logger.exception("执行失败")
        return IntentResponse(success=False, error=str(e))


@app.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    """查看服务状态"""
    return StatusResponse()


@app.post("/run", response_model=IntentResponse)
async def run_prd(request: RunPRDRequest) -> IntentResponse:
    """执行 PRD 文件"""
    try:
        from sprintcycle.prd.parser import PRDParser, PRDParseError, YAMLError
        from sprintcycle.scheduler.dispatcher import TaskDispatcher, ExecutionStatus
        
        parser = PRDParser()
        prd = parser.parse_file(request.prd_file)
        
        if request.dry_run:
            return IntentResponse(
                success=True,
                action="run",
                result={
                    "mode": "dry-run",
                    "project_name": prd.project.name,
                    "sprint_count": len(prd.sprints),
                    "task_count": prd.total_tasks,
                },
            )
        
        dispatcher = TaskDispatcher()
        sprint_results = await dispatcher.execute_prd(prd, max_concurrent=3)
        
        success = all(
            r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
            for r in sprint_results
        )
        completed_sprints = sum(
            1 for r in sprint_results
            if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
        )
        completed_tasks = sum(r.success_count for r in sprint_results)
        
        return IntentResponse(
            success=success,
            action="run",
            result={
                "completed_sprints": completed_sprints,
                "total_sprints": len(sprint_results),
                "completed_tasks": completed_tasks,
                "total_tasks": prd.total_tasks,
            },
        )
        
    except FileNotFoundError as e:
        return IntentResponse(success=False, error=f"PRD 文件不存在: {request.prd_file}")
    except (YAMLError, PRDParseError) as e:
        return IntentResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("执行失败")
        return IntentResponse(success=False, error=str(e))


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行 MCP 服务器"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
