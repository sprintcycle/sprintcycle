"""
PRD 验证器

验证 PRD 结构和内容的有效性
"""

import logging
from typing import List
from pathlib import Path
from dataclasses import dataclass

from .models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误"""
    pass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class YAMLError(ValueError):
    """YAML 解析错误"""
    pass


class PRDValidator:
    """
    PRD 验证器
    
    验证 PRD 文档的结构完整性和内容有效性
    """
    
    # Agent 类型白名单
    VALID_AGENTS = {"coder", "evolver", "tester"}
    
    # 文件大小限制（MB）
    MAX_FILE_SIZE = 10
    
    def validate(self, prd: PRD) -> ValidationResult:
        """
        验证 PRD 对象
        
        Args:
            prd: PRD 对象
            
        Returns:
            验证结果
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # 1. 验证项目信息
        project_errors, project_warnings = self._validate_project(prd.project)
        errors.extend(project_errors)
        warnings.extend(project_warnings)
        
        # 2. 验证执行模式
        mode_errors, mode_warnings = self._validate_mode(prd)
        errors.extend(mode_errors)
        warnings.extend(mode_warnings)
        
        # 3. 验证 Sprint 列表
        sprint_errors, sprint_warnings = self._validate_sprints(prd)
        errors.extend(sprint_errors)
        warnings.extend(sprint_warnings)
        
        # 4. 生成警告
        if not warnings and len(prd.sprints) > 5:
            warnings.append(f"Sprint 数量较多 ({len(prd.sprints)})，建议拆分为多个 PRD")
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
    
    def _validate_project(self, project: PRDProject) -> tuple:
        """验证项目信息"""
        errors: List[str] = []
        warnings: List[str] = []
        
        # 名称验证
        if not project.name:
            errors.append("project.name 不能为空")
        elif len(project.name) > 100:
            warnings.append("project.name 过长，可能影响显示")
        
        # 路径验证
        if not project.path:
            errors.append("project.path 不能为空")
        elif not Path(project.path).is_absolute():
            warnings.append("project.path 建议使用绝对路径")
        
        # 版本号格式（简单检查）
        if project.version and not project.version.startswith("v"):
            warnings.append("version 建议使用 'v' 前缀格式，如 'v1.0.0'")
        
        return errors, warnings
    
    def _validate_mode(self, prd: PRD) -> tuple:
        """验证执行模式"""
        errors: List[str] = []
        warnings: List[str] = []
        
        # 自进化模式必须配置进化目标
        if prd.mode == ExecutionMode.EVOLUTION:
            if not prd.evolution:
                errors.append("自进化模式 (mode: evolution) 必须配置 evolution 部分")
            elif not prd.evolution.targets:
                errors.append("自进化模式必须指定至少一个 targets")
            elif not prd.evolution.goals:
                warnings.append("自进化模式建议指定 goals")
        
        return errors, warnings
    
    def _validate_sprints(self, prd: PRD) -> tuple:
        """验证 Sprint 列表"""
        errors: List[str] = []
        warnings: List[str] = []
        
        if not prd.sprints:
            errors.append("必须定义至少一个 Sprint")
            return errors, warnings
        
        # 验证每个 Sprint
        for i, sprint in enumerate(prd.sprints):
            sprint_errors, sprint_warnings = self._validate_single_sprint(sprint, i, prd.mode)
            errors.extend(sprint_errors)
            warnings.extend(sprint_warnings)
        
        return errors, warnings
    
    def _validate_single_sprint(self, sprint: PRDSprint, index: int, mode: ExecutionMode = ExecutionMode.NORMAL) -> tuple:
        """验证单个 Sprint"""
        errors: List[str] = []
        warnings: List[str] = []
        
        sprint_label = f"Sprint #{index + 1} '{sprint.name}'"
        
        # 验证名称
        if not sprint.name:
            errors.append(f"{sprint_label}: 缺少 name")
        
        # 验证任务列表
        if not sprint.tasks:
            errors.append(f"{sprint_label}: 缺少 tasks")
            return errors, warnings
        
        # 验证每个任务
        agent_usage = {"coder": 0, "evolver": 0, "tester": 0}
        for i, task in enumerate(sprint.tasks):
            task_errors, task_warnings = self._validate_task(task, index, i)
            errors.extend(task_errors)
            warnings.extend(task_warnings)
            
            if task.agent in agent_usage:
                agent_usage[task.agent] += 1
        
        # 检查 Agent 类型分布
        if agent_usage["evolver"] > 0 and mode != ExecutionMode.EVOLUTION:
            warnings.append(f"{sprint_label}: 包含 evolver agent，建议使用 evolution 模式")
        
        return errors, warnings
    
    def _validate_task(self, task: PRDTask, sprint_index: int, task_index: int) -> tuple:
        """验证单个任务"""
        errors: List[str] = []
        warnings: List[str] = []
        
        task_label = f"Sprint #{sprint_index + 1} Task #{task_index + 1}"
        
        # 验证任务描述
        if not task.task:
            errors.append(f"{task_label}: 缺少 task 描述")
        elif len(task.task) < 10:
            warnings.append(f"{task_label}: task 描述过短，建议提供更详细的任务说明")
        
        # 验证 Agent 类型
        if task.agent not in self.VALID_AGENTS:
            errors.append(f"{task_label}: 未知的 agent 类型 '{task.agent}'")
        
        # 验证目标路径（自进化模式必须指定）
        if task.agent == "evolver" and not task.target:
            warnings.append(f"{task_label}: evolver agent 建议指定 target")
        
        # 验证超时设置
        if task.timeout <= 0:
            errors.append(f"{task_label}: timeout 必须大于 0")
        elif task.timeout > 3600:
            warnings.append(f"{task_label}: timeout 较长 ({task.timeout}s)，可能导致执行缓慢")
        
        return errors, warnings
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        验证 PRD 文件
        
        Args:
            file_path: PRD 文件路径
            
        Returns:
            验证结果
        """
        from .parser import PRDParser, PRDParseError
        
        try:
            parser = PRDParser()
            prd = parser.parse_file(file_path)
            return self.validate(prd)
        except (PRDParseError, YAMLError) as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"文件验证失败: {e}"],
                warnings=[],
            )
