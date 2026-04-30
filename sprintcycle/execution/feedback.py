"""
反馈闭环系统 - 实现完整的学习循环

核心组件：
- ExecutionFeedback: 执行反馈数据类
- FeedbackLoop: 反馈收集、分析、应用、持久化

学习循环：
意图 → PRD → 执行 → 结果 → 反馈 → 下次迭代优化

使用方式：
```python
# 创建反馈循环
feedback_loop = FeedbackLoop()

# 收集反馈
feedback = feedback_loop.collect(prd, sprint_results)

# 持久化反馈
feedback_loop.save(feedback)

# 读取历史反馈
all_feedbacks = feedback_loop.get_all_feedbacks()

# 分析改进
suggestions = feedback_loop.analyze(feedback)

# 应用到下次迭代
updated_prd = feedback_loop.apply_to_prd(prd, feedback)
```
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json
import logging
import re
from pathlib import Path


class FeedbackLevel(Enum):
    """反馈级别"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class FeedbackCategory(Enum):
    """反馈类别"""
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    COVERAGE = "coverage"
    COMPLETENESS = "completeness"
    EFFICIENCY = "efficiency"




@dataclass
class ErrorPattern:
    """
    错误模式数据类
    
    用于记录和匹配代码错误模式，支持自学习机制。
    
    使用示例：
    ```python
    pattern = ErrorPattern(
        pattern=r"ModuleNotFoundError: No module named '(.+?)'",
        error_type="import_error",
        root_cause="缺少依赖模块",
        suggested_fix="pip install \\1",
        success_count=5,
    )
    
    if pattern.matches(error_log):
        print(f"匹配成功，可信度: {pattern.success_rate:.0%}")
    ```
    """
    pattern: str
    error_type: str
    root_cause: str
    suggested_fix: str
    success_count: int = 0
    failure_count: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_attempts(self) -> int:
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts
    
    @property
    def confidence(self) -> float:
        base_rate = self.success_rate
        attempt_factor = min(self.total_attempts / 5, 1.0)
        return round(base_rate * attempt_factor, 2)
    
    def matches(self, error_log: str) -> bool:
        try:
            compiled_pattern = re.compile(self.pattern, re.MULTILINE)
            return bool(compiled_pattern.search(error_log))
        except re.error:
            logger.warning(f"无效的正则表达式: {self.pattern}")
            return False
    
    def extract_values(self, error_log: str) -> Dict[str, str]:
        try:
            compiled_pattern = re.compile(self.pattern, re.MULTILINE)
            match = compiled_pattern.search(error_log)
            if match and match.groupdict():
                return match.groupdict()
            elif match:
                return {f"group_{i}": g for i, g in enumerate(match.groups(), 1)}
        except re.error:
            pass
        return {}
    
    def record_success(self) -> None:
        self.success_count += 1
        self.last_seen = datetime.now()
    
    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "error_type": self.error_type,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "confidence": self.confidence,
            "last_seen": self.last_seen.isoformat(),
            "first_seen": self.first_seen.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorPattern":
        data = data.copy()
        if "last_seen" in data and isinstance(data["last_seen"], str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        if "first_seen" in data and isinstance(data["first_seen"], str):
            data["first_seen"] = datetime.fromisoformat(data["first_seen"])
        return cls(**data)
    
    @classmethod
    def from_error_log(
        cls,
        error_log: str,
        error_type: str = "unknown",
        suggested_fix: str = "",
    ) -> Optional["ErrorPattern"]:
        patterns_to_try = [
            (r"ModuleNotFoundError: No module named '([^']+)'", "import_error", "pip install \\1"),
            (r"ImportError: (.+?)(?:\n|$)", "import_error", "检查导入语句"),
            (r"AttributeError: '([^']+)' object has no attribute '([^']+)'", "attribute_error", "检查属性名"),
            (r"TypeError: (.+?)(?:\n|$)", "type_error", "检查参数类型"),
            (r"SyntaxError: (.+?)(?:\n|$)", "syntax_error", "检查语法"),
            (r"NameError: name '([^']+)' is not defined", "name_error", "定义或导入 \\1"),
            (r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'", "file_not_found", "检查文件路径"),
            (r"IndentationError: (.+?)(?:\n|$)", "indentation_error", "检查缩进"),
        ]
        
        for pattern_str, err_type, fix_template in patterns_to_try:
            match = re.search(pattern_str, error_log)
            if match:
                return cls(
                    pattern=pattern_str,
                    error_type=err_type,
                    root_cause=f"自动识别: {err_type}",
                    suggested_fix=suggested_fix or fix_template,
                )
        
        lines = error_log.strip().split("\n")
        first_line = lines[0] if lines else ""
        return cls(
            pattern=re.escape(first_line[:100]),
            error_type=error_type,
            root_cause="未知原因",
            suggested_fix=suggested_fix,
        )

@dataclass
class ExecutionFeedback:
    """执行反馈数据类"""
    prd_id: str = ""
    prd_name: str = ""
    iteration: int = 1
    sprint_name: str = ""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_duration: float = 0.0
    agent_results: List[Dict[str, Any]] = field(default_factory=list)
    feedbacks: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    code_quality_score: float = 0.0
    test_coverage: float = 0.0
    performance_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round(self.successful_tasks / self.total_tasks * 100, 1)
    
    @property
    def overall_score(self) -> float:
        weights = {"quality": 0.4, "coverage": 0.3, "performance": 0.3}
        score = (
            self.code_quality_score * weights["quality"] +
            self.test_coverage * weights["coverage"] +
            self.performance_score * weights["performance"]
        )
        return round(score, 1)
    
    def add_feedback(self, feedback: str, level: FeedbackLevel, category: FeedbackCategory) -> None:
        self.feedbacks.append({
            "feedback": feedback,
            "level": level.value,
            "category": category.value,
            "timestamp": datetime.now().isoformat(),
        })
    
    def add_issue(self, issue: str, severity: str = "medium") -> None:
        self.issues.append({
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prd_id": self.prd_id,
            "prd_name": self.prd_name,
            "iteration": self.iteration,
            "sprint_name": self.sprint_name,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "code_quality_score": self.code_quality_score,
            "test_coverage": self.test_coverage,
            "performance_score": self.performance_score,
            "overall_score": self.overall_score,
            "feedbacks": self.feedbacks,
            "issues": self.issues,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_results(cls, prd_id: str, prd_name: str, sprint_name: str,
                     iteration: int, task_results: List[Any]) -> "ExecutionFeedback":
        feedback = cls(
            prd_id=prd_id, prd_name=prd_name, sprint_name=sprint_name,
            iteration=iteration, total_tasks=len(task_results),
        )
        
        successful = 0
        failed = 0
        total_duration = 0.0
        agent_results = []
        feedbacks = []
        
        for result in task_results:
            if hasattr(result, "status"):
                status_val = getattr(result.status, "value", str(result.status))
                if status_val == "success":
                    successful += 1
                else:
                    failed += 1
            
            if hasattr(result, "duration"):
                total_duration += result.duration
            
            if hasattr(result, "feedback") and result.feedback:
                feedbacks.append(result.feedback)
            
            if hasattr(result, "to_dict"):
                agent_results.append(result.to_dict())
        
        feedback.successful_tasks = successful
        feedback.failed_tasks = failed
        feedback.total_duration = total_duration
        feedback.agent_results = agent_results
        feedback.code_quality_score = cls._calculate_quality_score(feedbacks)
        feedback.test_coverage = cls._calculate_coverage(agent_results)
        feedback.performance_score = cls._calculate_performance_score(total_duration, len(task_results))
        
        return feedback
    
    @staticmethod
    def _calculate_quality_score(feedbacks: List[str]) -> float:
        if not feedbacks:
            return 70.0
        score = 70.0
        for fb in feedbacks:
            fb_lower = fb.lower()
            if "优秀" in fb or "excellent" in fb_lower:
                score += 10
            elif "良好" in fb or "good" in fb_lower:
                score += 5
            elif "改进" in fb or "improve" in fb_lower:
                score -= 5
        return min(max(score, 0), 100)
    
    @staticmethod
    def _calculate_coverage(agent_results: List[Dict]) -> float:
        if not agent_results:
            return 0.0
        coverages = []
        for result in agent_results:
            if "metrics" in result and "coverage" in result["metrics"]:
                coverages.append(result["metrics"]["coverage"])
        if coverages:
            return round(sum(coverages) / len(coverages), 1)
        return 0.0
    
    @staticmethod
    def _calculate_performance_score(duration: float, task_count: int) -> float:
        if task_count == 0:
            return 0.0
        avg_duration = duration / task_count
        baseline = 10.0
        if avg_duration <= baseline:
            return 100.0
        else:
            penalty = (avg_duration - baseline) * 5
            return max(100.0 - penalty, 0.0)


class FeedbackLoop:
    """反馈闭环管理器 - 支持持久化"""
    
    def __init__(self, storage_dir: str = ".sprintcycle/feedback"):
        """初始化反馈循环
        
        Args:
            storage_dir: 反馈持久化存储目录
        """
        self._history: List[ExecutionFeedback] = []
        self._analyzers: List[Callable] = []
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._register_default_analyzers()
    
    # ==================== 持久化方法 ====================
    
    def save(self, feedback: ExecutionFeedback) -> None:
        """持久化反馈到文件"""
        filepath = self._storage_dir / f"{feedback.prd_id}.json"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(feedback.to_dict(), f, ensure_ascii=False, indent=2)
            logger = logging.getLogger(__name__)
            logger.debug(f"💾 反馈已保存: {filepath}")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ 保存反馈失败: {e}")
            raise
    
    def load_history(self, prd_id: str) -> List[ExecutionFeedback]:
        """加载指定 PRD 的历史反馈"""
        filepath = self._storage_dir / f"{prd_id}.json"
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 移除计算属性，它们不是构造参数
            data_copy = data.copy()
            data_copy.pop("success_rate", None)
            data_copy.pop("overall_score", None)
            return [ExecutionFeedback(**data_copy)]
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ 加载历史反馈失败: {e}")
            return []
    
    def get_all_feedbacks(self) -> List[Dict[str, Any]]:
        """获取所有历史反馈"""
        feedbacks = []
        try:
            for filepath in self._storage_dir.glob("*.json"):
                with open(filepath, "r", encoding="utf-8") as f:
                    feedbacks.append(json.load(f))
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ 读取历史反馈失败: {e}")
        return feedbacks
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        all_feedbacks = self.get_all_feedbacks()
        if not all_feedbacks:
            return {"total": 0, "message": "暂无历史反馈"}
        
        total = len(all_feedbacks)
        success_rates = [f.get("success_rate", 0) for f in all_feedbacks]
        quality_scores = [f.get("code_quality_score", 0) for f in all_feedbacks]
        coverage_scores = [f.get("test_coverage", 0) for f in all_feedbacks]
        
        return {
            "total": total,
            "avg_success_rate": round(sum(success_rates) / total, 1),
            "avg_quality_score": round(sum(quality_scores) / total, 1),
            "avg_coverage": round(sum(coverage_scores) / total, 1),
            "latest": all_feedbacks[-1] if all_feedbacks else None,
        }
    
    # ==================== 分析器 ====================
    
    def _register_default_analyzers(self):
        """注册默认分析器"""
        self._analyzers = [
            self._analyze_success_rate,
            self._analyze_quality_trends,
            self._analyze_performance,
            self._analyze_issues,
        ]
    
    def collect(self, prd: Any, results: List[Any]) -> ExecutionFeedback:
        """收集反馈"""
        prd_id = getattr(prd, "id", "") or ""
        prd_name = getattr(prd, "project", type("obj", (), {"name": ""})) or ""
        if hasattr(prd_name, "name"):
            prd_name = prd_name.name
        
        task_results = []
        for result in results:
            if hasattr(result, "task_results"):
                task_results.extend(result.task_results)
            else:
                task_results.append(result)
        
        sprint_name = ""
        if results and hasattr(results[0], "sprint_name"):
            sprint_name = results[0].sprint_name
        elif results and hasattr(results[0], "sprint"):
            sprint_name = results[0].sprint.name
        
        feedback = ExecutionFeedback.from_results(
            prd_id=prd_id, prd_name=prd_name, sprint_name=sprint_name,
            iteration=1, task_results=task_results,
        )
        
        self._history.append(feedback)
        return feedback
    
    def analyze(self, feedback: ExecutionFeedback) -> List[str]:
        """分析反馈，生成改进建议"""
        suggestions = []
        for analyzer in self._analyzers:
            result = analyzer(feedback)
            if result:
                suggestions.extend(result)
        suggestions.extend(self._analyze_common_issues(feedback))
        return suggestions
    
    def _analyze_success_rate(self, feedback: ExecutionFeedback) -> List[str]:
        suggestions = []
        rate = feedback.success_rate
        if rate < 50:
            suggestions.append(f"成功率过低({rate}%)，建议检查任务设计和执行策略")
        elif rate < 80:
            suggestions.append(f"成功率一般({rate}%)，可以进一步优化")
        return suggestions
    
    def _analyze_quality_trends(self, feedback: ExecutionFeedback) -> List[str]:
        suggestions = []
        quality = feedback.code_quality_score
        if quality < 60:
            suggestions.append("代码质量偏低，建议加强代码审查和重构")
        elif quality < 80:
            suggestions.append("代码质量有提升空间，可以考虑使用 Evolver 优化")
        return suggestions
    
    def _analyze_performance(self, feedback: ExecutionFeedback) -> List[str]:
        suggestions = []
        if feedback.total_duration > 0:
            avg_duration = feedback.total_duration / max(feedback.total_tasks, 1)
            if avg_duration > 60:
                suggestions.append(f"任务平均执行时间较长({avg_duration:.1f}s)，建议优化执行策略")
        return suggestions
    
    def _analyze_issues(self, feedback: ExecutionFeedback) -> List[str]:
        suggestions = []
        for issue in feedback.issues:
            severity = issue.get("severity", "medium")
            if severity == "high":
                suggestions.append(f"严重问题需要关注: {issue['issue']}")
        return suggestions
    
    def _analyze_common_issues(self, feedback: ExecutionFeedback) -> List[str]:
        suggestions = []
        coverage = feedback.test_coverage
        if coverage < 50:
            suggestions.append(f"测试覆盖率较低({coverage}%)，建议增加测试用例")
        perf = feedback.performance_score
        if perf < 70:
            suggestions.append(f"性能评分较低({perf})，建议进行性能优化")
        return suggestions
    
    def apply_to_prd(self, prd: Any, feedback: ExecutionFeedback) -> Any:
        """将反馈应用到 PRD"""
        import copy
        updated_prd = copy.deepcopy(prd)
        if hasattr(updated_prd, "metadata"):
            if updated_prd.metadata is None:
                updated_prd.metadata = {}
            updated_prd.metadata["last_feedback"] = feedback.to_dict()
            updated_prd.metadata["iterations"] = updated_prd.metadata.get("iterations", 0) + 1
        suggestions = self.analyze(feedback)
        if hasattr(updated_prd, "config"):
            if updated_prd.config is None:
                updated_prd.config = {}
            updated_prd.config["improvement_suggestions"] = suggestions
        return updated_prd
    
    def get_improvements(self, feedback: ExecutionFeedback) -> List[Dict[str, Any]]:
        """获取改进建议详情"""
        improvements = []
        if feedback.success_rate < 80:
            improvements.append({
                "category": "efficiency", "title": "提高执行成功率",
                "description": f"当前成功率 {feedback.success_rate}%",
                "action": "优化任务定义或增加重试机制",
            })
        if feedback.code_quality_score < 80:
            improvements.append({
                "category": "code_quality", "title": "提升代码质量",
                "description": f"当前质量评分 {feedback.code_quality_score}",
                "action": "使用 Evolver 进行代码优化",
            })
        if feedback.test_coverage < 70:
            improvements.append({
                "category": "coverage", "title": "提升测试覆盖率",
                "description": f"当前覆盖率 {feedback.test_coverage}%",
                "action": "增加测试用例或使用 Tester 重新生成测试",
            })
        if feedback.performance_score < 80:
            improvements.append({
                "category": "performance", "title": "提升性能",
                "description": f"当前性能评分 {feedback.performance_score}",
                "action": "使用 Evolver(strategy=performance) 优化",
            })
        return improvements
    
    def track_learning(self, iterations: Optional[int] = None) -> Dict[str, Any]:
        """跟踪学习进度"""
        history = self._history[-iterations:] if iterations else self._history
        if not history:
            return {"iterations": 0, "message": "暂无学习历史"}
        
        success_rates = [f.success_rate for f in history]
        quality_scores = [f.code_quality_score for f in history]
        performance_scores = [f.performance_score for f in history]
        
        avg_success_rate = sum(success_rates) / len(success_rates)
        avg_quality = sum(quality_scores) / len(quality_scores)
        avg_performance = sum(performance_scores) / len(performance_scores)
        
        if len(history) >= 2:
            success_trend = "improving" if success_rates[-1] > success_rates[0] else "declining"
            quality_trend = "improving" if quality_scores[-1] > quality_scores[0] else "declining"
        else:
            success_trend = "stable"
            quality_trend = "stable"
        
        return {
            "iterations": len(history),
            "avg_success_rate": round(avg_success_rate, 1),
            "avg_quality_score": round(avg_quality, 1),
            "avg_performance_score": round(avg_performance, 1),
            "success_trend": success_trend,
            "quality_trend": quality_trend,
            "latest_overall_score": history[-1].overall_score,
        }
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取反馈历史"""
        history = self._history[-limit:] if limit else self._history
        return [f.to_dict() for f in history]
    
    def export_feedback(self, filepath: str) -> None:
        """导出反馈历史到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_history(), f, ensure_ascii=False, indent=2)
    
    def import_feedback(self, filepath: str) -> None:
        """从文件导入反馈历史"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._history = [ExecutionFeedback(**d) for d in data]


__all__ = [
    "FeedbackLevel",
    "FeedbackCategory",
    "ExecutionFeedback",
    "FeedbackLoop",
    "ErrorPattern",
]
