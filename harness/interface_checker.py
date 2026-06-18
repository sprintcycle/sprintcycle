#!/usr/bin/env python3
"""
接口覆盖验证器 - Interface Checker

扫描所有Protocol/ABC，检查是否有至少一个concrete实现。

输出：结构化JSON，Trae可以直接读取作为修复上下文。
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

class InterfaceChecker:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.sprintcycle_root = self.project_root / "sprintcycle"
        self.issues: List[Dict[str, Any]] = []
        self.visited_files: Set[str] = set()
        self.abc_classes: Dict[str, Dict[str, Any]] = {}
        self.concrete_classes: Dict[str, Dict[str, Any]] = {}
        self.protocol_classes: Dict[str, Dict[str, Any]] = {}
    
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
            "severity": "error" if issue_type == "no_implementation" else "warning"
        })
    
    def _is_abc_class(self, node: ast.ClassDef) -> bool:
        """判断类是否继承自ABC"""
        for base in node.bases:
            base_name = self._get_base_name(base)
            if base_name == "ABC":
                return True
            if "." in base_name and base_name.endswith(".ABC"):
                return True
        return False
    
    def _is_protocol_class(self, node: ast.ClassDef) -> bool:
        """判断类是否是Protocol"""
        for base in node.bases:
            base_name = self._get_base_name(base)
            if base_name == "Protocol":
                return True
            if "." in base_name and base_name.endswith(".Protocol"):
                return True
        return False
    
    def _get_base_name(self, node: ast.AST) -> str:
        """获取基类名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return self._get_base_name(node.value)
        return ""
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return ""
    
    def _has_abstract_methods(self, node: ast.ClassDef) -> bool:
        """检查类是否有抽象方法"""
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in item.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if decorator_name == "abstractmethod":
                        return True
        return False
    
    def _extract_class_info(self, node: ast.ClassDef, file_path: str):
        """提取类信息"""
        class_name = node.name
        is_abc = self._is_abc_class(node)
        is_protocol = self._is_protocol_class(node)
        has_abstract = self._has_abstract_methods(node)
        
        bases = [self._get_base_name(b) for b in node.bases]
        
        class_info = {
            "name": class_name,
            "file": file_path,
            "line": node.lineno,
            "bases": bases,
            "is_abc": is_abc,
            "is_protocol": is_protocol,
            "has_abstract_methods": has_abstract,
            "methods": []
        }
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                class_info["methods"].append(item.name)
        
        if is_abc or has_abstract:
            self.abc_classes[class_name] = class_info
        elif is_protocol:
            self.protocol_classes[class_name] = class_info
        else:
            self.concrete_classes[class_name] = class_info
    
    def _scan_file(self, file_path: Path):
        """扫描单个文件"""
        str_path = str(file_path)
        if str_path in self.visited_files:
            return
        self.visited_files.add(str_path)
        
        tree = self._parse_file(file_path)
        if tree is None:
            return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class_info(node, str_path)
    
    def _find_implementations(self) -> Dict[str, List[str]]:
        """查找每个抽象类/协议的实现"""
        implementations: Dict[str, List[str]] = {}
        
        for abc_name, abc_info in {**self.abc_classes, **self.protocol_classes}.items():
            implementations[abc_name] = []
        
        for concrete_name, concrete_info in self.concrete_classes.items():
            for base in concrete_info["bases"]:
                base_class_name = base.split(".")[-1]
                if base_class_name in implementations:
                    implementations[base_class_name].append(concrete_name)
                if base in implementations:
                    implementations[base].append(concrete_name)
        
        return implementations
    
    def _check_release_plan_generator(self):
        """专门检查ReleasePlanGeneratorProtocol"""
        if "ReleasePlanGeneratorProtocol" in self.protocol_classes:
            proto_info = self.protocol_classes["ReleasePlanGeneratorProtocol"]
            implementations = self._find_implementations()
            impls = implementations.get("ReleasePlanGeneratorProtocol", [])
            if not impls:
                self._add_issue(
                    proto_info["file"], proto_info["line"], "no_implementation",
                    f"ReleasePlanGeneratorProtocol: 0 implementations found"
                )
    
    def run(self) -> Dict[str, Any]:
        """运行完整的接口检查"""
        self.issues = []
        self.visited_files = set()
        self.abc_classes = {}
        self.concrete_classes = {}
        self.protocol_classes = {}
        
        print("🔍 扫描所有Python文件...")
        all_py_files = self._find_python_files(self.sprintcycle_root)
        for py_file in all_py_files:
            self._scan_file(py_file)
        
        print("🔍 检查ReleasePlanGeneratorProtocol实现...")
        self._check_release_plan_generator()
        
        implementations = self._find_implementations()
        
        print("🔍 检查所有ABC/Protocol实现覆盖...")
        for interface_name in {**self.abc_classes, **self.protocol_classes}:
            if interface_name.endswith("Protocol") or (interface_name in self.abc_classes and self.abc_classes[interface_name]["has_abstract_methods"]):
                impls = implementations.get(interface_name, [])
                if not impls:
                    info = self.abc_classes.get(interface_name) or self.protocol_classes.get(interface_name)
                    self._add_issue(
                        info["file"], info["line"], "no_implementation",
                        f"{interface_name}: 0 implementations found"
                    )
        
        return {
            "status": "completed",
            "total_files_scanned": len(self.visited_files),
            "abc_classes_found": len(self.abc_classes),
            "protocol_classes_found": len(self.protocol_classes),
            "concrete_classes_found": len(self.concrete_classes),
            "issues": self.issues,
            "implementations": implementations,
            "summary": {
                "errors": len([i for i in self.issues if i["severity"] == "error"]),
                "warnings": len([i for i in self.issues if i["severity"] == "warning"])
            }
        }

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    checker = InterfaceChecker(project_root)
    result = checker.run()
    
    print("\n" + "="*60)
    print("接口覆盖验证结果")
    print("="*60)
    
    for issue in result["issues"]:
        severity = "❌" if issue["severity"] == "error" else "⚠️"
        print(f"{severity} {issue['file']}:{issue['line']}")
        print(f"   {issue['message']}")
        print()
    
    print("已找到的接口实现关系:")
    print("-" * 40)
    for interface, impls in result["implementations"].items():
        if impls:
            print(f"✅ {interface}: {', '.join(impls)}")
        else:
            print(f"❌ {interface}: 无实现")
    
    print(f"\n总计: {result['summary']['errors']} 错误, {result['summary']['warnings']} 警告")
    
    output_path = os.path.join(project_root, "harness", "interface_checker_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告已保存到: {output_path}")
    
    sys.exit(0 if result["summary"]["errors"] == 0 else 1)

if __name__ == "__main__":
    main()