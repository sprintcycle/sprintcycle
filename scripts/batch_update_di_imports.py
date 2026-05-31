#!/usr/bin/env python3
"""
批量更新导入语句脚本

将所有从 sprintcycle.domain.ports 导入 get_*() 函数的语句，
更新为从 sprintcycle.application.composition.di_bridge 导入。
"""

import re
from pathlib import Path

# 需要更新的导入模式
IMPORT_PATTERNS = {
    # 格式: (旧导入, 新导入)
    r"from sprintcycle\.domain\.ports\.(state_store|cache|config|observability|diagnostics|audit|rate_limit|registry|hitl|suggestion|knowledge|governance|deploy|evolution|llm|integrations) import get_(\w+)": 
        r"from sprintcycle.application.composition.di_bridge import get_\2",
}

# 需要更新的具体导入映射
SPECIFIC_IMPORTS = {
    # get_state_store 和 ExecutionStatus
    r"from sprintcycle\.domain\.ports\.state_store import (get_state_store|ExecutionState)":
        lambda m: f"from sprintcycle.application.composition.di_bridge import {m.group(1)}",
    
    # get_cache_backend
    r"from sprintcycle\.domain\.ports\.cache import get_cache_backend":
        "from sprintcycle.application.composition.di_bridge import get_cache_backend",
    
    # get_runtime_config
    r"from sprintcycle\.domain\.ports\.config import get_runtime_config":
        "from sprintcycle.application.composition.di_bridge import get_runtime_config",
    
    # get_observability_facade
    r"from sprintcycle\.domain\.ports\.observability import get_observability_facade":
        "from sprintcycle.application.composition.di_bridge import get_observability_facade",
    
    # get_diagnostic_adapter
    r"from sprintcycle\.domain\.ports\.diagnostics import get_diagnostic_adapter":
        "from sprintcycle.application.composition.di_bridge import get_diagnostic_adapter",
    
    # get_audit_adapter
    r"from sprintcycle\.domain\.ports\.audit import get_audit_adapter":
        "from sprintcycle.application.composition.di_bridge import get_audit_adapter",
    
    # get_rate_limit_adapter
    r"from sprintcycle\.domain\.ports\.rate_limit import get_rate_limit_adapter":
        "from sprintcycle.application.composition.di_bridge import get_rate_limit_adapter",
    
    # get_hitl_store
    r"from sprintcycle\.domain\.ports\.hitl import get_hitl_store":
        "from sprintcycle.application.composition.di_bridge import get_hitl_store",
    
    # get_suggestion_store
    r"from sprintcycle\.domain\.ports\.suggestion import get_suggestion_store":
        "from sprintcycle.application.composition.di_bridge import get_suggestion_store",
    
    # get_knowledge_repository
    r"from sprintcycle\.domain\.ports\.knowledge import get_knowledge_repository":
        "from sprintcycle.application.composition.di_bridge import get_knowledge_repository",
    
    # 治理适配器
    r"from sprintcycle\.domain\.ports\.governance import (get_archguard_adapter|get_grimp_adapter|get_import_linter_adapter|get_ruff_adapter|get_typecheck_adapter)":
        r"from sprintcycle.application.composition.di_bridge import \1",
    
    # create_* 工厂函数
    r"from sprintcycle\.domain\.ports\.(config|registry|evolution) import (create_\w+)":
        r"from sprintcycle.application.composition.di_bridge import \2",
}

def update_file(file_path: Path) -> bool:
    """更新单个文件的导入语句"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # 应用所有替换规则
        for pattern, replacement in SPECIFIC_IMPORTS.items():
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """批量更新所有 Python 文件"""
    base_path = Path("/Users/liangzai/CursorProjects/sprintcycle/sprintcycle")
    updated_files = []
    
    # 遍历所有 Python 文件
    for py_file in base_path.rglob("*.py"):
        # 跳过 __pycache__ 和 .pyc 文件
        if "__pycache__" in str(py_file) or py_file.suffix == ".pyc":
            continue
        
        if update_file(py_file):
            updated_files.append(py_file)
            print(f"✅ Updated: {py_file.relative_to(base_path)}")
    
    print(f"\n总计更新了 {len(updated_files)} 个文件")
    
    # 列出未更新的文件
    print("\n未更新的文件（可能不需要更新或已更新）：")
    for pattern_name, _ in list(SPECIFIC_IMPORTS.items())[:5]:
        remaining = list(base_path.rglob("*.py"))
        print(f"  - {pattern_name}")

if __name__ == "__main__":
    main()
