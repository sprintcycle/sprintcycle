# SprintCycle 架构精简 - PRD 需求文档

**版本：** v1.0  
**日期：** 2026-05-31  
**类型：** 架构优化/代码清理

---

## 一、问题描述

SprintCycle 项目存在以下架构问题：

1. **废弃模块堆积**：
   - `di_bridge.py` - 已标记废弃的向后兼容层
   - `http_factory.py` - 空壳工厂，仅包装 di_container
   - HITL 模块兼容层（context.py、config.py、utils.py）- 仅重新导出，无实际逻辑

2. **自定义 DI 容器过度设计**：
   - 431 行自定义容器代码
   - 项目已依赖 `dependency-injector>=4.40.0` 但未充分利用
   - 多层抽象增加维护成本

---

## 二、影响范围

### 2.1 后端模块

| 文件路径 | 变更类型 | 说明 |
|---------|----------|------|
| `sprintcycle/application/composition/di_bridge.py` | 删除 | 废弃模块 |
| `sprintcycle/application/composition/http_factory.py` | 删除/简化 | 空壳工厂 |
| `sprintcycle/application/composition/__init__.py` | 修改 | 更新导出 |
| `sprintcycle/domain/core/governance/hitl/context.py` | 删除 | 兼容层 |
| `sprintcycle/domain/core/governance/hitl/config.py` | 删除 | 兼容层 |
| `sprintcycle/domain/core/governance/hitl/utils.py` | 删除 | 兼容层 |
| `sprintcycle/domain/core/governance/hitl/__init__.py` | 修改 | 更新导入 |
| `sprintcycle/application/composition/di_container.py` | 重构 | 替换为 dependency-injector |

### 2.2 前端模块

无影响，无需修改。

### 2.3 外部依赖

无外部依赖影响。

---

## 三、风险评估

| 风险点 | 风险等级 | 缓解措施 |
|--------|----------|----------|
| 示例代码失效 | 🟡 中 | 更新示例代码使用新路径 |
| 文档过期 | 🟡 中 | 同步更新相关文档 |
| 依赖注入变更引入 bug | 🟡 中 | 充分测试，保留测试覆盖 |

---

## 四、业务目标

1. **降低维护成本**：减少 500+ 行废弃和过度设计的代码
2. **简化架构理解**：新人上手周期从 2-4 周降低到 1-2 周
3. **利用现有依赖**：充分利用已安装的 `dependency-injector` 库
4. **保持业务逻辑**：100% 保留现有功能

---

## 五、用户价值

| 用户角色 | 价值 |
|---------|------|
| 开发者 | 更少的概念需要理解，更快定位问题 |
| 维护者 | 更少的代码需要维护，降低 bug 风险 |
| 新人 | 更简单的架构，更快上手 |

---

## 六、非功能性需求

1. **可维护性**：代码结构更简洁，易于理解
2. **兼容性**：核心 API 保持不变（container 等）
3. **测试覆盖**：所有相关测试必须通过
4. **性能**：无性能退化

---

## 七、验收标准

- [ ] 所有废弃模块已删除
- [ ] DI 容器已替换为 dependency-injector
- [ ] 所有测试通过
- [ ] 文档同步更新
- [ ] 业务逻辑 100% 保留
