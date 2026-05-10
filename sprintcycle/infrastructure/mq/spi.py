"""
消息队列 SPI（可插拔 backend）

与 ``sprintcycle.execution.events.ExecutionEventBackend`` 解耦：后者负责执行期领域事件（``Event``），
本模块提供通用 ``topic + payload`` 队列契约，便于接入 SQLite / Redis / Kafka 等后端。

SQLite 后端见 ``SQLiteMQ``；需要把执行事件送 MQ 时可另写适配器将 ``Event`` 序列化后 ``publish``。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict

__all__ = ["MQHandler", "MQMessage", "MessageQueue"]


@dataclass(frozen=True, slots=True)
class MQMessage:
    """投递给订阅方的单条消息。"""

    id: str
    topic: str
    payload: Dict[str, Any]


MQHandler = Callable[[MQMessage], Any]


class MessageQueue(ABC):
    """消息队列抽象（SPI）：发布、订阅确认（ack）。"""

    @abstractmethod
    def publish(self, topic: str, payload: dict) -> str:
        """投递消息并返回服务端消息 ``id``。"""

    @abstractmethod
    def subscribe(self, topic: str, handler: MQHandler) -> None:
        """按 ``topic`` 注册处理器；语义由具体后端定义（SQLite 实现在 ``publish`` 时同步派发）。"""

    @abstractmethod
    def unsubscribe(self, topic: str, handler: MQHandler) -> None:
        """移除先前 ``subscribe`` 注册的 ``handler``（同一对象引用）。"""

    @abstractmethod
    def ack(self, message_id: str) -> None:
        """确认消息已处理；具体持久化语义由后端实现。"""
