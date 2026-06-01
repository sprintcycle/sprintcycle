#!/usr/bin/env python3
"""高级用户故事生成器 - 基于代码库和文档"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import ast
import re

from loguru import logger


@dataclass
class CodeAnalysisResult:
    """代码分析结果"""
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    modules: List[Dict[str, Any]]
    docstrings: List[str]
    comments: List[str]


@dataclass
class UserStoryEnhanced:
    """增强版用户故事"""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str
    impact: str
    complexity: str
    score: float
    related_code: List[str]
    related_docs: List[str]
    tags: List[str]
    source: str  # code / doc / hybrid


class AdvancedStoryGenerator:
    """高级用户故事生成器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.code_analysis = None
    
    def analyze_codebase(self) -> CodeAnalysisResult:
        """分析整个代码库"""
        logger.info("🔍 开始分析代码库...")
        
        functions = []
        classes = []
        modules = []
        docstrings = []
        comments = []
        
        # 遍历 Python 文件
        for py_file in self.project_root.rglob("*.py"):
            # 跳过某些目录
            if any(skip in str(py_file) for skip in [
                "__pycache__", ".pyc", ".venv", "test_", "_test.py",
                ".git", "node_modules", "dist", "build"
            ]):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                module_info = {
                    'path': str(py_file.relative_to(self.project_root)),
                    'name': py_file.stem
                }
                modules.append(module_info)
                
                for node in ast.walk(tree):
                    # 提取函数
                    if isinstance(node, ast.FunctionDef):
                        func_info = {
                            'name': node.name,
                            'module': py_file.stem,
                            'path': str(py_file.relative_to(self.project_root)),
                            'docstring': ast.get_docstring(node) or "",
                            'line': node.lineno,
                            'args': [arg.arg for arg in node.args.args]
                        }
                        functions.append(func_info)
                        if func_info['docstring']:
                            docstrings.append(func_info['docstring'])
                    
                    # 提取类
                    elif isinstance(node, ast.ClassDef):
                        class_info = {
                            'name': node.name,
                            'module': py_file.stem,
                            'path': str(py_file.relative_to(self.project_root)),
                            'docstring': ast.get_docstring(node) or "",
                            'line': node.lineno,
                            'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        }
                        classes.append(class_info)
                        if class_info['docstring']:
                            docstrings.append(class_info['docstring'])
                
                # 提取注释
                comment_pattern = r'#.*'
                file_comments = re.findall(comment_pattern, content)
                comments.extend(file_comments)
                
            except Exception as e:
                logger.debug(f"分析文件失败 {py_file}: {e}")
        
        self.code_analysis = CodeAnalysisResult(
            functions=functions,
            classes=classes,
            modules=modules,
            docstrings=docstrings,
            comments=comments
        )
        
        logger.info(f"✅ 代码分析完成: {len(modules)} 模块, {len(classes)} 类, {len(functions)} 函数")
        return self.code_analysis
    
    def generate_from_codebase(self) -> List[UserStoryEnhanced]:
        """从代码库生成用户故事"""
        if not self.code_analysis:
            self.analyze_codebase()
        
        stories = []
        
        # 从类生成用户故事
        stories.extend(self._generate_from_classes())
        
        # 从函数生成用户故事
        stories.extend(self._generate_from_functions())
        
        # 从文档字符串生成用户故事
        stories.extend(self._generate_from_docstrings())
        
        # 排序并去重
        stories = self._deduplicate_and_sort(stories)
        
        return stories
    
    def _generate_from_classes(self) -> List[UserStoryEnhanced]:
        """从类定义生成用户故事"""
        stories = []
        
        for cls in self.code_analysis.classes:
            if not cls['docstring']:
                continue
            
            # 提取关键信息
            class_name = cls['name']
            doc_lines = cls['docstring'].strip().split('\n')
            first_line = doc_lines[0] if doc_lines else ""
            
            # 生成用户故事
            story = UserStoryEnhanced(
                id=f"story_cls_{class_name.lower()}",
                title=f"作为用户，我希望能够使用 {class_name} 功能",
                description=first_line,
                acceptance_criteria=self._extract_acceptance_criteria(cls),
                priority=self._infer_priority(cls),
                impact=self._infer_impact(cls),
                complexity=self._infer_complexity(cls),
                score=self._calculate_score(cls),
                related_code=[cls['path']],
                related_docs=[],
                tags=['class', class_name],
                source='code'
            )
            stories.append(story)
        
        return stories
    
    def _generate_from_functions(self) -> List[UserStoryEnhanced]:
        """从函数定义生成用户故事"""
        stories = []
        
        for func in self.code_analysis.functions:
            if not func['docstring']:
                continue
            
            func_name = func['name']
            doc_lines = func['docstring'].strip().split('\n')
            first_line = doc_lines[0] if doc_lines else ""
            
            story = UserStoryEnhanced(
                id=f"story_func_{func_name.lower()}",
                title=f"作为用户，我希望能够执行 {func_name} 操作",
                description=first_line,
                acceptance_criteria=[f"{func_name} 函数正确执行", f"返回预期结果"],
                priority=self._infer_func_priority(func),
                impact="Medium",
                complexity="Low",
                score=self._calculate_func_score(func),
                related_code=[func['path']],
                related_docs=[],
                tags=['function', func_name],
                source='code'
            )
            stories.append(story)
        
        return stories
    
    def _generate_from_docstrings(self) -> List[UserStoryEnhanced]:
        """从文档字符串提取用户故事"""
        stories = []
        seen = set()
        
        for docstring in self.code_analysis.docstrings:
            # 提取关键短语
            lines = docstring.strip().split('\n')
            if not lines:
                continue
            
            key_phrases = [
                line.strip() for line in lines 
                if line.strip() and len(line.strip()) > 10
            ]
            
            for phrase in key_phrases[:3]:  # 每个文档最多生成3个故事
                if phrase in seen:
                    continue
                seen.add(phrase)
                
                # 推断优先级
                priority = "High" if any(word in phrase.lower() for word in ["must", "required", "core", "essential"]) else "Medium"
                
                story = UserStoryEnhanced(
                    id=f"story_doc_{hash(phrase) % 10000:04d}",
                    title=f"作为用户，我希望{phrase}",
                    description=phrase,
                    acceptance_criteria=[phrase],
                    priority=priority,
                    impact="Medium",
                    complexity="Medium",
                    score=70 if priority == "High" else 50,
                    related_code=[],
                    related_docs=["代码文档"],
                    tags=['documentation'],
                    source='doc'
                )
                stories.append(story)
        
        return stories
    
    def _extract_acceptance_criteria(self, cls: Dict) -> List[str]:
        """从类定义提取验收标准"""
        criteria = []
        if cls['docstring']:
            lines = cls['docstring'].split('\n')
            for line in lines:
                if any(prefix in line for prefix in ['- ', '* ', '1.', '2.', '3.']):
                    criteria.append(line.strip('-* 1234567890. ').strip())
        return criteria[:5]
    
    def _infer_priority(self, cls: Dict) -> str:
        """推断优先级"""
        name = cls['name'].lower()
        if any(keyword in name for keyword in ['core', 'main', 'service', 'manager']):
            return 'High'
        elif any(keyword in name for keyword in ['utils', 'helper', 'tools']):
            return 'Medium'
        return 'Medium'
    
    def _infer_impact(self, cls: Dict) -> str:
        """推断影响范围"""
        name = cls['name'].lower()
        if any(keyword in name for keyword in ['core', 'api', 'service']):
            return 'High'
        return 'Medium'
    
    def _infer_complexity(self, cls: Dict) -> str:
        """推断复杂度"""
        method_count = len(cls.get('methods', []))
        if method_count > 10:
            return 'High'
        elif method_count > 5:
            return 'Medium'
        return 'Low'
    
    def _calculate_score(self, cls: Dict) -> float:
        """计算分数"""
        priority_weight = {'High': 30, 'Medium': 20, 'Low': 10}
        impact_weight = {'High': 25, 'Medium': 15, 'Low': 5}
        complexity_weight = {'Low': 20, 'Medium': 15, 'High': 10}
        
        return (
            priority_weight[self._infer_priority(cls)] +
            impact_weight[self._infer_impact(cls)] +
            complexity_weight[self._infer_complexity(cls)] +
            10  # 基础分
        )
    
    def _infer_func_priority(self, func: Dict) -> str:
        """推断函数优先级"""
        name = func['name'].lower()
        if any(keyword in name for keyword in ['create', 'delete', 'update', 'get', 'run', 'execute']):
            return 'High'
        return 'Medium'
    
    def _calculate_func_score(self, func: Dict) -> float:
        """计算函数分数"""
        priority = self._infer_func_priority(func)
        return 75 if priority == 'High' else 55
    
    def _deduplicate_and_sort(self, stories: List[UserStoryEnhanced]) -> List[UserStoryEnhanced]:
        """去重并排序"""
        seen = set()
        unique_stories = []
        
        for story in stories:
            key = (story.title, story.source)
            if key not in seen:
                seen.add(key)
                unique_stories.append(story)
        
        return sorted(unique_stories, key=lambda x: x.score, reverse=True)
    
    def get_top_stories(self, count: int = 5) -> List[UserStoryEnhanced]:
        """获取 Top N 用户故事"""
        stories = self.generate_from_codebase()
        return stories[:count]


def main():
    """命令行入口"""
    generator = AdvancedStoryGenerator()
    
    print("===== 代码库分析 =====")
    analysis = generator.analyze_codebase()
    print(f"模块数: {len(analysis.modules)}")
    print(f"类数: {len(analysis.classes)}")
    print(f"函数数: {len(analysis.functions)}")
    print(f"文档字符串数: {len(analysis.docstrings)}")
    
    print("\n===== 生成用户故事 =====")
    stories = generator.generate_from_codebase()
    print(f"生成用户故事数: {len(stories)}")
    
    print("\n===== Top 5 用户故事 =====")
    top_stories = generator.get_top_stories(5)
    for i, story in enumerate(top_stories, 1):
        print(f"\n{i}. [{story.score:.1f}] {story.title}")
        print(f"   - 来源: {story.source}")
        print(f"   - 优先级: {story.priority}")
        print(f"   - 影响: {story.impact}")
        print(f"   - 复杂度: {story.complexity}")
        print(f"   - 相关代码: {', '.join(story.related_code)}")


if __name__ == "__main__":
    main()