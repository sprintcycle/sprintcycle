# Implementation Plan: EvolutionActivator（自进化激活器实现计划）

**Branch**: `002-evolution-activator`（分支：`002-evolution-activator`） | **Date**: 2026-05-18（日期：2026-05-18） | **Spec**: `specs/20260518-143022-evolution-activator/spec.md`（规格：`specs/20260518-143022-evolution-activator/spec.md`）

**Input**: Feature specification from `/specs/20260518-143022-evolution-activator/spec.md`（输入：来自 `/specs/20260518-143022-evolution-activator/spec.md` 的功能规格）

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.（注意：此模板由 `/speckit-plan` 命令填写。有关执行流程，请参见 `.specify/templates/plan-template.md`。）

## Summary（摘要）

Create a dedicated `application/evolution/activator.py` entry point that safely activates the existing self-evolution capability, enforces activation guards, monitors runtime health, retries transient failures with bounded backoff, and transitions into a degraded state when the runtime is not healthy enough to continue. The activator remains an orchestration boundary only; it coordinates existing services, facades, hooks, registries, or orchestrators without embedding self-evolution business logic.（创建一个专用的 `application/evolution/activator.py` 入口，用于安全激活现有自进化能力，执行激活守卫，监控运行时健康状态，以有界退避重试瞬时失败，并在运行时不再足够健康时切换为降级态。该激活器仅作为编排边界存在；它协调现有 service、facade、hook、registry 或 orchestrator，而不嵌入自进化业务逻辑。）

## Technical Context（技术上下文）

**Language/Version**: Python 3.11+（语言/版本：Python 3.11 及以上）

**Primary Dependencies**: Existing SprintCycle application services, self-evolution runtime components, health-check collaborators, retry/backoff policy helpers, and existing orchestration/runtime adapters（主要依赖：现有 SprintCycle application services、自进化运行时组件、健康检查协作者、重试/退避策略辅助器以及现有编排/运行时适配器）

**Storage**: N/A for the activator itself; runtime state is tracked in-memory and exposed through existing lifecycle/state surfaces when needed（存储：激活器本身不需要持久化；运行时状态以内存方式跟踪，并在需要时通过现有生命周期/状态表面暴露）

**Testing**: pytest, async unit tests, mocked guard/health/retry collaborators（测试：pytest、异步单元测试、mock 的守卫/健康/重试协作者）

**Target Platform**: Backend application runtime and local developer workflows（目标平台：后端应用运行时和本地开发工作流）

**Project Type**: Python application orchestration component within SprintCycle（项目类型：SprintCycle 内的 Python 应用编排组件）

**Performance Goals**: Prevent duplicate active loop workers, keep startup path deterministic, and avoid unbounded retry loops（性能目标：避免重复活跃循环 worker、保持启动路径确定性、避免无限重试）

**Constraints**: Preserve layered boundaries; do not move evolution domain policy into the activator; keep degraded mode explicit and safe; avoid concurrent activation sessions; use bounded retry with configurable backoff（约束：保持分层边界；不要把演化领域策略移入激活器；降级态必须显式且安全；避免并发激活会话；使用带可配置退避的有界重试）

**Scale/Scope**: One new application entry point, a small runtime state model, and associated tests（规模/范围：一个新的 application 入口、一个小型运行时状态模型以及配套测试）

## Constitution Check（宪法检查）

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*（*门禁：必须在阶段 0 调研之前通过，并在阶段 1 设计后复查。*）

- The activator MUST remain within the application/orchestration boundary and must not become a domain policy owner.（激活器必须保持在 application/编排边界内，不能成为领域策略的持有者。）
- All activation, health, retry, and degradation behavior MUST be observable through explicit runtime state or return values.（所有激活、健康、重试和降级行为都必须能通过显式运行时状态或返回值被观测。）
- Recovery MUST be explicit and safe; the activator must not silently start duplicate workers or bypass guards.（恢复必须显式且安全；激活器不能静默启动重复 worker 或绕过守卫。）
- The implementation MUST reuse existing services/adapters rather than introducing a parallel self-evolution workflow.（实现必须复用现有 service/adapter，而不是引入平行的自进化工作流。）

## Project Structure（项目结构）

### Documentation (this feature)（文档（本功能））

