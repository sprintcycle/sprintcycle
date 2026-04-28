"""
PRD 生成器

将 ParsedIntent 转换为 PRD 文档
"""

import os
from typing import Optional, List
from pathlib import Path

from .models import (
    PRD, PRDProject, PRDSprint, PRDTask,
    EvolutionConfig, ExecutionMode
)
from ..intent.parser import ParsedIntent, ActionType


class PRDGenerator:
    """
    PRD 生成器
    
    将 ParsedIntent 转换为标准的 PRD 对象
    """
    
    # 自进化关键词（必须同时匹配项目名和动作词）
    EVOLUTION_PROJECT_KEYWORDS = [
        "sprintcycle", "sprint cycle", "self", "自身", "自己"
    ]
    EVOLUTION_ACTION_KEYWORDS = [
        "进化", "evolve", "优化", "optimize", "improve", 
        "增强", "enhance", "重构", "refactor", "self-evolution"
    ]
    
    @staticmethod
    def generate(parsed: ParsedIntent) -> PRD:
        """
        从解析后的意图生成 PRD
        
        判断优先级：
        1. 意图关键词识别（如 "优化 sprintcycle 自身代码"）
        2. ParsedIntent.action 动作类型
        3. target/project 路径判断
        
        Args:
            parsed: ParsedIntent 对象
            
        Returns:
            PRD: 生成的 PRD 对象
        """
        # 优先级 1: 根据意图描述判断是否为自进化
        if parsed.description:
            inferred_mode = PRDGenerator._infer_mode_from_intent(parsed.description)
            if inferred_mode == ExecutionMode.EVOLUTION:
                # 意图匹配自进化，强制使用 EVOLVE 动作
                return PRDGenerator._from_evolve(parsed)
        
        # 优先级 2: 根据动作类型生成不同的 PRD
        if parsed.action == ActionType.EVOLVE:
            return PRDGenerator._from_evolve(parsed)
        elif parsed.action == ActionType.FIX:
            return PRDGenerator._from_fix(parsed)
        elif parsed.action == ActionType.TEST:
            return PRDGenerator._from_test(parsed)
        elif parsed.action == ActionType.RUN:
            return PRDGenerator._from_run(parsed)
        else:
            return PRDGenerator._from_build(parsed)
    
    @staticmethod
    def _infer_mode_from_intent(description: str) -> Optional[ExecutionMode]:
        """
        根据意图描述推断执行模式
        
        规则：意图同时包含项目关键词和动作关键词 → EVOLUTION
        
        Args:
            description: 意图描述
            
        Returns:
            ExecutionMode 或 None（无法判断）
        """
        if not description:
            return None
        
        desc_lower = description.lower()
        
        # 检查是否包含项目关键词
        has_project = any(kw in desc_lower for kw in PRDGenerator.EVOLUTION_PROJECT_KEYWORDS)
        
        # 检查是否包含动作关键词
        has_action = any(kw in desc_lower for kw in PRDGenerator.EVOLUTION_ACTION_KEYWORDS)
        
        # 同时满足才判断为自进化
        if has_project and has_action:
            return ExecutionMode.EVOLUTION
        
        return None
    
    @staticmethod
    def _infer_mode_from_target(target: Optional[str], project: Optional[str]) -> ExecutionMode:
        """
        根据 target 和 project 路径推断执行模式（备用方法）
        
        Args:
            target: 目标文件/目录路径
            project: 项目根目录路径
            
        Returns:
            ExecutionMode: 推断出的执行模式
        """
        return ExecutionMode.NORMAL
    
    @staticmethod
    def _get_sprintcycle_root() -> Path:
        """获取 SprintCycle 项目根目录"""
        return Path(__file__).parent.parent.parent
    
    @staticmethod
    def _from_evolve(parsed: ParsedIntent) -> PRD:
        """从进化意图生成 PRD"""
        project_path = parsed.project or PRDGenerator._get_sprintcycle_root()
        
        project = PRDProject(
            name="sprintcycle",
            path=project_path,
            version="v0.6.0",
        )
        
        evolution = EvolutionConfig(
            targets=[parsed.target] if parsed.target else [],
            goals=[parsed.description],
            constraints=parsed.constraints,
            max_variations=5,
            iterations=3,
        )
        
        sprint = PRDSprint(
            name="Evolution Sprint",
            goals=[parsed.description],
            tasks=[
                PRDTask(
                    task=parsed.description,
                    agent="evolver",
                    target=parsed.target,
                    constraints=parsed.constraints,
                )
            ],
        )
        
        return PRD(
            project=project,
            mode=ExecutionMode.EVOLUTION,
            evolution=evolution,
            sprints=[sprint],
        )
    
    @staticmethod
    def _from_build(parsed: ParsedIntent) -> PRD:
        """从构建意图生成 PRD"""
        project_path = parsed.project or os.getcwd()
        project_name = os.path.basename(os.path.abspath(project_path))
        
        project = PRDProject(
            name=project_name,
            path=project_path,
            version="v1.0.0",
        )
        
        sprint = PRDSprint(
            name="Feature Development",
            goals=[parsed.description],
            tasks=[
                PRDTask(
                    task=parsed.description,
                    agent="coder",
                    target=parsed.target,
                    constraints=parsed.constraints,
                )
            ],
        )
        
        return PRD(
            project=project,
            mode=ExecutionMode.NORMAL,
            sprints=[sprint],
        )
    
    @staticmethod
    def _from_fix(parsed: ParsedIntent) -> PRD:
        """从修复意图生成 PRD"""
        return PRDGenerator._from_build(parsed)
    
    @staticmethod
    def _from_test(parsed: ParsedIntent) -> PRD:
        """从测试意图生成 PRD"""
        return PRDGenerator._from_build(parsed)
    
    @staticmethod
    def _from_run(parsed: ParsedIntent) -> PRD:
        """从运行 PRD 文件意图生成"""
        # TODO: 实际解析 PRD 文件
        return PRDGenerator._from_build(parsed)
    
    @staticmethod
    def sample_prd() -> PRD:
        """生成示例 PRD"""
        project = PRDProject(
            name="demo",
            path="./demo",
            version="v1.0.0",
        )
        
        sprint = PRDSprint(
            name="Sprint 1",
            goals=["实现基础功能"],
            tasks=[
                PRDTask(task="实现用户认证", agent="coder"),
                PRDTask(task="编写单元测试", agent="tester"),
            ],
        )
        
        return PRD(
            project=project,
            mode=ExecutionMode.NORMAL,
            sprints=[sprint],
        )
