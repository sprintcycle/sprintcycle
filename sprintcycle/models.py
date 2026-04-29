"""
SprintCycle Pydantic 数据模型

提供类型安全的数据定义，替代 dict 传递

注意：枚举类型已统一到 sprintcycle.chorus.enums
此文件保留枚举的 re-export 以保持向后兼容
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ============================================================
# 枚举类型 - 从统一位置导入（re-export 保持向后兼容）
# ============================================================
from sprintcycle.chorus.enums import (
    AgentType,
    TaskStatus,
    SprintStatus,
    ReviewSeverity,
    IssueSeverity,
    IssueType,
    HealthStatus,
)


# ============================================================
# 基础模型
# ============================================================

class Task(BaseModel):
    """任务模型"""
    id: str = Field(default="", description="任务ID")
    name: str = Field(..., description="任务名称")
    description: str = Field(default="", description="任务描述")
    agent: AgentType = Field(default=AgentType.CODER, description="执行Agent")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    result: Optional[str] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    class Config:
        use_enum_values = True


class Sprint(BaseModel):
    """Sprint 模型"""
    name: str = Field(..., description="Sprint名称")
    description: str = Field(default="", description="Sprint描述")
    agent: AgentType = Field(default=AgentType.CODER, description="执行Agent")
    tasks: List[Task] = Field(default_factory=list, description="任务列表")
    status: SprintStatus = Field(default=SprintStatus.PLANNED, description="Sprint状态")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    acceptance_criteria: List[str] = Field(default_factory=list, description="验收标准")
    result: Optional[str] = Field(default=None, description="执行结果")

    class Config:
        use_enum_values = True


class Project(BaseModel):
    """项目模型"""
    name: str = Field(..., description="项目名称")
    path: str = Field(default="", description="项目路径")
    version: str = Field(default="v0.0", description="项目版本")
    theme: str = Field(default="", description="项目主题")
    goals: List[str] = Field(default_factory=list, description="项目目标")
    sprints: List[Sprint] = Field(default_factory=list, description="Sprint列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class Report(BaseModel):
    """执行报告模型"""
    project_name: str = Field(..., description="项目名称")
    version: str = Field(default="v0.0", description="版本")
    sprint_count: int = Field(default=0, description="Sprint数量")
    task_count: int = Field(default=0, description="任务总数")
    completed_count: int = Field(default=0, description="完成数")
    failed_count: int = Field(default=0, description="失败数")
    skipped_count: int = Field(default=0, description="跳过数")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    duration: float = Field(default=0.0, description="执行时长(秒)")
    results: List[str] = Field(default_factory=list, description="执行结果")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ============================================================
# 审查相关模型
# ============================================================

class ReviewResult(BaseModel):
    """审查结果模型"""
    severity: ReviewSeverity = Field(..., description="严重级别")
    message: str = Field(..., description="消息")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    line_number: Optional[int] = Field(default=None, description="行号")
    rule_id: Optional[str] = Field(default=None, description="规则ID")
    suggestion: Optional[str] = Field(default=None, description="建议")


# ============================================================
# 扫描相关模型
# ============================================================

class Issue(BaseModel):
    """问题模型"""
    severity: IssueSeverity = Field(..., description="严重级别")
    issue_type: IssueType = Field(..., description="问题类型")
    message: str = Field(..., description="消息")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    line_number: Optional[int] = Field(default=None, description="行号")
    code_snippet: Optional[str] = Field(default=None, description="代码片段")


class ScanResult(BaseModel):
    """扫描结果模型"""
    project_path: str = Field(..., description="项目路径")
    scan_time: datetime = Field(default_factory=datetime.now, description="扫描时间")
    total_issues: int = Field(default=0, description="问题总数")
    issues: List[Issue] = Field(default_factory=list, description="问题列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ============================================================
# 健康检查相关模型
# ============================================================

class HealthReport(BaseModel):
    """健康报告模型"""
    project_path: str = Field(..., description="项目路径")
    status: HealthStatus = Field(default=HealthStatus.HEALTHY, description="健康状态")
    score: float = Field(default=100.0, description="健康分数(0-100)")
    checks: Dict[str, Any] = Field(default_factory=dict, description="检查详情")
    recommendations: List[str] = Field(default_factory=list, description="建议")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")


# ============================================================
# 诊断相关模型
# ============================================================

class DiagnosticResult(BaseModel):
    """诊断结果模型"""
    issue: str = Field(..., description="问题描述")
    root_cause: Optional[str] = Field(default=None, description="根本原因")
    solution: Optional[str] = Field(default=None, description="解决方案")
    confidence: float = Field(default=0.0, description="置信度(0-1)")
    suggestions: List[str] = Field(default_factory=list, description="建议列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ============================================================
# PRD 解析相关模型
# ============================================================

class PRDSplitterConfig(BaseModel):
    """PRD 拆分器配置"""
    max_sprints_per_prd: int = Field(default=3, description="每个PRD最大Sprint数")
    max_tasks_per_sprint: int = Field(default=2, description="每个Sprint最大任务数")
    timeout_per_task: int = Field(default=120, description="任务超时(秒)")
    total_timeout_limit: int = Field(default=600, description="总超时限制(秒)")


class SplitResult(BaseModel):
    """拆分结果模型"""
    original_prd: str = Field(..., description="原始PRD路径")
    split_prds: List[str] = Field(default_factory=list, description="拆分后的PRD列表")
    total_sprints: int = Field(default=0, description="总Sprint数")
    split_count: int = Field(default=0, description="拆分次数")
    strategy_used: str = Field(default="", description="使用的策略")


# ============================================================
# 向后兼容：Dict 转换器
# ============================================================

def project_from_dict(data: Dict[str, Any]) -> Project:
    """从 dict 创建 Project 模型（向后兼容）"""
    return Project(**data)


def sprint_from_dict(data: Dict[str, Any]) -> Sprint:
    """从 dict 创建 Sprint 模型（向后兼容）"""
    return Sprint(**data)


def task_from_dict(data: Dict[str, Any]) -> Task:
    """从 dict 创建 Task 模型（向后兼容）"""
    return Task(**data)


def report_from_dict(data: Dict[str, Any]) -> Report:
    """从 dict 创建 Report 模型（向后兼容）"""
    return Report(**data)
