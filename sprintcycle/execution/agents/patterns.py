"""
Root Cause Patterns for Bug Analysis

Error pattern database used by BugAnalyzerAgent.
"""

from typing import Dict, Any
from ...exceptions import Severity

ROOT_CAUSE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "NameError": {
        "patterns": [r"name .+ is not defined"],
        "causes": ["变量未定义", "变量名拼写错误", "缺少 import"],
        "fixes": ["确保变量在使用前已定义", "检查变量名拼写", "添加缺失的 import"],
        "severity": Severity.MEDIUM,
    },
    "TypeError": {
        "patterns": [r"unsupported operand", r"NoneType"],
        "causes": ["类型不匹配", "空值未处理"],
        "fixes": ["添加类型检查", "处理 None 情况"],
        "severity": Severity.MEDIUM,
    },
    "ImportError": {
        "patterns": [r"No module named", r"cannot import name"],
        "causes": ["依赖未安装", "模块路径错误"],
        "fixes": ["pip install", "检查 import 路径"],
        "severity": Severity.HIGH,
    },
    "AttributeError": {
        "patterns": [r"has no attribute"],
        "causes": ["对象没有该属性", "属性名拼写错误"],
        "fixes": ["检查属性名", "使用 hasattr", "使用 getattr"],
        "severity": Severity.MEDIUM,
    },
    "IndexError": {
        "patterns": [r"index out of range"],
        "causes": ["索引越界"],
        "fixes": ["检查序列长度", "使用 try-except"],
        "severity": Severity.MEDIUM,
    },
    "KeyError": {
        "patterns": [r"KeyError"],
        "causes": ["字典键不存在"],
        "fixes": ["使用 dict.get()", "检查键存在"],
        "severity": Severity.LOW,
    },
    "FileNotFoundError": {
        "patterns": [r"No such file or directory"],
        "causes": ["文件不存在", "路径错误"],
        "fixes": ["检查文件路径", "使用 Path 检查"],
        "severity": Severity.HIGH,
    },
    "SyntaxError": {
        "patterns": [r"invalid syntax"],
        "causes": ["语法错误", "括号不匹配"],
        "fixes": ["检查语法", "检查缩进"],
        "severity": Severity.CRITICAL,
    },
    "IndentationError": {
        "patterns": [r"unexpected indent", r"expected an indented block"],
        "causes": ["缩进不一致", "混用空格和 Tab"],
        "fixes": ["统一缩进", "配置编辑器"],
        "severity": Severity.CRITICAL,
    },
    "ValueError": {
        "patterns": [r"invalid literal for int", r"could not convert"],
        "causes": ["值转换失败", "参数值不符合预期"],
        "fixes": ["验证输入", "使用 try-except"],
        "severity": Severity.MEDIUM,
    },
    "ZeroDivisionError": {
        "patterns": [r"division by zero"],
        "causes": ["除数为零"],
        "fixes": ["检查除数", "使用 if denominator != 0"],
        "severity": Severity.MEDIUM,
    },
    "PermissionError": {
        "patterns": [r"Permission denied"],
        "causes": ["没有权限"],
        "fixes": ["检查权限", "使用 sudo"],
        "severity": Severity.HIGH,
    },
    "MemoryError": {
        "patterns": [r"out of memory"],
        "causes": ["内存不足", "加载过大文件"],
        "fixes": ["优化内存", "使用生成器"],
        "severity": Severity.CRITICAL,
    },
    "RecursionError": {
        "patterns": [r"maximum recursion depth"],
        "causes": ["递归过深", "没有终止条件"],
        "fixes": ["检查终止条件", "改用迭代"],
        "severity": Severity.HIGH,
    },
}