```text
specs/20260518-143022-evolution-activator/
├── plan.md              # This file (/speckit-plan command output)（本文件（/speckit-plan 命令输出））
├── research.md          # Phase 0 output (/speckit-plan command)（阶段 0 输出（/speckit-plan 命令））
├── data-model.md        # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
├── quickstart.md        # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
├── contracts/           # Phase 1 output (/speckit-plan command)（阶段 1 输出（/speckit-plan 命令））
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)（阶段 2 输出（/speckit-tasks 命令 - 不由 /speckit-plan 创建））
```

### Source Code (repository root)（源代码（仓库根目录））

```text
sprintcycle/
├── application/
│   └── evolution/
│       ├── __init__.py
│       └── activator.py
├── domain/
│   └── evolution/
│       ├── __init__.py
│       └── runtime_state.py
├── infrastructure/
│   └── evolution/
│       └── adapters/
│           ├── health_check.py
│           └── retry_policy.py
└── tests/
    ├── application/
    │   └── evolution/
    └── domain/
        └── evolution/
```

**Structure Decision**: Implement the feature as a thin application-layer activator in `sprintcycle/application/evolution/activator.py`, with a small explicit runtime state model in `sprintcycle/domain/evolution/`, and adapter-backed health/retry collaborators in infrastructure. This keeps activation orchestration separate from self-evolution policy and stays aligned with the layered architecture and LangGraph boundary rules.（**结构决策**：将功能实现为 `sprintcycle/application/evolution/activator.py` 中的轻量 application 层激活器，在 `sprintcycle/domain/evolution/` 中放置一个小而显式的运行时状态模型，并在 infrastructure 中提供 health/retry 协作者。这样可以将激活编排与自进化策略分离，并与分层架构及 LangGraph 边界规则保持一致。）

## Phase 0 - Research（阶段 0 - 调研）

1. Identify existing self-evolution entry points, orchestration hooks, and runtime state surfaces that the activator should reuse.（识别现有自进化入口、编排钩子和运行时状态表面，供激活器复用。）
2. Confirm how activation guards should be expressed in the application layer without moving policy into the activator.（确认激活守卫应如何在 application 层表达，而不将策略移入激活器。）
3. Define the minimum health-check and retry collaborators needed to support bounded startup and steady-state monitoring.（定义支持有界启动与稳定态监控所需的最小健康检查与重试协作者。）
4. Verify how degraded state should be surfaced to callers and how recovery should be triggered without duplicate workers.（确认如何向调用方暴露降级态，以及如何在不产生重复 worker 的情况下触发恢复。）

## Phase 1 - Design（阶段 1 - 设计）

1. Design a small state model for `inactive`, `activating`, `active`, `degraded`, and `recovering` transitions.（设计一个小型状态模型，涵盖 `inactive`、`activating`、`active`、`degraded` 和 `recovering` 的迁移。）
2. Define the `activate()` flow, including guard evaluation, worker/session exclusivity, loop start, and health registration.（定义 `activate()` 流程，包括守卫评估、worker/session 排他、循环启动与健康注册。）
3. Define retry/backoff behavior for transient guard or health-check failures and the threshold for entering degraded mode.（定义瞬时守卫或健康检查失败时的重试/退避行为，以及进入降级态的阈值。）
4. Define recovery behavior so a healthy system can return from degraded mode without duplicating active loop workers.（定义恢复行为，使健康系统可从降级态返回，同时不会重复创建活跃循环 worker。）
5. Specify observability outputs: explicit reason codes or state records for blocked activation, retry exhaustion, and degradation.（规定可观测输出：例如阻断激活、重试耗尽和降级的显式原因码或状态记录。）

## Phase 1 Output Artifacts（阶段 1 输出工件）

- `data-model.md`: Evolution activation state, guard result, retry result, and health snapshot entities.（`data-model.md`：演化激活状态、守卫结果、重试结果与健康快照实体。）
- `quickstart.md`: Minimal activation and recovery flow for local verification.（`quickstart.md`：用于本地验证的最小激活与恢复流程。）
- `contracts/`: Any lifecycle or interface contracts needed to keep the activator observable and testable.（`contracts/`：为保持激活器可观测、可测试而需要的生命周期或接口契约。）

## Phase 1 Constitution Re-check（阶段 1 宪法复查）

After design, re-validate that the activator remains a thin orchestration boundary, that the state model is minimal, and that all retry/degradation behavior is explicit and recoverable.（设计完成后，重新验证激活器是否仍是薄编排边界、状态模型是否足够精简，以及所有重试/降级行为是否显式且可恢复。）

## Complexity Tracking（复杂度追踪）

No constitution violations identified for the proposed scope.（所提范围未发现宪法违规项。）
