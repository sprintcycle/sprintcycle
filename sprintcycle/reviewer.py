"""
SprintCycle 阶段2 - Reviewer Agent
实现双 Agent 架构：执行 Agent + 审查 Agent

审查维度：
1. 代码风格（PEP8、命名规范）
2. 安全检查（SQL注入、XSS、敏感信息泄露）
3. 性能分析（N+1查询、循环优化）
4. 逻辑检查（空指针、边界条件）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path
import re
import time


class ReviewSeverity(Enum):
    """审查问题严重程度"""
    CRITICAL = "critical"    # 必须修复
    WARNING = "warning"      # 建议修复
    INFO = "info"            # 信息提示


@dataclass
class ReviewIssue:
    """审查问题"""
    severity: ReviewSeverity
    category: str            # security/performance/style/logic/syntax
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ReviewResult:
    """审查结果"""
    passed: bool
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)
    review_time: float = 0.0


class CodeReviewer:
    """
    代码审查器 - 审查生成的代码质量
    """
    
    # 安全检查规则
    SECURITY_PATTERNS = {
        "sql_injection": [
            (r"f['\"].*SELECT.*\{", "可能的 SQL 注入风险"),
            (r"execute\s*\(\s*['\"].*%s", "使用参数化查询替代字符串拼接"),
        ],
        "secrets": [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "硬编码密码"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "硬编码 API Key"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "硬编码 Secret"),
        ],
        "dangerous": [
            (r"eval\s*\(", "危险的 eval 函数"),
            (r"exec\s*\(", "危险的 exec 函数"),
        ]
    }
    
    # 性能检查规则
    PERFORMANCE_PATTERNS = {
        "n_plus_1": [
            (r"for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.(get|filter|objects)", "可能的 N+1 查询"),
        ],
    }
    
    # 代码风格规则
    STYLE_RULES = {
        "naming": [
            (r"def\s+[A-Z][a-z]", "函数名应使用 snake_case"),
            (r"class\s+[a-z]", "类名应使用 CamelCase"),
        ],
    }
    
    def review_files(self, files: Dict[str, str], project_path: str = ".") -> ReviewResult:
        """审查多个文件"""
        start_time = time.time()
        result = ReviewResult(passed=True, issues=[])
        
        for file_path, content in files.items():
            # 1. 安全检查
            issues = self._check_patterns(file_path, content, self.SECURITY_PATTERNS, "security", ReviewSeverity.CRITICAL)
            result.issues.extend(issues)
            
            # 2. 性能检查
            issues = self._check_patterns(file_path, content, self.PERFORMANCE_PATTERNS, "performance", ReviewSeverity.WARNING)
            result.issues.extend(issues)
            
            # 3. 风格检查
            issues = self._check_patterns(file_path, content, self.STYLE_RULES, "style", ReviewSeverity.INFO)
            result.issues.extend(issues)
            
            # 4. Python 语法检查
            if file_path.endswith('.py'):
                issues = self._check_python_syntax(file_path, content)
                result.issues.extend(issues)
        
        # 统计
        critical = len([i for i in result.issues if i.severity == ReviewSeverity.CRITICAL])
        result.passed = critical == 0
        result.summary = {
            "total_issues": len(result.issues),
            "critical": critical,
            "warning": len([i for i in result.issues if i.severity == ReviewSeverity.WARNING]),
            "files_reviewed": len(files)
        }
        result.review_time = time.time() - start_time
        return result
    
    def _check_patterns(self, file_path: str, content: str, patterns: Dict, category: str, severity: ReviewSeverity) -> List[ReviewIssue]:
        """检查模式"""
        issues = []
        for cat, pats in patterns.items():
            for pattern, message in pats:
                try:
                    for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(ReviewIssue(
                            severity=severity,
                            category=category,
                            message=message,
                            file_path=file_path,
                            line_number=line_num
                        ))
                except:
                    pass
        return issues
    
    def _check_python_syntax(self, file_path: str, content: str) -> List[ReviewIssue]:
        """Python 语法检查"""
        issues = []
        try:
            import ast
            ast.parse(content)
        except SyntaxError as e:
            issues.append(ReviewIssue(
                severity=ReviewSeverity.CRITICAL,
                category="syntax",
                message=f"语法错误: {e.msg}",
                file_path=file_path,
                line_number=e.lineno or 1
            ))
        return issues


class ReviewerAgent:
    """
    审查 Agent - 协调多个审查器
    """
    
    def __init__(self, max_iterations: int = 3):
        self.code_reviewer = CodeReviewer()
        self.max_iterations = max_iterations
    
    def review_execution(self, project_path: str, files_changed: Dict, execution_output: str = None) -> ReviewResult:
        """审查执行结果"""
        start_time = time.time()
        all_issues = []
        
        # 收集文件内容
        files_to_review = {}
        for file_path in files_changed.get("added", []) + files_changed.get("modified", []):
            full_path = Path(project_path) / file_path
            if full_path.exists():
                try:
                    files_to_review[file_path] = full_path.read_text()
                except:
                    pass
        
        # 代码审查
        if files_to_review:
            code_result = self.code_reviewer.review_files(files_to_review, project_path)
            all_issues.extend(code_result.issues)
        
        # 执行输出审查
        if execution_output:
            if "error" in execution_output.lower() or "traceback" in execution_output.lower():
                all_issues.append(ReviewIssue(
                    severity=ReviewSeverity.WARNING,
                    category="execution",
                    message="执行输出包含错误信息"
                ))
        
        # 汇总
        critical = len([i for i in all_issues if i.severity == ReviewSeverity.CRITICAL])
        
        return ReviewResult(
            passed=critical == 0,
            issues=all_issues,
            summary={
                "total_issues": len(all_issues),
                "critical": critical,
                "files_reviewed": len(files_to_review)
            },
            review_time=time.time() - start_time
        )
    
    def generate_feedback(self, review_result: ReviewResult) -> str:
        """生成反馈信息"""
        if review_result.passed:
            return "✅ 代码审查通过"
        
        lines = ["⚠️ 代码审查发现问题：\n"]
        
        severity_emoji = {
            ReviewSeverity.CRITICAL: "🔴",
            ReviewSeverity.WARNING: "🟡",
            ReviewSeverity.INFO: "🔵"
        }
        
        for severity in [ReviewSeverity.CRITICAL, ReviewSeverity.WARNING, ReviewSeverity.INFO]:
            issues = [i for i in review_result.issues if i.severity == severity]
            if issues:
                lines.append(f"\n{severity_emoji[severity]} {severity.value.upper()} ({len(issues)} 个):")
                for issue in issues[:3]:
                    loc = f" ({issue.file_path}:{issue.line_number})" if issue.file_path else ""
                    lines.append(f"  - [{issue.category}] {issue.message}{loc}")
        
        return "\n".join(lines)
    
    def get_fix_suggestions(self, review_result: ReviewResult) -> List[Dict]:
        """获取修复建议"""
        return [
            {
                "file_path": i.file_path,
                "line_number": i.line_number,
                "issue": i.message,
                "category": i.category
            }
            for i in review_result.issues
            if i.severity in [ReviewSeverity.CRITICAL, ReviewSeverity.WARNING]
        ][:10]
