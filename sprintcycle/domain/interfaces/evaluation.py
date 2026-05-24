"""
Evaluation Interfaces - Domain Layer

定义评估相关的协议接口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class EvaluatorAgentProtocol(ABC):
    """评估器代理协议"""

    @abstractmethod
    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行评估

        Args:
            payload: 评估输入数据

        Returns:
            评估结果字典
        """
        ...


__all__ = [
    "EvaluatorAgentProtocol",
]
