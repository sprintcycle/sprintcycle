# 敏感信息扫描报告

## 扫描时间
2026-03-13

## 扫描范围
- 待提交文件: CHANGELOG.md, config/prd_split_strategy.yaml, sprintcycle/__init__.py, utils/logger.py, videos/record_demo.py
- 新增文件: sprintcycle/benchmark.py, sprintcycle/config.py, sprintcycle/error_handlers.py, sprintcycle/exceptions.py, sprintcycle/resource_monitor.py, sprintcycle/scheduler.py, sprintcycle/sprint_logger.py, sprintcycle/state_manager.py, sprintcycle/states/, tests/

## 扫描结果

| 类型 | 正则模式 | 发现数量 | 风险等级 | 状态 |
|------|---------|---------|---------|------|
| API Key (sk-xxx) | `sk-[a-zA-Z0-9]{32,}` | 1 | P0-致命 | ✅ 已治理 |
| API Key (其他) | `(api_key\|apikey\|api-key)\s*[=:]\s*['\"][^'\"]+['\"]` | 0 | P0-致命 | ✅ 通过 |
| 密码 | `password\s*[=:]\s*['\"][^'\"]+['\"]` | 0 | P0-致命 | ✅ 通过 |
| Token | `(token\|access_token)\s*[=:]\s*['\"][^'\"]+['\"]` | 0 | P0-致命 | ✅ 通过 |
| 密钥 | `(secret\|private_key)\s*[=:]\s*['\"]+['\"]` | 0 | P0-致命 | ✅ 通过 |
| 数据库连接 | `mysql://[^@]+:[^@]+@` | 0 | P1-高危 | ✅ 通过 |
| 邮箱地址 | 真实邮箱 | 0 | P2-中危 | ✅ 通过 |
| 手机号 | 1[3-9]\d{9} | 0 | P2-中危 | ✅ 通过 |
| 内网 IP | 192.168.x.x, 10.x.x.x | 0 | P3-低危 | ✅ 通过 |
| 个人路径 | /home/\|/Users/ | 0 | P3-低危 | ✅ 通过 |

## 发现详情

### P0-致命 (1项)

1. **文件**: `config.yaml`
   - **位置**: autofix 配置节
   - **问题**: `api_key: "sk-4191b41ff2704249bca62aba47754199"`
   - **治理**: 替换为 `${LLM_API_KEY}` 环境变量引用

## 结论
✅ **扫描通过** - 已完成所有敏感信息治理
