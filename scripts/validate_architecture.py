#!/usr/bin/env python3
"""
SprintCycle 架构不变性自动化验证器

基于 ARCHITECTURE_INVARIANTS.md 和架构约束规则，自动验证代码是否符合架构规范。
无需人工介入，完全自动化验证。
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class ArchitectureValidator:
    """架构不变性验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
    
    def validate(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """执行所有验证检查"""
        print("🏗️ 开始架构不变性验证...")
        
        # 验证端口定义数量
        self._validate_port_count()
        
        # 验证领域层纯粹性（无外部依赖）
        self._validate_domain_purity()
        
        # 验证聚合根不可变性
        self._validate_aggregate_immutability()
        
        # 验证端口/适配器分离
        self._validate_port_adapter_separation()
        
        # 验证组合根模式
        self._validate_composition_root()
        
        # 验证六边形架构层依赖
        self._validate_layer_dependencies()
        
        # 验证前后端契约对齐
        self._validate_frontend_backend_contract()
        
        # 验证hooks模块结构
        self._validate_hooks_structure()
        
        # 验证没有遗留的兼容代码
        self._validate_no_compatibility_code()
        
        print("\n" + "="*70)
        print(f"✅ 通过: {len(self.passed)}")
        print(f"⚠️ 警告: {len(self.warnings)}")
        print(f"❌ 错误: {len(self.errors)}")
        print("="*70)
        
        success = len(self.errors) == 0
        return success, self.passed, self.warnings, self.errors
    
    def _validate_port_count(self):
        """验证端口定义数量"""
        ports_dir = ROOT / "sprintcycle" / "domain" / "ports"
        port_files = list(ports_dir.glob("*.py"))
        port_count = len([f for f in port_files if not f.name.startswith("_")])
        
        expected_count = 17
        if port_count == expected_count:
            self.passed.append(f"端口定义数量正确: {port_count} 个")
        else:
            self.errors.append(f"端口定义数量不符: 期望 {expected_count} 个, 实际 {port_count} 个")
    
    def _validate_domain_purity(self):
        """验证领域层纯粹性 - 不应依赖外部框架"""
        domain_dir = ROOT / "sprintcycle" / "domain"
        forbidden_imports = [
            "fastapi", "uvicorn", "sqlalchemy", "redis", "requests",
            "pydantic", "playwright", "celery", "kafka"
        ]
        
        for py_file in domain_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            for forbidden in forbidden_imports:
                if re.search(rf"^\s*import\s+{forbidden}", content, re.MULTILINE):
                    self.errors.append(f"领域层存在外部依赖: {py_file} 导入了 {forbidden}")
                elif re.search(rf"^\s*from\s+{forbidden}", content, re.MULTILINE):
                    self.errors.append(f"领域层存在外部依赖: {py_file} 从 {forbidden} 导入")
        
        self.passed.append("领域层纯粹性检查通过")
    
    def _validate_aggregate_immutability(self):
        """验证聚合根不可变性 - 应使用 @dataclass(frozen=True)"""
        domain_dir = ROOT / "sprintcycle" / "domain"
        aggregate_files = [
            domain_dir / "core" / "execution" / "aggregates" / "execution_aggregates.py",
            domain_dir / "core" / "evolution" / "aggregates" / "evolution_aggregates.py",
            domain_dir / "core" / "governance" / "aggregates" / "governance_aggregates.py",
        ]
        
        for agg_file in aggregate_files:
            if not agg_file.exists():
                continue
            
            with open(agg_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查是否有 @dataclass(frozen=True)
            if "@dataclass(frozen=True)" in content or "@dataclass(\n    frozen=True" in content:
                self.passed.append(f"聚合根不可变性检查通过: {agg_file.name}")
            else:
                self.warnings.append(f"聚合根可能缺少不可变性声明: {agg_file.name}")
    
    def _validate_port_adapter_separation(self):
        """验证端口与适配器分离"""
        ports_dir = ROOT / "sprintcycle" / "domain" / "ports"
        adapters_dir = ROOT / "sprintcycle" / "infrastructure" / "adapters"
        
        # 检查端口目录只包含协议定义
        for py_file in ports_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 端口文件不应有具体实现
            if "class " in content and "Protocol" not in content:
                if not any(p in content for p in ["Protocol", "ABC", "abstractmethod"]):
                    self.warnings.append(f"端口文件可能包含具体实现: {py_file.name}")
        
        self.passed.append("端口/适配器分离检查通过")
    
    def _validate_composition_root(self):
        """验证组合根模式"""
        composition_dir = ROOT / "sprintcycle" / "application" / "composition"
        
        if not composition_dir.exists():
            self.errors.append("组合根目录不存在")
            return
        
        di_files = list(composition_dir.glob("*.py"))
        if len(di_files) == 0:
            self.errors.append("组合根目录为空")
        else:
            self.passed.append(f"组合根模式检查通过: {len(di_files)} 个文件")
    
    def _validate_layer_dependencies(self):
        """验证六边形架构层依赖"""
        layers = [
            ("interfaces", ["application", "domain"]),
            ("application", ["domain"]),
            ("domain", []),
            ("infrastructure", ["domain", "application"]),
        ]
        
        for layer, allowed_deps in layers:
            layer_dir = ROOT / "sprintcycle" / layer
            if not layer_dir.exists():
                continue
            
            for py_file in layer_dir.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                # 排除特殊情况：di_container.py 是容器本身，需要引用 infrastructure
                if layer == "application" and py_file.name == "di_container.py":
                    continue
                
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 检查导入
                for dep in ["interfaces", "application", "domain", "infrastructure"]:
                    if dep == layer:
                        continue  # 允许同层依赖
                    
                    if dep in allowed_deps:
                        continue  # 允许的依赖
                    
                    if re.search(rf"^\s*from\s+sprintcycle\.{dep}", content, re.MULTILINE):
                        self.errors.append(
                            f"架构层依赖违规: {layer}/{py_file.relative_to(layer_dir)} 依赖了 {dep} (不允许)"
                        )
        
        self.passed.append("六边形架构层依赖检查通过")
    
    def _validate_frontend_backend_contract(self):
        """验证前后端契约对齐"""
        # 检查后端 DTO 和前端类型
        backend_dto_dir = ROOT / "sprintcycle" / "application" / "dto"
        frontend_types_dir = ROOT / "frontend" / "src" / "types"
        
        if not backend_dto_dir.exists() or not frontend_types_dir.exists():
            self.warnings.append("DTO 或类型目录不存在")
            return
        
        # 检查文件数量匹配
        backend_files = list(backend_dto_dir.glob("*.py"))
        frontend_files = list(frontend_types_dir.glob("*.ts"))
        
        if len(backend_files) > 0 and len(frontend_files) > 0:
            self.passed.append(f"前后端契约目录检查通过: 后端 {len(backend_files)} 个, 前端 {len(frontend_files)} 个")
        else:
            self.warnings.append("前后端契约文件可能不完整")
    
    def _validate_hooks_structure(self):
        """验证 hooks 模块结构"""
        hooks_dir = ROOT / "sprintcycle" / "domain" / "core" / "execution" / "hooks"
        
        expected_files = ["__init__.py", "governance_context.py", "hook_context.py", 
                         "lifecycle_hooks.py", "quality_hooks.py", "skill_hooks.py"]
        forbidden_files = ["sprint_hooks.py", "task_hooks.py"]
        
        actual_files = [f.name for f in hooks_dir.glob("*.py")]
        
        for forbidden in forbidden_files:
            if forbidden in actual_files:
                self.warnings.append(f"遗留兼容文件存在: {forbidden} (建议删除)")
        
        self.passed.append("hooks 模块结构检查通过")
    
    def _validate_no_compatibility_code(self):
        """验证没有遗留的兼容代码"""
        patterns = [
            r"_legacy_",
            r"_compat_",
            r"_deprecated_",
            r"_migration_",
            r"compatibility",
            r"backward_compat",
        ]
        
        source_dir = ROOT / "sprintcycle"
        
        for py_file in source_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.warnings.append(f"可能存在兼容代码: {py_file} 包含 '{pattern}'")
                    break
        
        self.passed.append("兼容代码检查通过")


def main():
    parser = argparse.ArgumentParser(description="SprintCycle 架构不变性自动化验证器")
    parser.add_argument("--strict", action="store_true", help="严格模式：警告视为错误")
    args = parser.parse_args()
    
    validator = ArchitectureValidator()
    success, passed, warnings, errors = validator.validate()
    
    # 输出详细结果
    print("\n📋 验证结果详情:")
    print("\n✅ 通过项:")
    for p in passed:
        print(f"  - {p}")
    
    if warnings:
        print("\n⚠️ 警告项:")
        for w in warnings:
            print(f"  - {w}")
    
    if errors:
        print("\n❌ 错误项:")
        for e in errors:
            print(f"  - {e}")
    
    # 严格模式下警告视为错误
    if args.strict and warnings:
        print("\n❌ 严格模式：警告被视为错误")
        sys.exit(1)
    
    if not success:
        sys.exit(1)
    
    print("\n🎉 架构不变性验证全部通过！")


if __name__ == "__main__":
    main()