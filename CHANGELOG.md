# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-04-28

### Added
- **统一状态管理** (`state_manager.py`)
  - StateManager 单例模式
  - StateScope 状态作用域 (GLOBAL/SPRINT/TASK/AGENT/RESOURCE)
  - StateEvent 状态变更事件
  - EventBus 事件总线
  - 状态历史记录和快照
  - 线程安全实现

- **并发执行支持** (`scheduler.py`)
  - SprintScheduler 并发调度器
  - Task 任务模型
  - DependencyGraph 依赖图管理
  - ResourcePool 资源池
  - 拓扑排序执行
  - 循环依赖检测
  - 支持 max_concurrency 配置

- **性能基准测试** (`benchmark.py`)
  - BenchmarkSuite 基准测试套件
  - BenchmarkResult 测试结果
  - PerformanceMonitor 性能监控
  - 回归检测机制
  - 统计报告生成

- **资源监控** (`resource_monitor.py`)
  - ResourceMonitor 资源监控器
  - ResourceSnapshot 资源快照
  - Alert/AlertLevel 告警机制
  - CPU/内存/磁盘/网络监控
  - 后台线程采集

- **状态模块** (`states/`)
  - sprint_state.py - Sprint 状态
  - task_state.py - Task 状态
  - agent_state.py - Agent 状态

### Changed
- 更新 `__init__.py` 导出新模块
- 测试用例增加 31 个新测试
- 测试覆盖率提升至 91%

### Fixed
- BUG-001: 修复 `__init__.py` 导入错误
- BUG-002: 修复 StateManager.watch 回调签名
- BUG-003: 修复 DependencyGraph 拓扑排序

## [0.3.0] - 2026-04-28

### Added
- **错误处理增强** (`exceptions.py`)
  - 16 种异常类型完整体系
  - 智能错误分类 (Timeout/Configuration/Permission/Network 等)
  - 错误恢复建议
  - @retry_on_error 装饰器
  - @handle_errors 装饰器
  - safe_execute 安全执行函数

- **日志系统完善** (`sprint_logger.py`, `utils/logger.py`)
  - SprintLogger Sprint 专用日志
  - 结构化 JSON 日志输出
  - 日志轮转 (RotatingFileHandler)
  - 上下文信息 (任务ID/Sprint)
  - 性能日志追踪
  - 终端颜色输出

- **配置管理优化** (`config.py`)
  - SprintCycleConfig 类型安全配置类
  - ToolConfig/SchedulerConfig/ReviewConfig/PlaywrightConfig
  - 环境变量覆盖
  - 配置验证机制
  - 热更新 reload()
  - 全局配置管理

- **测试覆盖提升**
  - test_config.py (14 tests)
  - test_error_handlers.py (20 tests)
  - test_sprint_logger.py (18 tests)
  - 整体覆盖率提升至 ~90%

### Changed
- 优化了 chorus.py 错误处理
- 优化了 sprint_chain.py 配置管理
- 完善了 __init__.py 模块导出
- 更新了 README.md 文档

### Fixed
- BUG-001: 配置文件验证缺失
- BUG-002: 错误归因不准确
- BUG-003: Sprint 日志未保存
- BUG-004: 测试文件导入错误
- BUG-005: 断言条件不准确

## [0.2.0] - 2026-04-27

### Added
- OpenClaw Skill 集成
- 18 MCP 工具对齐
- Web Dashboard
- Playwright 视频录制
- 环境变量通用化 (LLM_API_KEY)

### Changed
- 优化了 Agent 协作流程
- 完善了知识库沉淀机制
- 改进了 UI 验证功能

## [0.1.0] - 2026-04-25

### Added
- SprintChain 执行链
- 6 Agent 协作 (CODER/REVIEWER/ARCHITECT/TESTER/DIAGNOSTIC/UI_VERIFY)
- 知识库系统
- 自进化框架骨架
- 基础错误处理

---

## 版本说明

- **Breaking Changes**: 主版本号更新
- **New Features**: 次版本号更新
- **Bug Fixes**: Patch 版本号更新

## 迁移指南

### v0.3.0 → v0.4.0

1. **新增依赖**
   ```bash
   pip install psutil>=5.9.0
   ```

2. **导入变更**
   ```python
   # 可选导入新模块
   from sprintcycle import get_state_manager, StateScope
   from sprintcycle import SprintScheduler
   from sprintcycle import get_resource_monitor
   from sprintcycle import get_benchmark_suite
   ```

3. **API 兼容**
   - 所有 v0.3.0 API 完全兼容
   - 新增功能可选使用

### v0.2.0 → v0.3.0

1. **配置更新**
   ```yaml
   # config.yaml 新增字段
   logging:
     level: INFO
     file: ./logs/sprint.log
     structured: false
   ```

2. **导入变更**
   ```python
   # 新增导入
   from sprintcycle.config import SprintCycleConfig
   from sprintcycle.error_handlers import ErrorHandler
   from sprintcycle.sprint_logger import SprintLogger
   ```

3. **API 变更**
   - Chorus 初始化参数类型变化
   - 异常类新增子类

### v0.1.0 → v0.2.0

1. **环境变量**
   - 使用 LLM_API_KEY 替代原来的 API_KEY

2. **工具配置**
   - 新增 aider 配置格式
