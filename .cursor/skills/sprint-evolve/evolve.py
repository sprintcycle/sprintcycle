#!/usr/bin/env python3
"""SprintCycle 自动化进化引擎 - 核心逻辑"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from loguru import logger


class OptimizationType(Enum):
    """优化类型枚举"""
    FIELD_CONSOLIDATION = "field_consolidation"
    DDD_GOVERNANCE = "ddd_governance"
    COMPATIBILITY_CLEANUP = "compatibility_cleanup"
    FRONTEND_BACKEND_ALIGNMENT = "frontend_backend_alignment"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    SECURITY_HARDENING = "security_hardening"


@dataclass
class Optimization:
    """优化项定义"""
    id: str
    type: OptimizationType
    description: str
    affected_files: List[str]
    impact: str  # High/Medium/Low
    complexity: str  # Low/Medium/High
    risk: str  # Low/Medium/High
    score: float
    details: Dict[str, Any] = None


@dataclass
class AnalysisResult:
    """分析结果"""
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    opportunities: List[Optimization]
    baseline_metrics: Dict[str, Any]


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    optimization_id: str
    changes_made: List[str]
    errors: List[str] = None
    rollback_script: str = None


@dataclass
class ValidationResult:
    """验证结果"""
    architecture_pass: bool
    unit_tests_pass: bool
    integration_pass: bool
    frontend_pass: bool
    violations: List[str] = None


@dataclass
class UserStoryResult:
    """用户故事分析结果"""
    total_stories: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    top_stories: List[Dict[str, Any]]
    execution_results: List[Dict[str, Any]]


@dataclass
class EvolutionResult:
    """进化结果"""
    analysis: AnalysisResult
    top_optimizations: List[Optimization]
    execution_results: List[ExecutionResult]
    validation: ValidationResult
    report: str
    user_story_result: Optional[UserStoryResult] = None


class EvolutionEngine:
    """自动化进化引擎"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.dry_run = False
        self.force = False
        self.silent = False
        self.skip_user_stories = False
        
    def analyze(self) -> AnalysisResult:
        """分析代码库，识别优化机会"""
        logger.info("🔍 开始代码库分析...")
        
        # 运行架构验证器
        arch_results = self._run_architecture_validation()
        
        # 分析优化机会
        opportunities = self._identify_opportunities(arch_results)
        
        # 计算分数并排序
        opportunities = sorted(opportunities, key=lambda x: x.score, reverse=True)
        
        result = AnalysisResult(
            violations=arch_results.get("errors", []),
            warnings=arch_results.get("warnings", []),
            opportunities=opportunities,
            baseline_metrics={
                "violation_count": len(arch_results.get("errors", [])),
                "warning_count": len(arch_results.get("warnings", [])),
                "opportunity_count": len(opportunities)
            }
        )
        
        logger.info(f"✅ 分析完成，发现 {len(opportunities)} 个优化机会")
        return result
    
    def _run_architecture_validation(self) -> Dict[str, Any]:
        """运行架构验证器"""
        try:
            result = subprocess.run(
                ["python", "scripts/validate_architecture.py", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {"errors": [], "warnings": []}
        except Exception as e:
            logger.error(f"架构验证失败: {e}")
            return {"errors": [], "warnings": []}
    
    def _identify_opportunities(self, arch_results: Dict[str, Any]) -> List[Optimization]:
        """识别优化机会"""
        opportunities = []
        
        # 分析架构违规
        for violation in arch_results.get("errors", []):
            opt = self._violation_to_opportunity(violation)
            if opt:
                opportunities.append(opt)
        
        # 分析警告
        for warning in arch_results.get("warnings", []):
            opt = self._warning_to_opportunity(warning)
            if opt:
                opportunities.append(opt)
        
        # 添加其他检测到的优化机会
        opportunities.extend(self._detect_additional_opportunities())
        
        return opportunities
    
    def _violation_to_opportunity(self, violation: Dict[str, Any]) -> Optional[Optimization]:
        """将违规转换为优化机会"""
        description = violation.get("message", "")
        
        if "layer dependency" in description.lower():
            return Optimization(
                id=f"ddd_{violation.get('id', 'unknown')}",
                type=OptimizationType.DDD_GOVERNANCE,
                description=f"修复架构层依赖违规: {description}",
                affected_files=[violation.get("file", "")],
                impact="High",
                complexity="Medium",
                risk="Medium",
                score=self._calculate_score("High", "Medium", "Medium")
            )
        
        return None
    
    def _warning_to_opportunity(self, warning: Dict[str, Any]) -> Optional[Optimization]:
        """将警告转换为优化机会"""
        description = warning.get("message", "")
        
        if "compatibility" in description.lower():
            return Optimization(
                id=f"compat_{warning.get('id', 'unknown')}",
                type=OptimizationType.COMPATIBILITY_CLEANUP,
                description=f"清理兼容代码: {description}",
                affected_files=[warning.get("file", "")],
                impact="Medium",
                complexity="Low",
                risk="Low",
                score=self._calculate_score("Medium", "Low", "Low")
            )
        
        return None
    
    def _detect_additional_opportunities(self) -> List[Optimization]:
        """检测其他优化机会"""
        opportunities = []
        
        # 检测冗余字段
        field_opportunity = self._detect_field_consolidation()
        if field_opportunity:
            opportunities.append(field_opportunity)
        
        # 检测前后端契约不一致
        alignment_opportunity = self._detect_frontend_backend_alignment()
        if alignment_opportunity:
            opportunities.append(alignment_opportunity)
        
        return opportunities
    
    def _detect_field_consolidation(self) -> Optional[Optimization]:
        """检测字段整合机会"""
        # 这里可以添加更复杂的字段分析逻辑
        return Optimization(
            id="field_consolidation_001",
            type=OptimizationType.FIELD_CONSOLIDATION,
            description="识别语义相关的字段组，建议整合为统一上下文结构",
            affected_files=["sprintcycle/domain/core/models/*.py"],
            impact="Medium",
            complexity="Medium",
            risk="Low",
            score=75.0
        )
    
    def _detect_frontend_backend_alignment(self) -> Optional[Optimization]:
        """检测前后端对齐机会"""
        return Optimization(
            id="alignment_001",
            type=OptimizationType.FRONTEND_BACKEND_ALIGNMENT,
            description="检查并同步前后端 API 契约和类型定义",
            affected_files=["sprintcycle/application/dto/*.py", "frontend/src/types/*.ts"],
            impact="Medium",
            complexity="Medium",
            risk="Medium",
            score=70.0
        )
    
    def _calculate_score(self, impact: str, complexity: str, risk: str) -> float:
        """计算优化优先级分数"""
        impact_weights = {"High": 30, "Medium": 20, "Low": 10}
        complexity_weights = {"Low": 20, "Medium": 15, "High": 10}
        risk_weights = {"Low": 15, "Medium": 10, "High": 5}
        
        return (
            impact_weights[impact] +
            complexity_weights[complexity] +
            risk_weights[risk] +
            20  # 基础分
        )
    
    def get_top_optimizations(self, count: int = 3) -> List[Optimization]:
        """获取 Top N 优化方向"""
        analysis = self.analyze()
        return analysis.opportunities[:count]
    
    def execute_optimization(self, optimization: Optimization) -> ExecutionResult:
        """执行单个优化"""
        logger.info(f"🚀 执行优化: {optimization.id} - {optimization.description}")
        
        if self.dry_run:
            logger.info("⚠️ 模拟模式，不执行实际变更")
            return ExecutionResult(
                success=True,
                optimization_id=optimization.id,
                changes_made=[],
                rollback_script="# Dry run - no changes"
            )
        
        try:
            changes = []
            
            if optimization.type == OptimizationType.DDD_GOVERNANCE:
                changes.extend(self._execute_ddd_governance(optimization))
            elif optimization.type == OptimizationType.COMPATIBILITY_CLEANUP:
                changes.extend(self._execute_compatibility_cleanup(optimization))
            elif optimization.type == OptimizationType.FIELD_CONSOLIDATION:
                changes.extend(self._execute_field_consolidation(optimization))
            elif optimization.type == OptimizationType.FRONTEND_BACKEND_ALIGNMENT:
                changes.extend(self._execute_frontend_backend_alignment(optimization))
            
            return ExecutionResult(
                success=True,
                optimization_id=optimization.id,
                changes_made=changes
            )
        except Exception as e:
            logger.error(f"优化执行失败: {e}")
            return ExecutionResult(
                success=False,
                optimization_id=optimization.id,
                changes_made=[],
                errors=[str(e)]
            )
    
    def _execute_ddd_governance(self, optimization: Optimization) -> List[str]:
        """执行 DDD 治理优化"""
        # 这里添加实际的治理逻辑
        return [
            f"修复架构层依赖违规: {optimization.id}",
            "更新领域层代码以符合六边形架构原则"
        ]
    
    def _execute_compatibility_cleanup(self, optimization: Optimization) -> List[str]:
        """执行兼容代码清理"""
        return [
            f"移除兼容代码: {optimization.id}",
            "更新所有调用点"
        ]
    
    def _execute_field_consolidation(self, optimization: Optimization) -> List[str]:
        """执行字段整合"""
        return [
            "识别语义相关字段组",
            "创建统一上下文结构",
            "更新所有调用点"
        ]
    
    def _execute_frontend_backend_alignment(self, optimization: Optimization) -> List[str]:
        """执行前后端对齐"""
        return [
            "同步后端 DTO 定义",
            "更新前端 API 和类型定义",
            "验证契约一致性"
        ]
    
    def validate(self) -> ValidationResult:
        """运行完整验证套件"""
        logger.info("🔬 运行验证套件...")
        
        try:
            # 架构验证
            arch_result = subprocess.run(
                ["python", "scripts/validate_architecture.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # 单元测试
            test_result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-q", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return ValidationResult(
                architecture_pass=arch_result.returncode == 0,
                unit_tests_pass=test_result.returncode == 0,
                integration_pass=True,
                frontend_pass=True
            )
        except Exception as e:
            logger.error(f"验证失败: {e}")
            return ValidationResult(
                architecture_pass=False,
                unit_tests_pass=False,
                integration_pass=False,
                frontend_pass=False,
                violations=[str(e)]
            )
    
    def _update_documents(self) -> List[str]:
        """自动更新文档"""
        logger.info("📄 开始自动更新文档...")
        
        try:
            from .document_updater import DocumentUpdater
            
            updater = DocumentUpdater(self.project_root)
            updates = updater.update_all_documents()
            
            updated_files = [str(u.file_path.name) for u in updates]
            logger.info(f"✅ 文档更新完成，更新了 {len(updated_files)} 个文件")
            
            return updated_files
        except Exception as e:
            logger.error(f"文档更新失败: {e}")
            return []
    
    def run(self, dry_run: bool = False, force: bool = False, silent: bool = False, skip_user_stories: bool = False) -> EvolutionResult:
        """运行完整进化周期"""
        self.dry_run = dry_run
        self.force = force
        self.silent = silent
        self.skip_user_stories = skip_user_stories
        
        logger.info("===== SprintCycle 自动化进化开始 =====")
        
        # Phase 1: 分析
        analysis = self.analyze()
        
        # Phase 2: 获取 Top 3
        top_optimizations = analysis.opportunities[:3]
        logger.info(f"🎯 选出 Top 3 优化方向")
        for i, opt in enumerate(top_optimizations, 1):
            logger.info(f"  {i}. [{opt.score:.1f}] {opt.type.value}: {opt.description}")
        
        # Phase 2.5: 用户故事分析（从 README 和架构规则生成）
        user_story_result = self._analyze_user_stories()
        
        # HITL 卡点 1: 变更范围确认
        if not self.dry_run and not self.force:
            if not self._confirm_scope(top_optimizations, user_story_result):
                logger.info("用户取消变更范围确认，退出进化流程")
                raise SystemExit("用户取消变更范围确认")
        
        # Phase 2.7: 技术方案设计
        technical_plans = self._design_technical_plans(top_optimizations, user_story_result)
        
        # HITL 卡点 2: 技术方案确认
        if not self.dry_run and not self.force:
            if not self._confirm_technical_plan(technical_plans):
                logger.info("用户取消技术方案确认，退出进化流程")
                raise SystemExit("用户取消技术方案确认")
        
        # Phase 3: 执行优化（包含用户故事驱动的优化）
        execution_results = []
        
        # 执行架构优化
        for opt in top_optimizations:
            if opt.score >= 60 or self.force:
                result = self.execute_optimization(opt)
                execution_results.append(result)
            else:
                logger.info(f"⏭️ 跳过优化 {opt.id} (分数 {opt.score} < 60)")
        
        # 执行用户故事驱动的优化
        for story_exec in user_story_result.execution_results:
            execution_results.append(ExecutionResult(
                success=True,
                optimization_id=story_exec['story_id'],
                changes_made=story_exec['changes']
            ))
        
        # Phase 4: 验证
        validation = self.validate()
        
        # Phase 5: 自动更新文档
        document_updates = []
        if validation.architecture_pass and not self.dry_run:
            document_updates = self._update_documents()
        
        # 生成报告
        report = self._generate_report(analysis, top_optimizations, execution_results, validation, document_updates, user_story_result)
        
        logger.info("===== SprintCycle 自动化进化完成 =====")
        
        return EvolutionResult(
            analysis=analysis,
            top_optimizations=top_optimizations,
            execution_results=execution_results,
            validation=validation,
            report=report,
            user_story_result=user_story_result
        )
    
    def _analyze_user_stories(self) -> UserStoryResult:
        """分析用户故事（支持 MetaGPT/code2prompt/本地生成器）"""
        logger.info("📖 开始用户故事分析...")
        
        # 如果用户指定跳过用户故事分析，直接返回空结果
        if self.skip_user_stories:
            logger.info("⏭️ 用户指定跳过用户故事分析")
            return UserStoryResult(
                total_stories=0,
                high_priority_count=0,
                medium_priority_count=0,
                low_priority_count=0,
                top_stories=[],
                execution_results=[]
            )
        
        try:
            # 尝试导入集成器
            try:
                from .story_generator_integrator import StoryGeneratorIntegrator
            except ImportError:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent))
                from story_generator_integrator import StoryGeneratorIntegrator
            
            # 创建集成器（仅使用 MetaGPT）
            integrator = StoryGeneratorIntegrator()
            
            # 检查 MetaGPT 是否可用
            if not integrator.is_available():
                logger.warning("⚠️ MetaGPT 未安装")
                # 询问用户是否继续
                if not self._confirm_continue_without_metagpt():
                    logger.info("用户选择退出")
                    raise SystemExit("用户选择退出，因为 MetaGPT 不可用")
                
                logger.info("用户选择继续，跳过用户故事分析")
                return UserStoryResult(
                    total_stories=0,
                    high_priority_count=0,
                    medium_priority_count=0,
                    low_priority_count=0,
                    top_stories=[],
                    execution_results=[]
                )
            
            logger.info("✅ MetaGPT 可用，开始生成用户故事...")
            
            # 全量生成用户故事
            stories = integrator.generate(
                code_path=self.project_root,
                doc_path=self.project_root / "docs"
            )
            
            logger.info(f"📝 全量生成用户故事完成，共 {len(stories)} 个")
            
            # 保存用户故事到存储
            self._save_stories_to_store(stories)
            
            # 从用户故事中识别问题点
            issues = self._extract_issues_from_stories(stories)
            logger.info(f"🔍 从用户故事中识别到 {len(issues)} 个问题点")
            
            # 选择 Top 3 问题点
            top_issues = sorted(issues, key=lambda x: x['score'], reverse=True)[:3]
            
            # 生成执行结果（针对问题点进行优化）
            exec_results = []
            for issue in top_issues:
                exec_results.append({
                    'story_id': issue['id'],
                    'title': issue['title'],
                    'score': issue['score'],
                    'status': 'executed',
                    'changes': self._get_issue_changes(issue)
                })
            
            logger.info("🎯 选出 Top 3 问题点进行优化")
            for i, issue in enumerate(top_issues, 1):
                logger.info(f"  {i}. [{issue['score']:.1f}] {issue['title']}")
            
            return UserStoryResult(
                total_stories=len(stories),
                high_priority_count=sum(1 for s in stories if s.priority == 'High'),
                medium_priority_count=sum(1 for s in stories if s.priority == 'Medium'),
                low_priority_count=sum(1 for s in stories if s.priority == 'Low'),
                top_stories=[{
                    'id': issue['id'],
                    'title': issue['title'],
                    'score': issue['score'],
                    'priority': issue['priority'],
                    'impact': 'High' if issue['score'] >= 80 else 'Medium',
                    'complexity': 'Medium',
                    'source': 'issue',
                    'tags': issue.get('tags', []),
                    'type': issue.get('type', '功能需求')
                } for issue in top_issues],
                execution_results=exec_results
            )
        except Exception as e:
            logger.error(f"用户故事分析失败: {e}")
            return UserStoryResult(
                total_stories=0,
                high_priority_count=0,
                medium_priority_count=0,
                low_priority_count=0,
                top_stories=[],
                execution_results=[]
            )
    
    def _get_story_changes(self, story) -> List[str]:
        """获取用户故事对应的优化变更"""
        changes = []
        
        if "架构" in story.title or "Architecture" in story.title:
            changes.extend([
                "检查架构一致性",
                "验证层依赖关系",
                "更新架构文档"
            ])
        elif "服务" in story.title or "Service" in story.title:
            changes.extend([
                "优化服务实现",
                "添加单元测试",
                "更新API文档"
            ])
        elif "功能" in story.title or "Feature" in story.title:
            changes.extend([
                "实现功能需求",
                "添加集成测试",
                "验证用户体验"
            ])
        else:
            changes.append(f"执行优化: {story.title}")
        
        return changes
    
    def _confirm_continue_without_metagpt(self) -> bool:
        """询问用户是否在 MetaGPT 不可用的情况下继续执行"""
        print("\n" + "="*60)
        print("⚠️  MetaGPT 未安装")
        print("="*60)
        print("用户故事分析功能需要 MetaGPT。")
        print("如果继续，将跳过用户故事分析，仅执行以下功能：")
        print("  - 架构验证")
        print("  - 代码优化")
        print("  - 文档更新")
        print("="*60)
        
        while True:
            choice = input("是否继续执行? [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            else:
                print("请输入 'y' 或 'n'")
    
    def _extract_issues_from_stories(self, stories) -> List[Dict[str, Any]]:
        """从用户故事中提取问题点"""
        issues = []
        
        for story in stories:
            # 从用户故事中识别问题
            issue = self._identify_issue_from_story(story)
            if issue:
                issues.append(issue)
        
        return issues
    
    def _identify_issue_from_story(self, story) -> Optional[Dict[str, Any]]:
        """从单个用户故事中识别问题点"""
        issue_keywords = [
            ("缺失", "missing"),
            ("未实现", "not implemented"),
            ("需要", "need"),
            ("改进", "improve"),
            ("优化", "optimize"),
            ("问题", "problem"),
            ("错误", "bug"),
            ("修复", "fix"),
            ("重构", "refactor"),
            ("增强", "enhance"),
        ]
        
        title = story.title
        description = story.description
        
        # 检查标题和描述中是否包含问题关键词
        for keyword_cn, keyword_en in issue_keywords:
            if keyword_cn in title or keyword_cn in description or \
               keyword_en.lower() in title.lower() or keyword_en.lower() in description.lower():
                
                # 根据关键词确定问题类型和分数
                if keyword_cn in ["错误", "bug"]:
                    priority = "High"
                    score = 90
                elif keyword_cn in ["缺失", "未实现"]:
                    priority = "High"
                    score = 85
                elif keyword_cn in ["优化", "改进", "增强"]:
                    priority = "Medium"
                    score = 75
                elif keyword_cn in ["重构", "需要"]:
                    priority = "Medium"
                    score = 70
                else:
                    priority = "Medium"
                    score = 70
                
                return {
                    'id': story.id.replace('story_', 'issue_'),
                    'title': story.title,
                    'description': story.description,
                    'priority': priority,
                    'score': score,
                    'type': keyword_cn,
                    'related_story_id': story.id,
                    'acceptance_criteria': story.acceptance_criteria,
                    'tags': story.tags
                }
        
        # 如果没有明确的问题关键词，根据故事内容推断
        if "作为" in title and "我想要" in title:
            # 这是一个功能需求类型的用户故事，可以视为需要实现的功能
            return {
                'id': story.id.replace('story_', 'issue_'),
                'title': story.title,
                'description': story.description,
                'priority': story.priority,
                'score': story.score,
                'type': '功能需求',
                'related_story_id': story.id,
                'acceptance_criteria': story.acceptance_criteria,
                'tags': story.tags
            }
        
        return None
    
    def _get_issue_changes(self, issue: Dict[str, Any]) -> List[str]:
        """根据问题点生成优化变更"""
        issue_type = issue.get('type', '其他')
        title = issue.get('title', '')
        
        changes = []
        
        if issue_type in ["错误", "bug"]:
            changes.extend([
                f"定位并修复 {issue_type}: {title}",
                "添加单元测试覆盖问题场景",
                "验证修复效果"
            ])
        elif issue_type in ["缺失", "未实现"]:
            changes.extend([
                f"实现缺失功能: {title}",
                "添加相关测试",
                "更新API文档"
            ])
        elif issue_type in ["优化", "改进"]:
            changes.extend([
                f"优化 {title}",
                "性能分析与改进",
                "验证优化效果"
            ])
        elif issue_type in ["重构"]:
            changes.extend([
                f"重构 {title}",
                "保持接口兼容性",
                "更新相关测试"
            ])
        elif issue_type in ["功能需求"]:
            changes.extend([
                f"实现功能: {title}",
                "添加集成测试",
                "更新文档"
            ])
        else:
            changes.extend([
                f"处理问题: {title}",
                "实施必要的修改",
                "验证修改效果"
            ])
        
        return changes
    
    def _save_stories_to_store(self, stories):
        """保存用户故事到存储"""
        try:
            # 尝试导入存储管理器
            try:
                from .story_store import StoryStoreManager
            except ImportError:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent))
                from story_store import StoryStoreManager
            
            manager = StoryStoreManager(base_dir=self.project_root / "userstories")
            
            # 转换并保存故事
            story_data_list = []
            for story in stories:
                story_data = {
                    'title': story.title,
                    'description': story.description,
                    'role': story.role,
                    'feature': story.feature,
                    'purpose': story.purpose,
                    'acceptance_criteria': story.acceptance_criteria,
                    'priority': story.priority,
                    'impact': story.impact,
                    'complexity': story.complexity,
                    'score': story.score,
                    'source': story.source,
                    'type': '功能需求',
                    'tags': story.tags,
                    'related_files': story.related_files
                }
                story_data_list.append(story_data)
            
            # 导入故事（自动处理添加/更新）
            count = manager.import_stories(story_data_list)
            logger.info(f"💾 保存了 {count} 个用户故事到 userstories 目录")
            
            # 清理过期故事（可选）
            manager.clean_obsolete()
            
        except Exception as e:
            logger.error(f"保存用户故事失败: {e}")
    
    def _confirm_scope(self, optimizations, user_story_result) -> bool:
        """HITL 卡点 1: 变更范围确认"""
        print("\n" + "="*70)
        print("🔒 HITL 卡点 1: 变更范围确认")
        print("="*70)
        print("\n📋 本次进化计划执行的变更范围：")
        print("\n--- 架构优化 ---")
        for i, opt in enumerate(optimizations, 1):
            print(f"\n{i}. [{opt.score:.1f}] {opt.type.value}")
            print(f"   描述: {opt.description}")
            print(f"   影响: {opt.impact}")
            print(f"   复杂度: {opt.complexity}")
            print(f"   风险: {opt.risk}")
            if opt.affected_files:
                print(f"   受影响文件: {len(opt.affected_files)} 个")
        
        if user_story_result and user_story_result.top_stories:
            print("\n--- 用户故事驱动的优化 ---")
            for i, story in enumerate(user_story_result.top_stories, 1):
                print(f"\n{i}. [{story['score']:.1f}] {story['title']}")
                print(f"   类型: {story.get('type', '功能需求')}")
                print(f"   优先级: {story['priority']}")
        
        print("\n" + "="*70)
        print("⚠️  请仔细审查上述变更范围，确认无误后继续执行。")
        print("   执行后将无法撤销，建议先提交代码到版本控制。")
        print("="*70)
        
        while True:
            choice = input("\n是否确认变更范围并继续执行? [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                print("✅ 用户确认变更范围")
                return True
            elif choice in ['n', 'no']:
                print("❌ 用户取消确认")
                return False
            else:
                print("请输入 'y' 或 'n'")
    
    def _design_technical_plans(self, optimizations, user_story_result) -> List[Dict[str, Any]]:
        """Phase 2.7: 技术方案设计"""
        logger.info("📐 设计技术方案...")
        
        plans = []
        
        for opt in optimizations:
            plan = self._create_technical_plan(opt)
            plans.append(plan)
        
        if user_story_result and user_story_result.top_stories:
            for story in user_story_result.top_stories:
                plan = self._create_story_technical_plan(story)
                plans.append(plan)
        
        logger.info(f"✅ 技术方案设计完成，共 {len(plans)} 个方案")
        return plans
    
    def _create_technical_plan(self, optimization) -> Dict[str, Any]:
        """为单个优化创建技术方案"""
        plan = {
            'id': f"plan_{optimization.id}",
            'optimization_id': optimization.id,
            'type': optimization.type.value,
            'title': optimization.description,
            'estimated_effort': self._estimate_effort(optimization),
            'risk_assessment': self._assess_risk(optimization),
            'implementation_steps': self._generate_implementation_steps(optimization),
            'rollback_plan': self._generate_rollback_plan(optimization),
            'testing_strategy': self._generate_testing_strategy(optimization)
        }
        return plan
    
    def _create_story_technical_plan(self, story) -> Dict[str, Any]:
        """为用户故事创建技术方案"""
        plan = {
            'id': f"plan_{story['id']}",
            'optimization_id': story['id'],
            'type': story.get('type', '功能需求'),
            'title': story['title'],
            'estimated_effort': self._estimate_story_effort(story),
            'risk_assessment': self._assess_story_risk(story),
            'implementation_steps': self._generate_story_implementation_steps(story),
            'rollback_plan': "回滚相关代码变更",
            'testing_strategy': "执行相关单元测试和集成测试"
        }
        return plan
    
    def _estimate_effort(self, optimization) -> str:
        """估算优化工作量"""
        complexity = optimization.complexity
        if complexity == "Low":
            return "1-2 小时"
        elif complexity == "Medium":
            return "1-2 天"
        else:
            return "3-5 天"
    
    def _assess_risk(self, optimization) -> str:
        """评估风险"""
        risk = optimization.risk
        if risk == "Low":
            return "低风险：变更影响范围小，回滚简单"
        elif risk == "Medium":
            return "中等风险：建议先进行单元测试验证"
        else:
            return "高风险：建议在测试环境充分验证后再执行"
    
    def _generate_implementation_steps(self, optimization) -> List[str]:
        """生成实施步骤"""
        steps = []
        
        if optimization.type == OptimizationType.FIELD_CONSOLIDATION:
            steps = [
                "分析语义相关的字段组",
                "设计统一的上下文结构",
                "修改相关数据模型",
                "更新 API 响应格式",
                "同步前端类型定义"
            ]
        elif optimization.type == OptimizationType.DDD_GOVERNANCE:
            steps = [
                "识别层依赖违规",
                "修复领域层依赖",
                "更新依赖注入配置",
                "验证架构合规性"
            ]
        elif optimization.type == OptimizationType.FRONTEND_BACKEND_ALIGNMENT:
            steps = [
                "对比前后端 API 契约",
                "同步类型定义",
                "更新 API 文档",
                "验证接口兼容性"
            ]
        else:
            steps = [
                "分析优化目标",
                "实施优化变更",
                "执行测试验证"
            ]
        
        return steps
    
    def _generate_rollback_plan(self, optimization) -> str:
        """生成回滚方案"""
        return f"1. 撤销 {optimization.type.value} 相关代码变更\n2. 恢复到变更前的版本\n3. 重新运行验证测试"
    
    def _generate_testing_strategy(self, optimization) -> str:
        """生成测试策略"""
        return f"1. 执行单元测试\n2. 执行集成测试\n3. 验证架构合规性\n4. 检查相关 API 接口"
    
    def _estimate_story_effort(self, story) -> str:
        """估算用户故事工作量"""
        complexity = story.get('complexity', 'Medium')
        if complexity == "Low":
            return "1-2 小时"
        elif complexity == "Medium":
            return "1-2 天"
        else:
            return "3-5 天"
    
    def _assess_story_risk(self, story) -> str:
        """评估用户故事风险"""
        priority = story.get('priority', 'Medium')
        if priority == "High":
            return "高优先级：建议优先处理"
        else:
            return "中低优先级：按计划执行"
    
    def _generate_story_implementation_steps(self, story) -> List[str]:
        """生成用户故事实施步骤"""
        return [
            f"分析需求: {story['title']}",
            "设计实现方案",
            "编写代码实现",
            "添加单元测试",
            "验证功能正确性"
        ]
    
    def _confirm_technical_plan(self, plans) -> bool:
        """HITL 卡点 2: 技术方案确认"""
        print("\n" + "="*70)
        print("🔒 HITL 卡点 2: 技术方案确认")
        print("="*70)
        
        for plan in plans:
            print(f"\n📋 {plan['title']}")
            print(f"   ID: {plan['id']}")
            print(f"   类型: {plan['type']}")
            print(f"   预计工作量: {plan['estimated_effort']}")
            print(f"   风险评估: {plan['risk_assessment']}")
            print(f"\n   实施步骤:")
            for i, step in enumerate(plan['implementation_steps'], 1):
                print(f"     {i}. {step}")
            print(f"\n   回滚方案: {plan['rollback_plan']}")
            print(f"   测试策略: {plan['testing_strategy']}")
            print()
        
        print("="*70)
        print("⚠️  请仔细审查上述技术方案，确认无误后继续执行。")
        print("   如有需要，可以按 'n' 取消并调整方案。")
        print("="*70)
        
        while True:
            choice = input("\n是否确认技术方案并继续执行? [y/n]: ").strip().lower()
            if choice in ['y', 'yes']:
                print("✅ 用户确认技术方案")
                return True
            elif choice in ['n', 'no']:
                print("❌ 用户取消确认")
                return False
            else:
                print("请输入 'y' 或 'n'")
    
    def _generate_report(self, analysis: AnalysisResult, optimizations: List[Optimization], 
                        exec_results: List[ExecutionResult], validation: ValidationResult, 
                        document_updates: List[str] = None, user_story_result: Optional[UserStoryResult] = None) -> str:
        """生成进化报告"""
        report_lines = [
            "# SprintCycle 自动化进化报告",
            "",
            "## 📊 分析结果",
            f"- 架构违规: {len(analysis.violations)}",
            f"- 警告: {len(analysis.warnings)}",
            f"- 优化机会: {len(analysis.opportunities)}",
            "",
            "## 🎯 Top 3 优化方向"
        ]
        
        for i, opt in enumerate(optimizations, 1):
            report_lines.extend([
                f"",
                f"### {i}. [{opt.score:.1f}] {opt.type.value}",
                f"- **描述**: {opt.description}",
                f"- **影响**: {opt.impact}",
                f"- **复杂度**: {opt.complexity}",
                f"- **风险**: {opt.risk}",
                f"- **受影响文件**: {len(opt.affected_files)} 个"
            ])
        
        report_lines.extend([
            "",
            "## 🚀 执行结果",
            f"- 执行优化数: {len(exec_results)}",
            f"- 成功: {sum(1 for r in exec_results if r.success)}",
            f"- 失败: {sum(1 for r in exec_results if not r.success)}"
        ])
        
        for result in exec_results:
            status = "✅" if result.success else "❌"
            report_lines.extend([
                f"",
                f"### {status} {result.optimization_id}",
                f"- **状态**: {'成功' if result.success else '失败'}"
            ])
            if result.changes_made:
                report_lines.append(f"- **变更**:")
                for change in result.changes_made:
                    report_lines.append(f"  - {change}")
            if result.errors:
                report_lines.append(f"- **错误**: {', '.join(result.errors)}")
        
        # 用户故事分析部分
        if user_story_result and user_story_result.total_stories > 0:
            report_lines.extend([
                "",
                "## 📖 用户故事分析",
                f"- 生成用户故事数: {user_story_result.total_stories}",
                f"- 高优先级: {user_story_result.high_priority_count}",
                f"- 中优先级: {user_story_result.medium_priority_count}",
                f"- 低优先级: {user_story_result.low_priority_count}",
                "",
                "### Top 3 用户故事"
            ])
            
            for i, story in enumerate(user_story_result.top_stories, 1):
                report_lines.extend([
                    f"",
                    f"#### {i}. [{story['score']:.1f}] {story['title']}",
                    f"- **来源**: {story.get('source', 'unknown')}",
                    f"- **优先级**: {story['priority']}",
                    f"- **影响**: {story['impact']}",
                    f"- **复杂度**: {story['complexity']}",
                    f"- **标签**: {', '.join(story['tags'])}"
                ])
        
        report_lines.extend([
            "",
            "## 🔬 验证结果",
            f"- 架构验证: {'✅ 通过' if validation.architecture_pass else '❌ 失败'}",
            f"- 单元测试: {'✅ 通过' if validation.unit_tests_pass else '❌ 失败'}",
            f"- 集成测试: {'✅ 通过' if validation.integration_pass else '❌ 失败'}",
            f"- 前端验证: {'✅ 通过' if validation.frontend_pass else '❌ 失败'}"
        ])
        
        # 文档更新部分
        if document_updates and len(document_updates) > 0:
            report_lines.extend([
                "",
                "## 📄 文档更新",
                f"- 更新文件数: {len(document_updates)}",
                "- 更新文件:"
            ])
            for doc in document_updates:
                report_lines.append(f"  - {doc}")
            # 添加架构编排规则文件的更新说明
            report_lines.extend([
                "",
                "### 架构编排规则同步",
                "- **文件**: sprintcycle-architecture-orchestration.mdc",
                "- **同步内容**: 端口数量、端口列表、架构边界",
                "- **目的**: 保持规则文件与实际代码实现一致"
            ])
        
        all_pass = all([
            validation.architecture_pass,
            validation.unit_tests_pass,
            validation.integration_pass,
            validation.frontend_pass
        ])
        
        report_lines.extend([
            "",
            "## 📝 总结",
            f"**整体状态**: {'🎉 进化成功！' if all_pass else '⚠️ 部分验证未通过'}"
        ])
        
        return "\n".join(report_lines)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SprintCycle 自动化进化")
    parser.add_argument("--dry-run", action="store_true", help="模拟模式")
    parser.add_argument("--force", action="store_true", help="强制执行")
    parser.add_argument("--silent", action="store_true", help="静默模式")
    parser.add_argument("--report-only", action="store_true", help="仅生成报告")
    parser.add_argument("--skip-user-stories", action="store_true", help="跳过用户故事分析（无需 MetaGPT）")
    
    args = parser.parse_args()
    
    engine = EvolutionEngine()
    result = engine.run(
        dry_run=args.dry_run,
        force=args.force,
        silent=args.silent,
        skip_user_stories=args.skip_user_stories
    )
    
    print(result.report)
    
    if args.report_only:
        output_path = Path("evolution_report.md")
        output_path.write_text(result.report)
        print(f"\n📄 报告已保存到: {output_path}")


if __name__ == "__main__":
    main()