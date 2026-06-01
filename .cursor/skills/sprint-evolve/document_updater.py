#!/usr/bin/env python3
"""文档自动更新器 - 根据代码实现自动更新文档"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from loguru import logger


@dataclass
class DocumentUpdate:
    """文档更新内容"""
    file_path: Path
    section: str
    old_content: str
    new_content: str
    change_type: str  # add/update/remove


class DocumentUpdater:
    """文档自动更新器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.updated_files = []
    
    def update_all_documents(self) -> List[DocumentUpdate]:
        """更新所有文档"""
        logger.info("📄 开始自动更新文档...")
        
        updates = []
        
        # 更新 README.md
        readme_updates = self._update_readme()
        updates.extend(readme_updates)
        
        # 更新 README_EN.md
        readme_en_updates = self._update_readme_en()
        updates.extend(readme_en_updates)
        
        # 更新 ARCHITECTURE_INVARIANTS.md
        arch_updates = self._update_architecture_invariants()
        updates.extend(arch_updates)
        
        # 更新 sprintcycle-architecture-orchestration.mdc
        orchestration_updates = self._update_architecture_orchestration()
        updates.extend(orchestration_updates)
        
        logger.info(f"✅ 文档更新完成，共更新 {len(updates)} 处")
        return updates
    
    def _update_readme(self) -> List[DocumentUpdate]:
        """更新 README.md"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return []
        
        content = readme_path.read_text()
        updates = []
        
        # 更新架构概述
        arch_summary = self._generate_architecture_summary()
        old_section = self._find_section(content, "## 架构概述")
        if old_section:
            updates.append(DocumentUpdate(
                file_path=readme_path,
                section="架构概述",
                old_content=old_section,
                new_content=arch_summary,
                change_type="update"
            ))
        
        # 更新端口数量
        port_count = self._count_ports(include_init=False)
        content = self._replace_port_count(content, port_count)
        readme_path.write_text(content)
        
        return updates
    
    def _update_readme_en(self) -> List[DocumentUpdate]:
        """更新 README_EN.md"""
        readme_en_path = self.project_root / "README_EN.md"
        if not readme_en_path.exists():
            return []
        
        content = readme_en_path.read_text()
        
        # 同步端口数量
        port_count = self._count_ports(include_init=False)
        content = self._replace_port_count_en(content, port_count)
        readme_en_path.write_text(content)
        
        return []
    
    def _update_architecture_invariants(self) -> List[DocumentUpdate]:
        """更新 ARCHITECTURE_INVARIANTS.md"""
        arch_path = self.project_root / "docs" / "ARCHITECTURE_INVARIANTS.md"
        if not arch_path.exists():
            return []
        
        content = arch_path.read_text()
        
        # 更新端口定义
        ports_section = self._generate_ports_section()
        content = self._replace_section(content, "### 端口定义", ports_section)
        arch_path.write_text(content)
        
        return []
    
    def _update_architecture_orchestration(self) -> List[DocumentUpdate]:
        """更新 sprintcycle-architecture-orchestration.mdc"""
        orchestration_path = self.project_root / ".cursor" / "rules" / "sprintcycle-architecture-orchestration.mdc"
        if not orchestration_path.exists():
            return []
        
        content = orchestration_path.read_text()
        updates = []
        
        # 更新端口数量
        port_count = self._count_ports(include_init=False)
        old_content = content
        content = self._replace_port_count_in_orchestration(content, port_count)
        
        # 更新端口列表
        ports_section = self._generate_ports_list_for_orchestration()
        content = self._replace_ports_section_in_orchestration(content, ports_section)
        
        if content != old_content:
            orchestration_path.write_text(content)
            updates.append(DocumentUpdate(
                file_path=orchestration_path,
                section="架构编排规则",
                old_content=old_content[:200] + "...",  # 只保存开头部分用于记录
                new_content=content[:200] + "...",
                change_type="update"
            ))
        
        return updates
    
    def _generate_architecture_summary(self) -> str:
        """生成架构概述"""
        return """## 架构概述

SprintCycle 采用 DDD（领域驱动设计）+ 六边形架构模式，核心特点：

- **领域层纯粹性**：领域层不依赖任何外部框架
- **聚合根不可变性**：使用 `@dataclass(frozen=True)` 确保不可变性
- **Port/Adapter 模式**：端口定义与适配器实现分离
- **组合根模式**：依赖注入容器作为单一入口

### 架构层次

```
┌─────────────────────────────────────────┐
│              interfaces (接口层)          │
│  - HTTP API / GraphQL / CLI / WebSocket │
├─────────────────────────────────────────┤
│              application (应用层)         │
│  - 服务层 / DTO / 组合根 / 业务编排      │
├─────────────────────────────────────────┤
│                domain (领域层)            │
│  - 聚合根 / 值对象 / 领域服务 / 端口定义   │
├─────────────────────────────────────────┤
│           infrastructure (基础设施层)      │
│  - 数据库 / 外部 API / 适配器实现        │
└─────────────────────────────────────────┘
```

