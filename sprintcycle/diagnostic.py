#!/usr/bin/env python3
"""
SprintCycle 诊断引擎
支持服务检查、API测试、数据库检查、日志分析
"""
import os
import json
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import urllib.request
import urllib.error

from loguru import logger


class DiagnosticStatus(Enum):
    """诊断状态"""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ProblemType(Enum):
    """问题类型"""
    SERVICE = "service"       # 服务健康检查
    API = "api"               # API 测试
    DATABASE = "database"     # 数据库检查
    LOG = "log"               # 日志分析
    FULL = "full"             # 全面诊断


@dataclass
class DiagnosticIssue:
    """诊断问题"""
    type: str
    severity: DiagnosticStatus
    location: str
    description: str
    suggestion: str = ""


@dataclass
class DiagnosticResult:
    """诊断结果"""
    success: bool
    status: DiagnosticStatus
    issues: List[DiagnosticIssue] = field(default_factory=list)
    report_path: str = ""
    summary: str = ""
    fix_suggestions: List[Dict] = field(default_factory=list)
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ServiceChecker:
    """服务健康检查器"""
    
    @staticmethod
    def check_port(host: str, port: int, timeout: float = 5.0) -> bool:
        """检查端口是否开放"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"端口检查失败: {host}:{port} - {e}")
            return False
    
    @staticmethod
    def check_process(process_name: str) -> bool:
        """检查进程是否运行"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def check_services(self, project_path: str) -> List[DiagnosticIssue]:
        """检查项目相关服务"""
        issues = []
        
        # 常见服务端口检查
        common_ports = [
            ("localhost", 3000, "前端开发服务器"),
            ("localhost", 8080, "后端API服务"),
            ("localhost", 8088, "后端API服务(备用)"),
            ("localhost", 5432, "PostgreSQL"),
            ("localhost", 3306, "MySQL"),
            ("localhost", 6379, "Redis"),
        ]
        
        for host, port, name in common_ports:
            if self.check_port(host, port):
                logger.debug(f"✓ {name} ({host}:{port}) 运行中")
            else:
                issues.append(DiagnosticIssue(
                    type="service",
                    severity=DiagnosticStatus.WARN,
                    location=f"{host}:{port}",
                    description=f"{name} 未运行",
                    suggestion=f"启动 {name} 服务"
                ))
        
        return issues


