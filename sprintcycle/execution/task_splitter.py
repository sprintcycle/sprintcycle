"""
TaskSplitter - 任务拆分模块

将复杂的 PRD（产品需求文档）拆分为可执行的任务列表。

功能：
1. 意图分析和任务识别
2. 任务依赖分析
3. 任务优先级排序
4. 任务粒度控制

使用方式：
```python
from sprintcycle.execution.task_splitter import TaskSplitter

splitter = TaskSplitter()
tasks = splitter.split("实现用户认证和权限管理功能")

for task in tasks:
    print(f"任务: {task['title']}")
    print(f"描述: {task['description']}")
```
"""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    """任务数据类"""
    title: str                           # 任务标题
    description: str                     # 任务描述
    priority: str = "medium"             # 优先级
    estimated_time: str = "1-2h"         # 预估时间
    dependencies: List[str] = field(default_factory=list)  # 依赖任务
    tags: List[str] = field(default_factory=list)         # 标签
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "estimated_time": self.estimated_time,
            "dependencies": self.dependencies,
            "tags": self.tags,
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.title}: {self.description[:50]}..."


class TaskSplitter:
    """
    PRD 任务拆分器
    
    将复杂的 PRD 拆分为可管理的子任务。
    支持多种拆分策略：
    - 按功能模块拆分
    - 按优先级拆分
    - 按依赖关系拆分
    """
    
    # 功能模块关键词
    MODULE_KEYWORDS = {
        "auth": ["认证", "登录", "注册", "登出", "OAuth", "JWT", "权限", "permission"],
        "user": ["用户", "profile", "个人信息", "账户"],
        "data": ["数据", "CRUD", "增删改查", "存储", "数据库"],
        "api": ["API", "接口", "REST", "GraphQL", "endpoint"],
        "ui": ["界面", "UI", "前端", "组件", "按钮", "表单"],
        "cache": ["缓存", "cache", "redis", "memcached"],
        "security": ["安全", "加密", "CSRF", "XSS", "防护"],
        "test": ["测试", "unit", "e2e", "集成测试", "自动化测试"],
        "deploy": ["部署", "CI/CD", "docker", "k8s", "云服务"],
        "logging": ["日志", "logging", "监控", "metrics"],
        "config": ["配置", "config", "环境变量", "settings"],
        "performance": ["性能", "优化", "缓存", "索引", "CDN"],
    }
    
    # 优先级映射
    PRIORITY_MAP = {
        "high": ["核心", "关键", "必须", "紧急", "critical"],
        "medium": ["重要", "需要", "应该", "建议", "normal"],
        "low": ["可选", "优化", "改进", "nice-to-have"],
    }
    
    # 时间估算模式
    TIME_PATTERNS = [
        (r"(\d+)-(\d+)h", "estimated"),
        (r"(\d+)h", "1h"),
        (r"(\d+)天", "1d"),
        (r"(\d+)周", "1w"),
    ]
    
    def __init__(self, max_tasks: int = 20, min_tasks: int = 3):
        """
        初始化任务拆分器
        
        Args:
            max_tasks: 最大任务数
            min_tasks: 最小任务数
        """
        self.max_tasks = max_tasks
        self.min_tasks = min_tasks
    
    def split(self, prd: str) -> List[Dict[str, Any]]:
        """
        将 PRD 拆分为任务列表
        
        Args:
            prd: 产品需求文档
            
        Returns:
            List[Dict]: 任务列表
        """
        if not prd or not prd.strip():
            return []
        
        tasks = []
        
        # 策略1: 检测编号列表 (1. 2. 3. 或 - [ ] - [x])
        numbered_tasks = self._extract_numbered_tasks(prd)
        if numbered_tasks:
            tasks.extend(numbered_tasks)
        
        # 策略2: 检测模块关键词
        module_tasks = self._extract_module_tasks(prd)
        if module_tasks:
            tasks.extend(module_tasks)
        
        # 策略3: 基于句子拆分
        if not tasks:
            sentence_tasks = self._extract_sentence_tasks(prd)
            tasks.extend(sentence_tasks)
        
        # 策略4: 基于换行拆分
        if not tasks:
            line_tasks = self._extract_line_tasks(prd)
            tasks.extend(line_tasks)
        
        # 去重和排序
        tasks = self._deduplicate_tasks(tasks)
        tasks = self._sort_by_priority(tasks)
        
        # 限制任务数量
        if len(tasks) > self.max_tasks:
            tasks = tasks[: self.max_tasks]
        
        # 确保最小任务数
        if len(tasks) < self.min_tasks and tasks:
            tasks = self._expand_tasks(tasks)
        
        # 添加序号
        for i, task in enumerate(tasks, 1):
            task["id"] = f"T{i:03d}"
        
        return tasks
    
    def _extract_numbered_tasks(self, prd: str) -> List[Dict[str, Any]]:
        """提取编号列表任务"""
        tasks = []
        
        # 匹配模式: 1. xxx, 1) xxx, - xxx, * xxx
        patterns = [
            (r"^\s*(\d+)[.、)]\s*(.+)$", True),   # 带编号的列表，True表示需要处理编号前缀
            (r"^\s*[-*]\s*(.+)$", False),           # 无编号的列表
            (r"^\s*\[[ x]\]\s*(.+)$", False),     # checkbox 列表
        ]
        
        for pattern, has_number in patterns:
            matches = re.finditer(pattern, prd, re.MULTILINE)
            for match in matches:
                if has_number:
                    # 从完整匹配中提取数字后的内容
                    full = match.group(0)
                    content = re.sub(r"^\s*\d+[.、)]\s*", "", full).strip()
                else:
                    content = match.group(1).strip() if match.lastindex else match.group(0).strip()
                
                if content and len(content) > 2:
                    task = self._create_task_from_text(content)
                    tasks.append(task)
        
        return tasks
    
    def _extract_module_tasks(self, prd: str) -> List[Dict[str, Any]]:
        """基于模块关键词提取任务"""
        tasks = []
        prd_lower = prd.lower()
        
        detected_modules = set()
        for module, keywords in self.MODULE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in prd_lower:
                    detected_modules.add(module)
                    break
        
        # 为每个检测到的模块创建一个任务
        module_names = {
            "auth": "认证授权模块",
            "user": "用户管理模块",
            "data": "数据处理模块",
            "api": "API接口模块",
            "ui": "界面组件模块",
            "cache": "缓存模块",
            "security": "安全防护模块",
            "test": "测试模块",
            "deploy": "部署配置模块",
            "logging": "日志监控模块",
            "config": "配置管理模块",
            "performance": "性能优化模块",
        }
        
        for module in detected_modules:
            title = module_names.get(module, f"{module}模块")
            task = {
                "title": title,
                "description": f"实现{title}相关功能",
                "priority": "medium",
                "estimated_time": "2-4h",
                "dependencies": [],
                "tags": [module],
            }
            tasks.append(task)
        
        return tasks
    
    def _extract_sentence_tasks(self, prd: str) -> List[Dict[str, Any]]:
        """基于句子拆分任务"""
        tasks = []
        
        # 按句子拆分
        sentences = re.split(r"[。；;!?\n]", prd)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:
                task = self._create_task_from_text(sentence)
                tasks.append(task)
        
        return tasks
    
    def _extract_line_tasks(self, prd: str) -> List[Dict[str, Any]]:
        """基于换行拆分任务"""
        tasks = []
        
        lines = prd.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:
                task = self._create_task_from_text(line)
                tasks.append(task)
        
        return tasks
    
    def _create_task_from_text(self, text: str) -> Dict[str, Any]:
        """从文本创建任务"""
        # 检测优先级
        priority = "medium"
        for prio, keywords in self.PRIORITY_MAP.items():
            for keyword in keywords:
                if keyword in text:
                    priority = prio
                    break
        
        # 检测预估时间
        estimated_time = "1-2h"
        for pattern, replacement in self.TIME_PATTERNS:
            if re.search(pattern, text):
                match = re.search(pattern, text)
                if match:
                    estimated_time = match.group(0)
                    break
        
        # 检测依赖
        dependencies = []
        dep_keywords = ["依赖", "前置", "需要先", "before", "after"]
        for keyword in dep_keywords:
            if keyword in text.lower():
                dependencies.append(keyword)
        
        # 提取标签
        tags = []
        for module, keywords in self.MODULE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    tags.append(module)
                    break
        
        return {
            "title": text[:50] + "..." if len(text) > 50 else text,
            "description": text,
            "priority": priority,
            "estimated_time": estimated_time,
            "dependencies": dependencies,
            "tags": list(set(tags)) if tags else ["general"],
        }
    
    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重任务"""
        seen = set()
        unique_tasks = []
        
        for task in tasks:
            # 使用标题作为去重键
            key = task["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                unique_tasks.append(task)
        
        return unique_tasks
    
    def _sort_by_priority(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按优先级排序"""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        
        return sorted(
            tasks,
            key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 1),
                -len(t.get("title", "")),
            ),
        )
    
    def _expand_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """扩展任务"""
        if not tasks:
            return tasks
        
        # 如果任务太少，添加一些通用任务
        expanded = list(tasks)
        
        # 添加编码任务
        expanded.append(
            {
                "title": "核心功能实现",
                "description": "实现需求文档中描述的核心功能",
                "priority": "high",
                "estimated_time": "4-8h",
                "dependencies": [],
                "tags": ["coding"],
            }
        )
        
        # 添加测试任务
        expanded.append(
            {
                "title": "测试与验证",
                "description": "编写单元测试和集成测试，验证功能正确性",
                "priority": "medium",
                "estimated_time": "2-4h",
                "dependencies": ["coding"],
                "tags": ["test"],
            }
        )
        
        return expanded
    
    def analyze_dependencies(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        分析任务依赖关系
        
        Args:
            tasks: 任务列表
            
        Returns:
            Dict[str, List[str]]: 任务ID -> 依赖任务ID列表
        """
        dependencies = {}
        
        for task in tasks:
            task_id = task.get("id", task["title"])
            deps = []
            
            # 基于标签检测依赖
            tags = set(task.get("tags", []))
            
            for other_task in tasks:
                other_id = other_task.get("id", other_task["title"])
                if other_id == task_id:
                    continue
                
                other_tags = set(other_task.get("tags", []))
                
                # test 依赖 coding
                if "test" in tags and "coding" in other_tags:
                    deps.append(other_id)
                
                # deploy 依赖 test
                if "deploy" in tags and "test" in other_tags:
                    deps.append(other_id)
            
            dependencies[task_id] = list(set(deps))
        
        return dependencies


# 导出主要类
__all__ = ["TaskSplitter", "Task"]