### 核心聚合根

| 聚合根 | 说明 |
|--------|------|
| LifecycleContract | 生命周期契约，核心状态机 |
| SprintDefinition | Sprint 定义 |
| ReleasePlan | 发布计划 |
| GovernancePolicy | 治理策略 |

### 端口数量

当前系统包含 **{} 个端口定义**，涵盖：
- 配置端口
- 治理端口  
- 集成端口
- 可观测性端口
- 存储端口""".format(self._count_ports())
    
    def _count_ports(self, include_init: bool = False) -> int:
        """统计端口数量"""
        ports_dir = self.project_root / "sprintcycle" / "domain" / "ports"
        if not ports_dir.exists():
            return 0
        
        port_files = list(ports_dir.rglob("*.py"))
        if not include_init:
            port_files = [f for f in port_files if f.name != "__init__.py"]
        return len(port_files)
    
    def _find_section(self, content: str, section_title: str) -> Optional[str]:
        """查找文档中的章节"""
        lines = content.split("\n")
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if line.startswith(section_title):
                start_idx = i
            elif start_idx is not None and line.startswith("## "):
                end_idx = i
                break
        
        if start_idx is not None:
            if end_idx is not None:
                return "\n".join(lines[start_idx:end_idx])
            return "\n".join(lines[start_idx:])
        return None
    
    def _replace_section(self, content: str, section_title: str, new_content: str) -> str:
        """替换文档中的章节"""
        lines = content.split("\n")
        result_lines = []
        in_section = False
        skip_until_next_section = False
        
        for line in lines:
            if line.startswith(f"### {section_title}"):
                result_lines.append(f"### {section_title}")
                result_lines.append("")
                result_lines.append(new_content)
                skip_until_next_section = True
                in_section = True
            elif skip_until_next_section and line.startswith("### "):
                result_lines.append("")
                result_lines.append(line)
                skip_until_next_section = False
                in_section = False
            elif not skip_until_next_section:
                result_lines.append(line)
        
        return "\n".join(result_lines)
    
    def _replace_port_count(self, content: str, count: int) -> str:
        """替换中文文档中的端口数量"""
        import re
        return re.sub(r"端口数量.*?(\d+)", f"端口数量：{count}", content)
    
    def _replace_port_count_en(self, content: str, count: int) -> str:
        """替换英文文档中的端口数量"""
        import re
        return re.sub(r"port count.*?(\d+)", f"port count: {count}", content, flags=re.IGNORECASE)
    
    def _replace_port_count_in_orchestration(self, content: str, count: int) -> str:
        """替换 orchestration 文件中的端口数量"""
        import re
        # 替换中文部分
        content = re.sub(r"(\d+)\s*个端口", f"{count} 个端口", content)
        # 替换英文部分
        content = re.sub(r"(\d+)\s*ports?", f"{count} ports", content, flags=re.IGNORECASE)
        return content
    
    def _generate_ports_list_for_orchestration(self) -> str:
        """为 orchestration 文件生成端口列表"""
        ports_dir = self.project_root / "sprintcycle" / "domain" / "ports"
        if not ports_dir.exists():
            return ""
        
        port_files = sorted(ports_dir.rglob("*.py"))
        port_info = []
        
        for port_file in port_files:
            if port_file.name == "__init__.py":
                continue
            module_name = port_file.stem
            port_info.append(f"  - `{port_file.name}`")
        
        return "\n".join(port_info)
    
    def _replace_ports_section_in_orchestration(self, content: str, new_ports: str) -> str:
        """替换 orchestration 文件中的端口数量部分，但保留原有的详细说明"""
        import re
        
        # 只更新端口数量，不替换详细的端口列表
        # 查找并替换中文部分的端口数量
        port_count = self._count_ports(include_init=False)
        
        # 替换中文部分的端口数量（先修复可能的双括号问题）
        content = re.sub(r"（\d+ 个端口[）]*", f"（{port_count} 个端口）", content)
        
        # 替换英文部分的端口数量
        content = re.sub(r"\(\d+ ports\)", f"({port_count} ports)", content)
        
        return content
    
    def _generate_ports_section(self) -> str:
        """生成端口定义章节"""
        ports_dir = self.project_root / "sprintcycle" / "domain" / "ports"
        if not ports_dir.exists():
            return ""
        
        port_files = sorted(ports_dir.rglob("*.py"))
        port_info = []
        
        for port_file in port_files:
            module_name = port_file.stem.replace("_port", "")
            port_info.append(f"- **{module_name}**: {port_file.name}")
        
        return "\n".join(port_info)


def main():
    """命令行入口"""
    updater = DocumentUpdater()
    updates = updater.update_all_documents()
    
    print("===== 文档自动更新 =====")
    print(f"更新文件数: {len(updates)}")
    for update in updates:
        print(f"- {update.file_path.name}: {update.section} ({update.change_type})")
    print("===== 更新完成 =====")


if __name__ == "__main__":
    main()