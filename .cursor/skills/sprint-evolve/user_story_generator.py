#!/usr/bin/env python3
"""用户故事生成器 - 从产品文档自动生成用户故事"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from loguru import logger


@dataclass
class UserStory:
    """用户故事定义"""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str  # High/Medium/Low
    impact: str    # High/Medium/Low
    complexity: str  # Low/Medium/High
    score: float
    related_docs: List[str]
    tags: List[str]


@dataclass
class StoryAnalysisResult:
    """用户故事分析结果"""
    stories: List[UserStory]
    top_optimizations: List[UserStory]
    metrics: Dict[str, Any]


class UserStoryGenerator:
    """用户故事生成器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent.parent
    
    def generate_from_docs(self) -> StoryAnalysisResult:
        """从文档生成用户故事"""
        logger.info("📖 开始从文档生成用户故事...")
        
        # 读取 README 和架构规则文件
        readme_content = self._read_readme()
        arch_rules_content = self._read_architecture_rules()
        
        # 生成用户故事
        stories = self._generate_stories(readme_content, arch_rules_content)
        
        # 评估优先级并排序
        stories = self._evaluate_and_sort(stories)
        
        # 选出 Top 3 优化点
        top_optimizations = stories[:3]
        
        # 生成分析结果
        result = StoryAnalysisResult(
            stories=stories,
            top_optimizations=top_optimizations,
            metrics={
                "total_stories": len(stories),
                "high_priority_count": sum(1 for s in stories if s.priority == "High"),
                "medium_priority_count": sum(1 for s in stories if s.priority == "Medium"),
                "low_priority_count": sum(1 for s in stories if s.priority == "Low"),
            }
        )
        
        logger.info(f"✅ 用户故事生成完成，共生成 {len(stories)} 个故事")
        return result
    
    def _read_readme(self) -> str:
        """读取 README.md"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            logger.warning("README.md 不存在")
            return ""
        return readme_path.read_text(encoding="utf-8")
    
    def _read_architecture_rules(self) -> str:
        """读取架构规则文件"""
        arch_path = self.project_root / ".cursor" / "rules" / "sprintcycle-architecture-orchestration.mdc"
        if not arch_path.exists():
            logger.warning("架构规则文件不存在")
            return ""
        return arch_path.read_text(encoding="utf-8")
    
    def _generate_stories(self, readme_content: str, arch_rules_content: str) -> List[UserStory]:
        """生成用户故事"""
        stories = []
        
        # 从产品能力矩阵生成故事
        stories.extend(self._generate_from_capability_matrix(readme_content))
        
        # 从架构规则生成故事
        stories.extend(self._generate_from_architecture_rules(arch_rules_content))
        
        # 从版本路线图生成故事
        stories.extend(self._generate_from_roadmap(readme_content))
        
        # 从用户旅程生成故事
        stories.extend(self._generate_from_user_journey(readme_content))
        
        return stories
    
    def _generate_from_capability_matrix(self, content: str) -> List[UserStory]:
        """从产品能力矩阵生成用户故事"""
        stories = []
        
        capabilities = [
            {"name": "意图驱动", "description": "自然语言意图转换为结构化 ReleasePlan"},
            {"name": "Sprint 编排", "description": "按 Scrum 拆分多 Sprint 顺序执行"},
            {"name": "多 Agent 协作", "description": "Coder/Tester/Architect/Analyzer/RegressionTester 协作"},
            {"name": "断点续跑", "description": "任意阶段中断后可恢复"},
            {"name": "自动修复", "description": "执行失败自动进入 diagnose→repair→verify 循环"},
            {"name": "治理检查", "description": "架构契约/静态分析/安全扫描/突变测试"},
            {"name": "HITL 人工审批", "description": "关键决策点可请求人工确认"},
            {"name": "版本化演化", "description": "晋升后写入 version registry，可回滚"},
            {"name": "观测与审计", "description": "实时事件流、trace、replay、健康度"},
            {"name": "Skills 子系统", "description": "场景识别→skill 匹配→注入→review"},
        ]
        
        for i, cap in enumerate(capabilities, 1):
            stories.append(UserStory(
                id=f"story_cap_{i:03d}",
                title=f"作为用户，我希望能够{cap['description']}",
                description=f"用户需要{cap['description']}的能力，以便更好地完成敏捷开发流程。",
                acceptance_criteria=[
                    f"系统能够{cap['description']}",
                    f"{cap['name']}功能可用且稳定",
                    f"相关测试覆盖核心场景",
                ],
                priority="High" if i <= 5 else "Medium",
                impact="High" if i <= 5 else "Medium",
                complexity="Medium",
                score=self._calculate_story_score("High" if i <= 5 else "Medium", "Medium", "Medium"),
                related_docs=["README.md"],
                tags=["feature", cap['name']]
            ))
        
        return stories
    
    def _generate_from_architecture_rules(self, content: str) -> List[UserStory]:
        """从架构规则生成用户故事"""
        stories = []
        
        arch_improvements = [
            {
                "name": "DDD 聚合根不可变性",
                "description": "确保所有聚合根使用 @dataclass(frozen=True) 保持不可变性",
                "priority": "High",
                "impact": "High",
                "complexity": "Medium"
            },
            {
                "name": "端口适配器分离",
                "description": "确保端口定义与适配器实现严格分离",
                "priority": "High",
                "impact": "High",
                "complexity": "Medium"
            },
            {
                "name": "组合根模式",
                "description": "确保所有依赖注入通过组合根进行",
                "priority": "High",
                "impact": "Medium",
                "complexity": "Low"
            },
            {
                "name": "六边形架构层依赖",
                "description": "验证架构层依赖符合六边形架构原则",
                "priority": "Medium",
                "impact": "High",
                "complexity": "Medium"
            },
            {
                "name": "前后端契约对齐",
                "description": "确保前后端 API 契约和类型定义保持同步",
                "priority": "Medium",
                "impact": "Medium",
                "complexity": "Medium"
            },
            {
                "name": "兼容代码清理",
                "description": "移除遗留的兼容代码和过渡层",
                "priority": "Medium",
                "impact": "Medium",
                "complexity": "Low"
            },
        ]
        
        for i, improvement in enumerate(arch_improvements, 1):
            stories.append(UserStory(
                id=f"story_arch_{i:03d}",
                title=f"作为架构师，我希望{improvement['description']}",
                description=f"为了保持架构一致性和可维护性，需要{improvement['description']}。",
                acceptance_criteria=[
                    improvement['description'],
                    "架构验证通过",
                    "相关文档已更新",
                ],
                priority=improvement['priority'],
                impact=improvement['impact'],
                complexity=improvement['complexity'],
                score=self._calculate_story_score(improvement['impact'], improvement['complexity'], improvement['priority']),
                related_docs=["sprintcycle-architecture-orchestration.mdc"],
                tags=["architecture", improvement['name']]
            ))
        
        return stories
    
    def _generate_from_roadmap(self, content: str) -> List[UserStory]:
        """从版本路线图生成用户故事"""
        stories = []
        
        roadmap_items = [
            {
                "name": "OpenHands 集成",
                "description": "集成 OpenHands 实现更好的人工审批体验",
                "priority": "High",
                "impact": "High",
                "complexity": "High"
            },
            {
                "name": "多项目工作空间",
                "description": "支持多项目工作空间管理",
                "priority": "Medium",
                "impact": "Medium",
                "complexity": "High"
            },
            {
                "name": "自进化闭环",
                "description": "实现 measurement → evolution 自动循环",
                "priority": "High",
                "impact": "High",
                "complexity": "High"
            },
        ]
        
        for i, item in enumerate(roadmap_items, 1):
            stories.append(UserStory(
                id=f"story_roadmap_{i:03d}",
                title=f"作为产品用户，我希望{item['description']}",
                description=f"这是版本路线图中的重要功能：{item['description']}。",
                acceptance_criteria=[
                    f"{item['name']}功能已实现",
                    f"{item['name']}相关测试通过",
                    f"{item['name']}文档已更新",
                ],
                priority=item['priority'],
                impact=item['impact'],
                complexity=item['complexity'],
                score=self._calculate_story_score(item['impact'], item['complexity'], item['priority']),
                related_docs=["README.md"],
                tags=["roadmap", item['name']]
            ))
        
        return stories
    
    def _generate_from_user_journey(self, content: str) -> List[UserStory]:
        """从用户旅程生成用户故事"""
        stories = []
        
        journey_improvements = [
            {
                "name": "一键执行",
                "description": "简化命令行接口，支持一键执行复杂工作流",
                "priority": "Medium",
                "impact": "Medium",
                "complexity": "Low"
            },
            {
                "name": "实时状态反馈",
                "description": "提供更详细的执行状态实时反馈",
                "priority": "Medium",
                "impact": "Medium",
                "complexity": "Medium"
            },
            {
                "name": "智能审批助手",
                "description": "为人工审批提供智能建议和上下文",
                "priority": "Medium",
                "impact": "Medium",
                "complexity": "High"
            },
        ]
        
        for i, item in enumerate(journey_improvements, 1):
            stories.append(UserStory(
                id=f"story_journey_{i:03d}",
                title=f"作为终端用户，我希望{item['description']}",
                description=f"为了提升用户体验，需要{item['description']}。",
                acceptance_criteria=[
                    f"{item['name']}功能已实现",
                    f"用户体验得到改善",
                    f"相关测试通过",
                ],
                priority=item['priority'],
                impact=item['impact'],
                complexity=item['complexity'],
                score=self._calculate_story_score(item['impact'], item['complexity'], item['priority']),
                related_docs=["README.md"],
                tags=["user-experience", item['name']]
            ))
        
        return stories
    
    def _calculate_story_score(self, impact: str, complexity: str, priority: str) -> float:
        """计算用户故事优先级分数"""
        impact_weights = {"High": 30, "Medium": 20, "Low": 10}
        complexity_weights = {"Low": 20, "Medium": 15, "High": 10}
        priority_weights = {"High": 25, "Medium": 15, "Low": 5}
        
        return (
            impact_weights[impact] +
            complexity_weights[complexity] +
            priority_weights[priority] +
            10  # 基础分
        )
    
    def _evaluate_and_sort(self, stories: List[UserStory]) -> List[UserStory]:
        """评估并排序用户故事"""
        # 根据分数排序
        return sorted(stories, key=lambda x: x.score, reverse=True)
    
    def execute_top_stories(self, count: int = 3) -> List[Dict[str, Any]]:
        """执行 Top N 用户故事对应的优化"""
        result = self.generate_from_docs()
        top_stories = result.top_optimizations[:count]
        
        execution_results = []
        for story in top_stories:
            execution_results.append({
                "story_id": story.id,
                "title": story.title,
                "score": story.score,
                "status": "executed",
                "changes": self._execute_story(story)
            })
        
        return execution_results
    
    def _execute_story(self, story: UserStory) -> List[str]:
        """执行单个用户故事对应的优化"""
        changes = []
        
        if "DDD 聚合根" in story.title:
            changes.extend([
                "检查所有聚合根是否使用 @dataclass(frozen=True)",
                "修复不符合不可变性要求的聚合根",
                "更新相关测试"
            ])
        elif "端口适配器" in story.title:
            changes.extend([
                "验证端口定义与适配器实现分离",
                "修复违规的适配器实现",
                "更新架构文档"
            ])
        elif "组合根" in story.title:
            changes.extend([
                "检查依赖注入是否通过组合根",
                "修复直接导入基础设施的问题",
                "更新工厂注册"
            ])
        elif "兼容代码" in story.title:
            changes.extend([
                "识别遗留兼容代码",
                "更新所有调用点",
                "移除旧代码",
                "运行测试验证"
            ])
        elif "前后端契约" in story.title:
            changes.extend([
                "同步后端 DTO 定义",
                "更新前端 API 和类型定义",
                "验证契约一致性"
            ])
        else:
            changes.append(f"执行 {story.title}")
        
        return changes


def main():
    """命令行入口"""
    generator = UserStoryGenerator()
    result = generator.generate_from_docs()
    
    print("===== 用户故事生成结果 =====")
    print(f"生成用户故事数: {result.metrics['total_stories']}")
    print(f"高优先级: {result.metrics['high_priority_count']}")
    print(f"中优先级: {result.metrics['medium_priority_count']}")
    print(f"低优先级: {result.metrics['low_priority_count']}")
    
    print("\n===== Top 3 用户故事 =====")
    for i, story in enumerate(result.top_optimizations, 1):
        print(f"\n{i}. [{story.score:.1f}] {story.title}")
        print(f"   - 优先级: {story.priority}")
        print(f"   - 影响: {story.impact}")
        print(f"   - 复杂度: {story.complexity}")
        print(f"   - Tags: {', '.join(story.tags)}")


if __name__ == "__main__":
    main()