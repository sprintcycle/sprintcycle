"""
ProjectDiagnostic - 项目诊断提供者

多维度项目体检:
- 代码诊断: 覆盖率、复杂度、类型错误、测试失败
- 架构诊断: 模块耦合、循环依赖
- 文档诊断: 覆盖率、时效性
- 历史诊断: 改动记录、效果评估
"""

import logging
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass

from .health_report import ProjectHealthReport, CodeIssue, IssueSeverity

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticConfig:
    """诊断配置"""
    project_path: str = "."
    test_command: str = "python -m pytest tests/ -v --tb=short"
    coverage_command: str = "python -m pytest --cov --cov-report=json"
    complexity_threshold: int = 10  # 复杂度阈值
    timeout: int = 300  # 超时时间（秒）


    @classmethod
    def from_runtime_config(cls, rc) -> "DiagnosticConfig":
        """Construct from RuntimeConfig."""
        return cls(
            test_command=getattr(rc, 'test_command', 'python -m pytest tests/ -v --tb=short'),
            coverage_command=getattr(rc, 'coverage_command', 'python -m pytest --cov --cov-report=json'),
            complexity_threshold=getattr(rc, 'complexity_threshold', 10),
            timeout=getattr(rc, 'diagnostic_timeout', 300),
        )


