# SprintCycle 产品与技术方案 V4.0 — 仓库内真理源

## 1. 与附件的关系

- **附件**：《3.1 SprintCycle 产品与技术完整方案 V4.0》（例如有道云笔记导出 `.mhtml`）可作为背景材料与评审输入。
- **对外唯一真理源（canonical）**：以本仓库内下列文件为准，与 **`main` 分支当前实现**一致；附件与下文冲突时，**以下位为准**。
  1. **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`** — 全文修订版（含 G1–G4、六 Phase、改造路线图 §6）。
  2. **本文件** — 入口与声明，避免散落链接歧义。

## 2. 产品一句与入口

- **定位**：PRD / 意图驱动的自我进化敏捷开发框架（非「已交付全栈平台」过度承诺）。
- **六大 API**：`plan` / `run` / `diagnose` / `status` / `rollback` / `stop`（`sprintcycle.api.SprintCycle`）。
- **三入口**：CLI、`MCP`（stdio + SSE）、Dashboard Web UI。

## 3. 主执行路径（必须写进架构评审）

```
SprintCycle.run / resume
    → TaskDispatcher.execute_prd（及 resume 路径）
        → SprintExecutor.execute_sprints（唯一 Sprint 编排循环）
```

- **`EvolutionPipeline`**：进化实验、诊断派生 PRD 等场景使用；**不与** `TaskDispatcher` 并列称为第二套「唯一生产编排」。

## 4. 质量门禁（G1–G4）

与 `L0–L3` 档位映射见 `sprintcycle/config/quality.py` 及 **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`** §2.3。`RuntimeConfig.quality_profile`（`off` / `fast` / `default` / `strict`）与 `quality_level` 的解析见 `effective_quality_level()`（§6.3）。G4：**import-linter**（`pyproject.toml` `[tool.importlinter]`）由 CI job **`architecture-gate`** 强制执行；**Hypothesis** 属性测试见 `tests/test_g4_properties.py`（§6.4）；突变测试见 `.github/workflows/mutation.yml`（§6.5）；可选 **Semgrep** 见 `.github/workflows/semgrep.yml`（§6.4）。

## 5. 部署脚本与仓库事实

- 本地开发脚本若放在 **未纳入版本库的 `docs-dev/`**，文档中不得写死不存在的 `main/.../dev-setup.sh` URL；以 **README 与 Release 中实际给出的 raw 路径** 为准（见 **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`** §5.1）。

---

## English (summary)

In-repo **canonical** product/tech spec for V4.0 alignment: **`SPRINTCYCLE_PRODUCT_TECH_PLAN.md`** plus this file. External note exports are **inputs only**. **Primary execution path** is `SprintCycle` → `TaskDispatcher` → `SprintExecutor.execute_sprints`; `EvolutionPipeline` is for evolution/diagnostic flows, not a parallel “only” orchestrator. **G4**: CI **`architecture-gate`** (`lint-imports`), Hypothesis tests in `tests/test_g4_properties.py`, optional Semgrep workflow.
