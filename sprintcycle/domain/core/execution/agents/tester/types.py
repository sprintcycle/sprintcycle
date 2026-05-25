"""Tester Agent 数据类型。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class TestType(Enum):
    """测试类型枚举"""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestResult(Enum):
    """测试结果枚举"""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class TestCase:
    """测试用例"""

    name: str
    type: str = "unit"
    input: Dict[str, Any] = field(default_factory=dict)
    expected: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "input": self.input,
            "expected": self.expected,
            "priority": self.priority,
        }


__all__ = ["TestCase", "TestType", "TestResult"]
