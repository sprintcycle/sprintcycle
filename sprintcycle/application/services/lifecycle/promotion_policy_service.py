"""Promotion Policy 应用层服务 - 封装 domain 层的 PromotionPolicy。"""

from __future__ import annotations

from typing import Any, Dict

from sprintcycle.domain.core.governance.promotion_policy import PromotionPolicy


class PromotionPolicyService:
    """PromotionPolicy 的应用层包装服务。"""

    def __init__(self):
        self._policy = PromotionPolicy()

    @property
    def policy(self) -> PromotionPolicy:
        """获取底层 PromotionPolicy 实例。"""
        return self._policy

    def evaluate(self, execution_id: str, **kwargs) -> Any:
        """评估晋升策略。"""
        return self._policy.evaluate(execution_id, **kwargs)

    def promote(self, execution_id: str, **kwargs) -> Any:
        """执行晋升。"""
        return self._policy.promote(execution_id, **kwargs)

    def can_promote(self, execution_id: str) -> bool:
        """检查是否可以晋升。"""
        return self._policy.can_promote(execution_id)

    def get_promotion_status(self, execution_id: str) -> Dict[str, Any]:
        """获取晋升状态。"""
        return self._policy.get_promotion_status(execution_id)
