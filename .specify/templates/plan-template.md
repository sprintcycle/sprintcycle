# Implementation Plan: [FEATURE]（实现计划：[FEATURE]）

**Branch**: `[###-feature-name]`（分支：[###-feature-name]） | **Date**: [DATE]（日期：[DATE]） | **Spec**: [link]（规格文档：[link]）

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`（输入：来自 `/specs/[###-feature-name]/spec.md` 的功能规格）

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.（注意：此模板由 `/speckit-plan` 命令填写。有关执行流程，请参见 `.specify/templates/plan-template.md`。）

## Summary（摘要）

[Extract from feature spec: primary requirement + technical approach from research]（[从功能规格中提取：主要需求 + 来自调研的技术方案]）

## Technical Context（技术上下文）

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->
<!--
  需要处理：请将本节内容替换为项目的技术细节。
  该结构仅作为建议，用于指导迭代过程。
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]（**语言/版本**：[例如，Python 3.11、Swift 5.9、Rust 1.75 或 需要澄清]）

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]（**主要依赖**：[例如，FastAPI、UIKit、LLVM 或 需要澄清]）

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]（**存储**：[如适用，例如 PostgreSQL、CoreData、文件或不适用]）

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]（**测试**：[例如，pytest、XCTest、cargo test 或 需要澄清]）

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]（**目标平台**：[例如，Linux 服务器、iOS 15+、WASM 或 需要澄清]）

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]（**项目类型**：[例如，库/CLI/Web 服务/移动应用/编译器/桌面应用 或 需要澄清]）

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]（**性能目标**：[领域相关，例如 1000 req/s、10k 行/秒、60 fps 或 需要澄清]）

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]（**约束**：[领域相关，例如 p95 <200ms、内存 <100MB、支持离线 或 需要澄清]）

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]（**规模/范围**：[领域相关，例如 1 万用户、100 万行代码、50 个界面或 需要澄清]）

## Constitution Check（宪法检查）

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*（*门禁：必须在阶段 0 调研之前通过，并在阶段 1 设计后复查。*）

[Gates determined based on constitution file]（[门禁依据宪法文件确定]）

## Project Structure（项目结构）

### Documentation (this feature)（文档（本功能））

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)（本文件（/speckit-plan 命令输出））
├── research.md          # Phase 0 output (/speckit-plan command)（阶段 0 输出（/speckit-plan 命令））
├── data-model.md        # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
├── quickstart.md        # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
├── contracts/           # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)（阶段 2 输出（/speckit-tasks 命令 - 不由 /speckit-plan 创建））
```

### Source Code (repository root)（源代码（仓库根目录））
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
<!--
  需要处理：请将下方占位树替换为本功能的真实目录结构。
  删除未使用的选项，并用真实路径扩展所选结构（例如 apps/admin、packages/something）。交付的计划中不得保留 Option 标签。
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]（**结构决策**：[记录所选结构，并引用上面捕获的真实目录]）

## Complexity Tracking（复杂度追踪）

> **Fill ONLY if Constitution Check has violations that must be justified**（*仅当宪法检查存在必须说明理由的违规项时填写*）

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
