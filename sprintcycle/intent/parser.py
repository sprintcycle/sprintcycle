"""
Intent 意图解析器

将自然语言意图解析为结构化的执行计划
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class ActionType(Enum):
    """动作类型"""
    EVOLVE = "evolution"   # 进化、优化
    BUILD = "normal"       # 构建、开发、添加
    FIX = "fix"            # 修复、解决
    TEST = "test"          # 测试
    RUN = "run"            # 执行 PRD 文件
    UNKNOWN = "normal"     # 未知，默认普通模式


@dataclass
class ParsedIntent:
    """解析后的意图"""
    action: ActionType
    description: str
    target: Optional[str] = None
    project: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    mode: str = "auto"
    prd_file: Optional[str] = None  # 用于 run 命令


class IntentParser:
    """
    意图解析器
    
    将用户意图（自然语言或结构化参数）解析为标准的 ParsedIntent
    """
    
    # 关键词映射
    EVOLVE_KEYWORDS = [
        "优化", "进化", "optimize", "evolve", "improve", 
        "增强", "提升", "重构", "refactor", "性能"
    ]
    BUILD_KEYWORDS = [
        "添加", "开发", "构建", "add", "build", "create", 
        "实现", "新增", "写", "编写"
    ]
    FIX_KEYWORDS = [
        "修复", "解决", "fix", "solve", "bug", "错误", 
        "问题", "修复", "排查"
    ]
    TEST_KEYWORDS = [
        "测试", "test", "验证", "验收", "检查"
    ]
    RUN_KEYWORDS = [
        "执行", "run", "运行"
    ]
    
    def parse(
        self, 
        intent: str, 
        project: Optional[str] = None, 
        target: Optional[str] = None, 
        mode: str = "auto",
        constraints: List[str] = None,
    ) -> ParsedIntent:
        """解析用户意图"""
        
        # 检查是否是 PRD 文件路径
        prd_file = self._extract_prd_path(intent)
        
        # 如果用户指定了模式，直接使用
        if mode != "auto":
            try:
                action = ActionType(mode)
            except ValueError:
                action = ActionType.UNKNOWN
        elif prd_file:
            action = ActionType.RUN
        else:
            action = self._infer_action(intent)
        
        # 提取目标文件
        extracted_target = self._extract_target(intent) or target
        
        # 提取约束条件
        extracted_constraints = self._extract_constraints(intent)
        if constraints:
            extracted_constraints.extend(constraints)
        
        return ParsedIntent(
            action=action,
            description=intent,
            target=extracted_target,
            project=project,
            constraints=extracted_constraints,
            mode=action.value,
            prd_file=prd_file,
        )
    
    def _infer_action(self, intent: str) -> ActionType:
        """根据关键词推断动作类型"""
        intent_lower = intent.lower()
        
        for kw in self.FIX_KEYWORDS:
            if kw in intent_lower:
                return ActionType.FIX
        
        for kw in self.TEST_KEYWORDS:
            if kw in intent_lower:
                return ActionType.TEST
        
        for kw in self.EVOLVE_KEYWORDS:
            if kw in intent_lower:
                return ActionType.EVOLVE
        
        for kw in self.BUILD_KEYWORDS:
            if kw in intent_lower:
                return ActionType.BUILD
        
        return ActionType.UNKNOWN
    
    def _extract_target(self, text: str) -> Optional[str]:
        """从文本中提取目标文件路径"""
        patterns = [
            r'([\w./\\-]+\.(?:py|vue|ts|tsx|js|jsx|go|rs|java|cpp|c|h|css|scss|less|html|md|txt))',
            r'`([^`]+)`',
            r'"([^"]+\.(?:yaml|yml|json))"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_prd_path(self, text: str) -> Optional[str]:
        """检查是否是 PRD 文件路径"""
        match = re.search(r'([\w./\\-]+\.(?:yaml|yml))', text)
        return match.group(1) if match else None
    
    def _extract_constraints(self, text: str) -> List[str]:
        """从文本中提取约束条件"""
        constraints = []
        constraint_patterns = [
            r'[（(]保持([^）)]+)[）)]',
            r'[（(]不([^）)]+)[）)]',
            r'必须([^\s，,。]+)',
            r'要求([^\s，,。]+)',
        ]
        
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text)
            constraints.extend(matches)
        
        return constraints
