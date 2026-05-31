"""
HTTP 层服务工厂 - 为 interfaces/http 提供基础设施初始化

使用 DI Container 进行初始化。
"""

from __future__ import annotations


def initialize_http_infrastructure(project_path: str) -> None:
    """初始化 HTTP 层所需的基础设施"""
    from sprintcycle.application.composition.di_container import create_container
    create_container(project_path=project_path)


class InfrastructureFactory:
    """基础设施工厂注册器 - 保持向后兼容的空壳。"""

    def __init__(self, project_path: str):
        self.project_path = project_path
