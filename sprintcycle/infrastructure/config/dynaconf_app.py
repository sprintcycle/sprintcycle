"""Dynaconf 单例工厂：多源合并、环境变量、dotenv；不做类型校验。"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from dynaconf import Dynaconf

# Dashboard / CLI 可写入的运行时覆盖层（在 sprintcycle.toml 之后、环境变量之前合并）
RUNTIME_YAML_NAME = "sprintcycle.runtime.yaml"


def build_dynaconf(
    project_path: str | Path | None,
    *,
    extra_files: Sequence[str | Path] | None = None,
) -> Dynaconf:
    """
    构建 Dynaconf 实例。

    ``settings_files`` 顺序为：项目 ``sprintcycle.toml``（若存在）→ ``sprintcycle.runtime.yaml``（若存在）
    → ``extra_files``。
    环境变量 ``SPRINTCYCLE_*`` 与 dotenv 在文件之后合并，**环境覆盖文件**。

    ``project_path`` 为 ``None`` 时仅加载 dotenv + 环境变量（不绑定项目 TOML）。
    """
    files: list[str] = []
    if project_path is not None:
        root = Path(project_path).resolve()
        toml = root / "sprintcycle.toml"
        if toml.is_file():
            files.append(str(toml))
        runtime_yaml = root / RUNTIME_YAML_NAME
        if runtime_yaml.is_file():
            files.append(str(runtime_yaml))
    if extra_files:
        for p in extra_files:
            pp = Path(p)
            if pp.is_file():
                files.append(str(pp))
    return Dynaconf(
        envvar_prefix="SPRINTCYCLE",
        settings_files=files,
        load_dotenv=True,
        merge_enabled=True,
    )
