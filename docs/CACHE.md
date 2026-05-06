# 执行缓存配置与切换

SprintCycle 使用统一 **`ExecutionCache`**（底层 **`CacheBackend`**），在 **`SprintCycle(project_path, …)`** 构造时根据 **`RuntimeConfig`** 选择实现并写入全局实例（`get_cache()`）。

## 可选后端

| `cache_backend` | 说明 | 依赖 |
|-----------------|------|------|
| `diskcache`（默认） | 本地目录 + SQLite，LRU | 已随主包 `diskcache` |
| `redis` | 多进程/多实例共享 | `pip install -e ".[cache-redis]"` 或 `pip install redis` |
| （关闭） | `cache_enabled = false` 时使用空后端，不读写 | 无 |

`cache_backend = redis` 且未配置 **`cache_redis_url`** / 环境变量 **`REDIS_URL`** / **`SPRINTCYCLE_CACHE_REDIS_URL`** 时，会 **自动回退** 为 `diskcache` 并打 warning。

## 方式一：`sprintcycle.toml`（推荐）

项目根 **`sprintcycle.toml`** 中增加 **`[cache]`** 表（与 `flatten_sprintcycle_toml` 映射一致）：

| TOML 键 | 对应 `RuntimeConfig` 字段 | 说明 |
|---------|---------------------------|------|
| `enabled` | `cache_enabled` | `false` 关闭全部执行缓存 |
| `backend` | `cache_backend` | `diskcache` 或 `redis` |
| `dir` | `cache_dir` | 相对路径相对 **项目根**；绝对路径按原样使用 |
| `redis_url` 或 `url` | `cache_redis_url` | Redis 连接串 |
| `max_entries` | `cache_max_entries` | disk 后端 LRU 估算上限 |
| `default_ttl_hours` | `cache_default_ttl_hours` | `ExecutionCache.set` 默认 TTL（小时） |
| `llm_codegen` | `cache_llm_codegen` | 是否缓存 Coder 成功生成结果 |

示例：

```toml
[cache]
enabled = true
backend = "diskcache"
dir = ".sprintcycle/cache"
# backend = "redis"
# redis_url = "redis://localhost:6379/0"
# url = "redis://..."   # 与 redis_url 等价
llm_codegen = true
default_ttl_hours = 24
max_entries = 1000
```

修改后 **重新构造 `SprintCycle`** 或重启 CLI/MCP/Dashboard 进程即可生效。

## 方式二：环境变量（`SPRINTCYCLE_*`）

`RuntimeConfig` 使用 **`env_prefix="SPRINTCYCLE_"`**，布尔与字符串字段可直接覆盖 TOML：

| 环境变量 | 含义 |
|----------|------|
| `SPRINTCYCLE_CACHE_ENABLED` | `true` / `false` |
| `SPRINTCYCLE_CACHE_BACKEND` | `diskcache` / `redis` |
| `SPRINTCYCLE_CACHE_DIR` | 缓存目录 |
| `SPRINTCYCLE_CACHE_REDIS_URL` | Redis URL（可与 `REDIS_URL` 二选一；工厂内会读 `REDIS_URL`） |
| `SPRINTCYCLE_CACHE_MAX_ENTRIES` | 整数 |
| `SPRINTCYCLE_CACHE_DEFAULT_TTL_HOURS` | 整数 |
| `SPRINTCYCLE_CACHE_LLM_CODEGEN` | `true` / `false` |

与 `sprintcycle.toml` 的合并规则见 **`RuntimeConfig.from_project`**：先 TOML，再与环境合并（**环境覆盖文件**）。

## 方式三：代码内 `RuntimeConfig`

```python
from sprintcycle import SprintCycle
from sprintcycle.config import RuntimeConfig

cfg = RuntimeConfig(
    cache_backend="redis",
    cache_redis_url="redis://localhost:6379/0",
)
sc = SprintCycle(".", config=cfg)
```

## 程序化直接替换后端（高级）

不经过 `SprintCycle` 时，可注入自定义实例：

```python
from sprintcycle.execution.cache import ExecutionCache, set_cache
from sprintcycle.cache import DiskCacheBackend

set_cache(ExecutionCache(backend=DiskCacheBackend("/tmp/sc-cache", max_entries=100)))
```

## 使用位置（当前）

- **Coder**：成功生成（同一 engine + prompt）可走磁盘/Redis 缓存（受 `cache_llm_codegen` 控制）。
- **静态分析**：`which` 工具探测结果键 `tool_avail:*`，长 TTL。
- 其他模块可 **`from sprintcycle.execution import get_cache`** 读写同一全局实例。

更多实现细节见 **`sprintcycle/cache/`** 与 **`sprintcycle/execution/cache.py`**。
