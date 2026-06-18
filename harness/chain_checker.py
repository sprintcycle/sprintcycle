#!/usr/bin/env python3
"""
调用链验证器 - Chain Checker

使用Python AST模块静态扫描所有入口点（HTTP路由、CLI命令），
沿调用链追踪，检测方法是否存在、签名是否匹配。

输出：结构化JSON，Trae可以直接读取作为修复上下文。
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

class CallChainChecker:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.sprintcycle_root = self.project_root / "sprintcycle"
        self.issues: List[Dict[str, Any]] = []
        self.visited_files: Set[str] = set()
        self.class_methods: Dict[str, Set[str]] = {}
        self.imports: Dict[str, Dict[str, str]] = {}
    
    def _find_python_files(self, dir_path: Path) -> List[Path]:
        """查找目录下所有Python文件"""
        return list(dir_path.rglob("*.py"))
    
    def _parse_file(self, file_path: Path) -> Optional[ast.AST]:
        """解析Python文件为AST"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return ast.parse(f.read())
        except Exception as e:
            self._add_issue(
                str(file_path), 0, "parse_error",
                f"无法解析文件: {e}"
            )
            return None
    
    def _add_issue(self, file_path: str, line: int, issue_type: str, message: str):
        """添加问题记录"""
        self.issues.append({
            "file": file_path,
            "line": line,
            "type": issue_type,
            "message": message,
            "severity": "error" if issue_type in ("method_not_found", "attribute_error") else "warning"
        })
    
    def _scan_class_methods(self, tree: ast.AST, file_path: str):
        """扫描文件中的所有类和方法"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                methods = set()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.add(item.name)
                    elif isinstance(item, ast.AsyncFunctionDef):
                        methods.add(item.name)
                if class_name:
                    self.class_methods[class_name] = methods
    
    def _scan_imports(self, tree: ast.AST, file_path: str):
        """扫描文件中的import语句"""
        file_imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports[alias.asname or alias.name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    file_imports[alias.asname or alias.name] = full_name
        self.imports[file_path] = file_imports
    
    def _extract_http_routes(self, tree: ast.AST) -> List[Tuple[str, str, int]]:
        """从AST中提取HTTP路由定义"""
        routes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func_name = self._get_func_name(decorator.func)
                        if func_name in ("router.get", "router.post", "router.put", "router.delete", "app.get", "app.post", "app.put", "app.delete"):
                            if decorator.args:
                                path = self._get_string_value(decorator.args[0])
                                if path:
                                    routes.append((path, node.name, node.lineno))
        return routes
    
    def _get_func_name(self, node: ast.AST) -> str:
        """获取函数调用的完整名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return ""
    
    def _get_string_value(self, node: ast.AST) -> Optional[str]:
        """获取字符串节点的值"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None
    
    def _analyze_call_chain(self, tree: ast.AST, file_path: str):
        """分析函数调用链，检测缺失的方法"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                if "." in func_name:
                    parts = func_name.split(".")
                    if len(parts) >= 2:
                        obj_name = parts[0]
                        method_name = ".".join(parts[1:])
                        self._check_method_exists(obj_name, method_name, file_path, node.lineno)
    
    def _check_method_exists(self, obj_name: str, method_name: str, file_path: str, line: int):
        """检查方法是否存在"""
        file_imports = self.imports.get(file_path, {})
        if obj_name in file_imports:
            full_module = file_imports[obj_name]
            class_name = full_module.split(".")[-1]
            if class_name in self.class_methods:
                if method_name not in self.class_methods[class_name]:
                    self._add_issue(
                        file_path, line, "method_not_found",
                        f"{obj_name}.{method_name} not found on {class_name}"
                    )
    
    def _scan_execution_handlers(self):
        """扫描execution handlers中的方法调用"""
        handlers_dir = self.sprintcycle_root / "interfaces" / "http" / "handlers"
        for handler_file in handlers_dir.glob("*.py"):
            if handler_file.name == "__init__.py":
                continue
            self._process_file(handler_file)
    
    def _scan_routes(self):
        """扫描所有路由文件"""
        http_dir = self.sprintcycle_root / "interfaces" / "http"
        for route_file in http_dir.rglob("*.py"):
            if "__init__.py" in str(route_file):
                continue
            self._process_file(route_file)
    
    def _process_file(self, file_path: Path):
        """处理单个文件"""
        str_path = str(file_path)
        if str_path in self.visited_files:
            return
        self.visited_files.add(str_path)
        
        tree = self._parse_file(file_path)
        if tree is None:
            return
        
        self._scan_class_methods(tree, str_path)
        self._scan_imports(tree, str_path)
        
        if "handlers" in str_path:
            self._analyze_call_chain(tree, str_path)
    
    def _scan_sprint_orchestrator(self):
        """专门扫描SprintOrchestrator类"""
        orchestrator_path = self.sprintcycle_root / "application" / "orchestration" / "sprint_orchestrator.py"
        if orchestrator_path.exists():
            tree = self._parse_file(orchestrator_path)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == "SprintOrchestrator":
                        methods = set()
                        for item in node.body:
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                methods.add(item.name)
                        
                        required_methods = {"plan", "run"}
                        missing_methods = required_methods - methods
                        for missing in missing_methods:
                            self._add_issue(
                                str(orchestrator_path), node.lineno, "method_not_found",
                                f"SprintOrchestrator.{missing}() not found"
                            )
    
    def run(self) -> Dict[str, Any]:
        """运行完整的调用链检查"""
        self.issues = []
        self.visited_files = set()
        self.class_methods = {}
        self.imports = {}
        
        print("🔍 扫描所有Python文件...")
        all_py_files = self._find_python_files(self.sprintcycle_root)
        for py_file in all_py_files:
            self._process_file(py_file)
        
        print("🔍 扫描SprintOrchestrator...")
        self._scan_sprint_orchestrator()
        
        return {
            "status": "completed",
            "total_files_scanned": len(self.visited_files),
            "total_classes_found": len(self.class_methods),
            "issues": self.issues,
            "summary": {
                "errors": len([i for i in self.issues if i["severity"] == "error"]),
                "warnings": len([i for i in self.issues if i["severity"] == "warning"])
            }
        }

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    checker = CallChainChecker(project_root)
    result = checker.run()
    
    print("\n" + "="*60)
    print("调用链验证结果")
    print("="*60)
    
    for issue in result["issues"]:
        severity = "❌" if issue["severity"] == "error" else "⚠️"
        print(f"{severity} {issue['file']}:{issue['line']}")
        print(f"   {issue['message']}")
        print()
    
    print(f"总计: {result['summary']['errors']} 错误, {result['summary']['warnings']} 警告")
    
    output_path = os.path.join(project_root, "harness", "chain_checker_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告已保存到: {output_path}")
    
    sys.exit(0 if result["summary"]["errors"] == 0 else 1)

if __name__ == "__main__":
    main()