class APIChecker:
    """API 测试器"""
    
    @staticmethod
    def test_endpoint(url: str, method: str = "GET", 
                      headers: Dict = None, data: Dict = None,
                      timeout: float = 10.0) -> Dict:
        """测试 API 端点"""
        try:
            req_data = None
            if data:
                req_data = urllib.parse.urlencode(data).encode()
            
            req = urllib.request.Request(
                url,
                data=req_data,
                headers=headers or {},
                method=method
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return {
                    "success": True,
                    "status_code": response.status,
                    "body": response.read().decode()[:1000]
                }
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "status_code": e.code,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_api(self, base_url: str, endpoints: List[str] = None) -> List[DiagnosticIssue]:
        """测试 API 端点列表"""
        issues = []
        
        default_endpoints = endpoints or ["/", "/api", "/api/health", "/health"]
        
        for endpoint in default_endpoints:
            url = f"{base_url.rstrip('/')}{endpoint}"
            result = self.test_endpoint(url)
            
            if result["success"]:
                logger.debug(f"✓ API {url} 返回 {result['status_code']}")
            else:
                issues.append(DiagnosticIssue(
                    type="api",
                    severity=DiagnosticStatus.WARN,
                    location=url,
                    description=f"API 调用失败: {result.get('error', 'Unknown')}",
                    suggestion="检查 API 服务是否正常"
                ))
        
        return issues


class DatabaseChecker:
    """数据库检查器"""
    
    def check_database(self, project_path: str) -> List[DiagnosticIssue]:
        """检查数据库连接"""
        issues = []
        
        # 尝试从 .env 读取数据库配置
        env_path = Path(project_path) / ".env"
        db_url = None
        
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip()
                        break
        
        if not db_url:
            # 尝试检测常见数据库文件
            db_files = [
                "db.sqlite3",
                "app.db",
                "xuewanpai.db",
                "data.db"
            ]
            
            for db_file in db_files:
                db_path = Path(project_path) / db_file
                if db_path.exists():
                    logger.debug(f"✓ 发现 SQLite 数据库: {db_file}")
                    return self._check_sqlite(str(db_path), issues)
        
        # 检查 PostgreSQL
        if self._check_postgres(project_path):
            return issues
        
        # 检查 MySQL
        if self._check_mysql(project_path):
            return issues
        
        issues.append(DiagnosticIssue(
            type="database",
            severity=DiagnosticStatus.WARN,
            location=project_path,
            description="未找到数据库配置或数据库文件",
            suggestion="检查 .env 文件中的 DATABASE_URL 配置"
        ))
        
        return issues
    
    def _check_sqlite(self, db_path: str, issues: List) -> List[DiagnosticIssue]:
        """检查 SQLite 数据库"""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            logger.debug(f"✓ SQLite 数据库正常，包含 {len(tables)} 个表")
        except Exception as e:
            issues.append(DiagnosticIssue(
                type="database",
                severity=DiagnosticStatus.FAIL,
                location=db_path,
                description=f"SQLite 连接失败: {e}",
                suggestion="检查数据库文件完整性"
            ))
        return issues
    
    def _check_postgres(self, project_path: str) -> bool:
        """检查 PostgreSQL"""
        try:
            import psycopg2
            # 尝试连接
            return True
        except ImportError:
            return False
    
    def _check_mysql(self, project_path: str) -> bool:
        """检查 MySQL"""
        try:
            import mysql.connector
            return True
        except ImportError:
            return False


class LogAnalyzer:
    """日志分析器"""
    
    def analyze_logs(self, project_path: str, 
                     log_patterns: List[str] = None) -> List[DiagnosticIssue]:
        """分析日志文件"""
        issues = []
        
        # 常见日志文件位置
        log_locations = [
            Path(project_path) / "logs",
            Path(project_path) / "log",
            Path(project_path) / ".sprintcycle" / "logs",
            Path(project_path) / "var" / "log",
        ]
        
        # 默认搜索的错误模式
        patterns = log_patterns or [
            "ERROR",
            "Exception",
            "Traceback",
            "Failed",
            "failed",
            "Error:",
            "CRITICAL"
        ]
        
        found_issues = []
        
        for log_dir in log_locations:
            if not log_dir.exists():
                continue
            
            for log_file in sorted(log_dir.glob("*.log"))[-5:]:  # 最近5个日志文件
                try:
                    with open(log_file, errors='ignore') as f:
                        for i, line in enumerate(f):
                            for pattern in patterns:
                                if pattern in line:
                                    found_issues.append({
                                        "file": str(log_file),
                                        "line": i + 1,
                                        "pattern": pattern,
                                        "content": line.strip()[:200]
                                    })
                                    break
                except Exception as e:
                    logger.debug(f"读取日志文件失败: {log_file} - {e}")
        
        if found_issues:
            issues.append(DiagnosticIssue(
                type="log",
                severity=DiagnosticStatus.WARN,
                location=f"{len(found_issues)} 条日志记录",
                description=f"发现 {len(found_issues)} 条潜在问题日志",
                suggestion="检查日志详情，定位具体错误"
            ))
            
            # 保存详细日志报告
            report_path = Path(project_path) / ".sprintcycle" / "diagnostic_reports"
            report_path.mkdir(parents=True, exist_ok=True)
            
            report_file = report_path / f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(found_issues, f, indent=2, ensure_ascii=False)
            
            logger.info(f"日志分析报告已保存: {report_file}")
        
        return issues


class DiagnosticEngine:
    """诊断引擎"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.service_checker = ServiceChecker()
        self.api_checker = APIChecker()
        self.db_checker = DatabaseChecker()
        self.log_analyzer = LogAnalyzer()
        
        self.report_dir = self.project_path / ".sprintcycle" / "diagnostic_reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, problem_type: str = "full", **kwargs) -> DiagnosticResult:
        """
        运行诊断
        
        Args:
            problem_type: 问题类型 (service/api/database/log/full)
            **kwargs: 额外参数
                - base_url: API 基础 URL
                - endpoints: API 端点列表
                - log_patterns: 日志搜索模式
        
        Returns:
            DiagnosticResult
        """
        logger.info(f"开始诊断: {problem_type}")
        
        all_issues = []
        ptype = ProblemType(problem_type.lower())
        
        if ptype in [ProblemType.SERVICE, ProblemType.FULL]:
            logger.debug("检查服务...")
            all_issues.extend(self.service_checker.check_services(str(self.project_path)))
        
        if ptype in [ProblemType.API, ProblemType.FULL]:
            logger.debug("测试 API...")
            base_url = kwargs.get("base_url", "http://localhost:8088")
            endpoints = kwargs.get("endpoints")
            all_issues.extend(self.api_checker.test_api(base_url, endpoints))
        
        if ptype in [ProblemType.DATABASE, ProblemType.FULL]:
            logger.debug("检查数据库...")
            all_issues.extend(self.db_checker.check_database(str(self.project_path)))
        
        if ptype in [ProblemType.LOG, ProblemType.FULL]:
            logger.debug("分析日志...")
            log_patterns = kwargs.get("log_patterns")
            all_issues.extend(self.log_analyzer.analyze_logs(str(self.project_path), log_patterns))
        
        # 确定整体状态
        has_fail = any(i.severity == DiagnosticStatus.FAIL for i in all_issues)
        has_warn = any(i.severity == DiagnosticStatus.WARN for i in all_issues)
        
        if has_fail:
            overall_status = DiagnosticStatus.FAIL
        elif has_warn:
            overall_status = DiagnosticStatus.WARN
        else:
            overall_status = DiagnosticStatus.PASS
        
        # 生成报告
        report_path = self._save_report(all_issues, overall_status, problem_type)
        
        # 生成修复建议
        fix_suggestions = self._generate_fix_suggestions(all_issues)
        
        result = DiagnosticResult(
            success=overall_status != DiagnosticStatus.FAIL,
            status=overall_status,
            issues=all_issues,
            report_path=str(report_path),
            summary=self._generate_summary(all_issues, overall_status),
            fix_suggestions=fix_suggestions
        )
        
        logger.info(f"诊断完成: {result.status.value}, 发现 {len(all_issues)} 个问题")
        
        return result
    
    def _save_report(self, issues: List[DiagnosticIssue], 
                     status: DiagnosticStatus, 
                     problem_type: str) -> Path:
        """保存诊断报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 报告
        json_path = self.report_dir / f"diagnostic_{timestamp}.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "problem_type": problem_type,
            "status": status.value,
            "issues": [
                {
                    "type": i.type,
                    "severity": i.severity.value,
                    "location": i.location,
                    "description": i.description,
                    "suggestion": i.suggestion
                }
                for i in issues
            ]
        }
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Markdown 报告
        md_path = self.report_dir / f"diagnostic_{timestamp}.md"
        md_content = f"""# 诊断报告

**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**类型**: {problem_type}
**状态**: {status.value}

## 问题列表

| 类型 | 严重性 | 位置 | 描述 | 建议 |
|------|--------|------|------|------|
"""
        for i in issues:
            md_content += f"| {i.type} | {i.severity.value} | {i.location} | {i.description} | {i.suggestion} |\n"
        
        with open(md_path, 'w') as f:
            f.write(md_content)
        
        logger.info(f"诊断报告已保存: {json_path}")
        
        return json_path
    
    def _generate_fix_suggestions(self, issues: List[DiagnosticIssue]) -> List[Dict]:
        """生成修复建议"""
        suggestions = []
        
        for issue in issues:
            if issue.severity == DiagnosticStatus.FAIL:
                suggestions.append({
                    "priority": "high",
                    "type": issue.type,
                    "location": issue.location,
                    "action": issue.suggestion
                })
            elif issue.severity == DiagnosticStatus.WARN:
                suggestions.append({
                    "priority": "medium",
                    "type": issue.type,
                    "location": issue.location,
                    "action": issue.suggestion
                })
        
        return suggestions
    
    def _generate_summary(self, issues: List[DiagnosticIssue], 
                          status: DiagnosticStatus) -> str:
        """生成摘要"""
        fail_count = sum(1 for i in issues if i.severity == DiagnosticStatus.FAIL)
        warn_count = sum(1 for i in issues if i.severity == DiagnosticStatus.WARN)
        
        if status == DiagnosticStatus.PASS:
            return f"诊断通过，无异常问题"
        elif status == DiagnosticStatus.WARN:
            return f"诊断完成，发现 {warn_count} 个警告"
        else:
            return f"诊断完成，发现 {fail_count} 个错误，{warn_count} 个警告"


def quick_diagnose(project_path: str, problem_type: str = "full", **kwargs) -> DiagnosticResult:
    """
    快速诊断入口函数
    
    Args:
        project_path: 项目路径
        problem_type: 问题类型 (service/api/database/log/full)
        **kwargs: 额外参数
    
    Returns:
        DiagnosticResult
    """
    engine = DiagnosticEngine(project_path)
    return engine.run(problem_type, **kwargs)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python diagnostic.py <project_path> [problem_type]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    problem_type = sys.argv[2] if len(sys.argv) > 2 else "full"
    
    result = quick_diagnose(project_path, problem_type)
    print(f"\n诊断结果: {result.status.value}")
    print(f"报告路径: {result.report_path}")
    print(f"\n{result.summary}")
