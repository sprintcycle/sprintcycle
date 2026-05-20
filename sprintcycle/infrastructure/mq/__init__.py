"""
可插拔消息队列（MQ SPI + 实现）

- **SPI**：``MessageQueue`` / ``MQMessage``（``spi``）
- **首选本地实现**：``SQLiteMQ`` — 单实例、零外部依赖，见 ``sqlite_mq``

执行期领域事件默认经 ``sprintcycle.execution.sqlite_event_backend.SQLiteMQEventBackend`` 桥接到本层
``SQLiteMQ``；亦可在此层直接 ``publish`` / ``subscribe`` 做通用 topic。纯内存测试可换 ``EventBus``。
"""

from .spi import MessageQueue, MQHandler, MQMessage
from .sqlite_mq import SQLiteMQ

__all__ = ["MQHandler", "MQMessage", "MessageQueue", "SQLiteMQ"]