class ProjectDiagnostic:
    """
    项目诊断提供者
    
    执行多维度项目体检，返回ProjectHealthReport
    """
    
    def __init__(
        self,
        config: Optional[DiagnosticConfig] = None,
        runtime_config=None,
        runner: Optional[Callable[..., Tuple[int, str, str]]] = None,
    ):
        """
        初始化诊断提供者
        
        Args:
            config: 诊断配置
            runner: 命令执行器（用于测试mock）
        """
        if config is None and runtime_config is not None:
            config = DiagnosticConfig.from_runtime_config(runtime_config)
        self.config = config or DiagnosticConfig()
        self._runner = runner or self._default_runner
    
    def _default_runner(
        self, cmd: str, cwd: str = ".", timeout: int = 300
    ) -> Tuple[int, str, str]:
        """默认命令执行器"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def diagnose(self, project_path: str) -> ProjectHealthReport:
        """
        执行完整项目诊断
        
        Args:
            project_path: 项目路径
            
        Returns:
            ProjectHealthReport
        """
        report = ProjectHealthReport(target=project_path)
        
        # 1. 代码诊断
        self._diagnose_code(project_path, report)
        
        # 2. 架构诊断
        self._diagnose_architecture(project_path, report)
        
        # 3. 文档诊断
        self._diagnose_docs(project_path, report)
        
        # 4. 历史诊断
        self._analyze_history(project_path, report)
        
        logger.info(f"诊断完成: {project_path}, 健康评分: {report.health_score:.1f}")
        return report
    
    def _diagnose_code(
        self, project_path: str, report: ProjectHealthReport
    ) -> None:
        """
        诊断代码维度
        
        - 运行pytest获取测试失败
        - 运行coverage获取覆盖率
        - 运行radon获取复杂度
        - 运行mypy获取类型错误
        
        每个子诊断步骤独立 try-except，确保单个工具失败不影响整体诊断。
        """
        # 1. 测试失败诊断
        try:
            returncode, stdout, stderr = self._runner(
                self.config.test_command, project_path, self.config.timeout
            )
            failed_match = re.search(r"(\d+) failed", stdout + stderr)
            if failed_match:
                report.test_failures = int(failed_match.group(1))
        except Exception as e:
            logger.warning(f"测试失败诊断异常: {e}")
        
        # 2. 覆盖率诊断
        try:
            coverage_file = Path(project_path) / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    data = json.load(f)
                # 总覆盖率
                totals = data.get("totals", {})
                report.coverage_total = totals.get("percent_covered", 0.0)
                # 各模块覆盖率
                for file_path, info in data.get("files", {}).items():
                    module_name = Path(file_path).stem
                    report.coverage_modules[module_name] = info.get("percent_covered", 0.0)
        except Exception as e:
            logger.warning(f"覆盖率诊断异常: {e}")
        
        # 3. 复杂度诊断
        try:
            returncode, stdout, stderr = self._runner(
                f"cd {project_path} && python -m radon cc -a -j sprintcycle/",
                project_path, 60
            )
            if returncode == 0 and stdout:
                data = json.loads(stdout)
                high_complexity = [
                    item for item in data
                    if item.get("complexity", 0) >= self.config.complexity_threshold
                ]
                report.complexity_high = len(high_complexity)
                # 添加代码问题
                for item in high_complexity[:10]:
                    report.code_issues.append(CodeIssue(
                        file=item.get("file", ""),
                        line=item.get("line", 0),
                        severity=IssueSeverity.MEDIUM,
                        message=f"高复杂度函数: {item.get('name', 'unknown')} (复杂度: {item.get('complexity', 0)})",
                        rule="high_complexity",
                        tool="radon",
                    ))
        except json.JSONDecodeError:
            logger.warning("复杂度输出JSON解析失败")
        except Exception as e:
            logger.warning(f"复杂度诊断异常: {e}")
        
        # 4. 类型错误诊断
        try:
            returncode, stdout, stderr = self._runner(
                f"cd {project_path} && python -m mypy sprintcycle/ --no-error-summary --output=json 2>/dev/null || true",
                project_path, 120
            )
            if stdout:
                for line in stdout.strip().split("\n"):
                    if line.strip():
                        report.mypy_errors += 1
                        match = re.match(r"(.+?):(\d+):(\d+): (.+)", line)
                        if match:
                            report.code_issues.append(CodeIssue(
                                file=match.group(1),
                                line=int(match.group(2)),
                                severity=IssueSeverity.HIGH,
                                message=match.group(4),
                                tool="mypy",
                            ))
        except Exception as e:
            logger.warning(f"类型错误诊断异常: {e}")
    
    def _diagnose_architecture(
        self, project_path: str, report: ProjectHealthReport
    ) -> None:
        """
        诊断架构维度
        
        - 分析模块结构
        - 检测循环依赖
        - 计算模块耦合度
        """
        sprintcycle_path = Path(project_path) / "sprintcycle"
        if not sprintcycle_path.exists():
            return
        
        # 分析导入关系
        imports: Dict[str, set] = {}
        
        for py_file in sprintcycle_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            module_name = str(py_file.relative_to(sprintcycle_path)).replace("/", ".").replace(".py", "")
            
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 提取导入
                module_imports = set()
                for match in re.finditer(r"from\s+(?:sprintcycle\.)?(\w+)", content):
                    module_imports.add(match.group(1))
                for match in re.finditer(r"import\s+(?:sprintcycle\.)?(\w+)", content):
                    module_imports.add(match.group(1))
                
                imports[module_name] = module_imports
                
            except Exception as e:
                logger.debug(f"读取模块 {py_file.name} 失败: {e}")
        
        # 检测循环依赖
        circular = self._find_circular_dependencies(imports)
        report.circular_deps = circular
        
        # 计算模块耦合度 (简化版: 平均导入数)
        if imports:
            avg_coupling = sum(len(imps) for imps in imports.values()) / len(imports)
            report.module_coupling = min(avg_coupling / 10, 1.0)  # 归一化
    
    def _find_circular_dependencies(self, imports: Dict[str, set]) -> List[str]:
        """检测循环依赖"""
        circular = []
        
        for module, deps in imports.items():
            for dep in deps:
                if dep in imports and module in imports[dep]:
                    circular.append(f"{module} <-> {dep}")
        
        # 去重
        return list(set(circular))[:10]  # 最多10个
    
    def _diagnose_docs(
        self, project_path: str, report: ProjectHealthReport
    ) -> None:
        """
        诊断文档维度
        
        - 计算文档覆盖率
        - 检测过时文档
        """
        sprintcycle_path = Path(project_path) / "sprintcycle"
        docs_path = Path(project_path) / "docs"
        
        if not sprintcycle_path.exists():
            return
        
        # 统计Python文件和文档文件
        py_files = list(sprintcycle_path.rglob("*.py"))
        py_files = [f for f in py_files if not f.name.startswith("_")]
        
        doc_files = []
        if docs_path.exists():
            doc_files = list(docs_path.rglob("*.md"))
        
        # 计算文档覆盖率 (文档文件数 / Python文件数)
        if py_files:
            report.doc_coverage = min(len(doc_files) / len(py_files) * 100, 100.0)
        
        # 检测过时文档 (超过6个月未修改)
        # 简化处理: 检查文档中是否包含最新版本标记
        outdated = []
        for doc in doc_files:
            try:
                doc_content = doc.read_text()
                if "v0.9" not in doc_content and "v0.8" not in doc_content:
                    outdated.append(str(doc))
            except Exception as e:
                logger.debug(f"读取文档 {doc.name} 失败: {e}")
        
        report.outdated_docs = outdated[:5]  # 最多5个
    
    def _analyze_history(
        self, project_path: str, report: ProjectHealthReport
    ) -> None:
        """
        分析进化历史
        
        - 从evolution_cache读取历史
        - 分析有效/失败模式
        - 计算覆盖率趋势
        """
        # 尝试从evolution_cache读取历史
        cache_path = Path(project_path) / "evolution_cache"
        
        if not cache_path.exists():
            return
        
        # 读取历史记录
        history_records = []
        for json_file in cache_path.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        history_records.extend(data)
                    else:
                        history_records.append(data)
            except Exception as e:
                logger.debug(f"读取历史记录 {json_file.name} 失败: {e}")
        
        # 分析有效模式
        effective = set()
        failed = set()
        
        for record in history_records[-10:]:  # 最近10条
            success = record.get("success", False)
            tags = record.get("tags", [])
            coverage_delta = record.get("coverage_delta")
            
            if success:
                for tag in tags:
                    effective.add(tag)
                if coverage_delta is not None:
                    report.coverage_trend += coverage_delta
            else:
                for tag in tags:
                    failed.add(tag)
        
        report.effective_patterns = list(effective)[:10]
        report.failed_patterns = list(failed)[:10]
        report.rollback_count = sum(1 for r in history_records[-10:] if not r.get("success", True))
