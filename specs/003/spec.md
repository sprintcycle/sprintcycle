# Feature Specification: EvolutionActivator（自进化激活器）

**Feature Branch**: `002-evolution-activator`（功能分支：`002-evolution-activator`）

**Created**: 2026-05-18（创建时间：2026-05-18）

**Status**: Draft（状态：草稿）

**Input**: User description: "EvolutionActivator | 自进化组件存在但未激活 | 创建`application/evolution/activator.py`激活循环"（输入：用户描述：“EvolutionActivator | 自进化组件存在但未激活 | 创建`application/evolution/activator.py`激活循环”）

## Clarifications（澄清）

### Session 2026-05-18
- Q: `EvolutionActivator` 激活后应承担哪些责任？ → A: 除了启动循环，还要补齐激活守卫、健康检查、失败重试与降级。

## User Scenarios & Testing *(mandatory)*（用户场景与测试 *（必填）*）

### User Story 1 - Activate self-evolution safely（安全激活自进化） (Priority: P1)（用户故事 1 - 安全激活自进化（优先级：P1））

As a maintainer, I want a dedicated `EvolutionActivator` so that self-evolution can be enabled without embedding activation concerns into the domain evolution logic.（作为维护者，我希望有一个专门的 `EvolutionActivator`，以便可以在不把激活关切嵌入领域演化逻辑的情况下启用自进化。）

**Why this priority**: The feature exists to make the self-evolution capability operational while preserving architecture boundaries.（为什么是这个优先级：该功能的存在是为了让自进化能力可运行，同时保持架构边界。）

**Independent Test**: Create an activator with mocked dependencies, call `activate()`, and verify the activation guard, loop start, and initial state transition behave as expected.（独立测试：使用 mock 依赖创建激活器，调用 `activate()`，验证激活守卫、循环启动和初始状态流转符合预期。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** activation guards pass, **When** `activate()` is called, **Then** the evolution loop starts and the activator enters an active state.（**Given** 激活守卫通过，**When** 调用 `activate()`，**Then** 自进化循环启动，激活器进入激活状态。）
2. **Given** activation guards fail, **When** `activate()` is called, **Then** the loop does not start and the activator reports a blocked activation reason.（**Given** 激活守卫失败，**When** 调用 `activate()`，**Then** 循环不会启动，激活器会报告阻断激活的原因。）

---

### User Story 2 - Detect unhealthy evolution runtime（检测不健康的演化运行时） (Priority: P2)（用户故事 2 - 检测不健康的演化运行时（优先级：P2））

As an operator, I want health checks and bounded retries so that temporary failures do not permanently break self-evolution.（作为运维人员，我希望有健康检查和有界重试，以便临时故障不会永久破坏自进化。）

**Why this priority**: A running activator must remain resilient after startup, not just successfully boot once.（为什么是这个优先级：运行中的激活器必须在启动后保持韧性，而不只是成功启动一次。）

**Independent Test**: Stub the runtime dependency health checks and retry policy, then simulate transient and persistent failures to verify retry and degradation behavior.（独立测试：stub 运行时依赖健康检查和重试策略，模拟瞬时与持续失败，验证重试与降级行为。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** a transient failure occurs, **When** the activator performs health checks, **Then** it retries within the configured limit before returning to healthy operation.（**Given** 发生瞬时失败，**When** 激活器执行健康检查，**Then** 它会在配置限制内重试，随后恢复到健康运行。）
2. **Given** failures persist beyond the retry limit, **When** health checks continue to fail, **Then** the activator enters a degraded state and stops progressing the evolution loop.（**Given** 失败持续超过重试限制，**When** 健康检查持续失败，**Then** 激活器进入降级态并停止推进自进化循环。）

---

### User Story 3 - Recover from degraded mode（从降级态恢复） (Priority: P3)（用户故事 3 - 从降级态恢复（优先级：P3））

As a maintainer, I want the activator to recover when dependencies become healthy again so that self-evolution can resume without manual rework.（作为维护者，我希望激活器在依赖恢复健康后自动恢复，以便自进化可以在无需手工重建的情况下继续。）

**Why this priority**: Recovery completes the lifecycle and avoids leaving the system stuck in a degraded-but-recoverable state.（为什么是这个优先级：恢复能力完成生命周期闭环，避免系统卡在可恢复但未恢复的降级态。）

**Independent Test**: Simulate a degraded state followed by healthy dependency signals, then verify the activator leaves degraded mode and resumes the loop.（独立测试：模拟降级态后再出现健康依赖信号，验证激活器退出降级态并恢复循环。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** the activator is degraded due to prior failures, **When** dependencies recover, **Then** the activator can transition back to active mode.（**Given** 激活器因先前失败而降级，**When** 依赖恢复，**Then** 激活器可以回到激活模式。）
2. **Given** the activator is degraded, **When** an activation attempt is retried after recovery, **Then** it revalidates guards and resumes the loop without duplicating active workers.（**Given** 激活器处于降级态，**When** 恢复后重试激活，**Then** 它会重新校验守卫并恢复循环，同时不会重复启动活跃工作线程。）

---

### Edge Cases（边界情况）

- What happens when the evolution loop starts but the first health check fails?（当自进化循环启动但第一次健康检查失败时会怎样？）
- What happens if `activate()` is called while the activator is already active?（当激活器已处于激活状态时再次调用 `activate()` 会怎样？）
- How are repeated transient failures distinguished from a true degraded condition?（如何区分重复瞬时失败与真正的降级状态？）
- How does the system avoid duplicate loop workers after a recovery attempt?（系统如何避免在恢复尝试后出现重复循环 worker？）

## Requirements *(mandatory)*（需求 *（必填）*）

### Functional Requirements（功能需求）

- **FR-001**: System MUST provide `application/evolution/activator.py` as the dedicated entry point for activating self-evolution.（系统必须提供 `application/evolution/activator.py` 作为激活自进化的专用入口。）
- **FR-002**: System MUST enforce activation guards before starting the evolution loop.（系统必须在启动自进化循环之前执行激活守卫。）
- **FR-003**: System MUST expose a health check mechanism that can detect unhealthy runtime conditions during activation and steady state.（系统必须提供健康检查机制，以便在激活和稳定运行期间检测不健康的运行时状态。）
- **FR-004**: System MUST retry transient activation or health-check failures using a bounded retry policy with configurable limits and backoff.（系统必须使用带配置上限和退避策略的有界重试来处理瞬时激活或健康检查失败。）
- **FR-005**: System MUST enter a degraded state when failures persist beyond the retry policy or when a dependency becomes unavailable.（系统必须在失败持续超过重试策略或依赖不可用时进入降级态。）
- **FR-006**: System MUST stop progressing the evolution loop while in degraded state.（系统必须在降级态下停止推进自进化循环。）
- **FR-007**: System MUST allow recovery from degraded state when guards and health checks pass again.（系统必须允许在守卫和健康检查再次通过时从降级态恢复。）
- **FR-008**: System MUST avoid duplicating active loop workers or concurrent activation sessions.（系统必须避免重复的循环 worker 或并发激活会话。）
- **FR-009**: System MUST keep activation concerns isolated from the underlying self-evolution domain logic, using existing application/service/facade/hook/orchestrator boundaries.（系统必须将激活关切与底层自进化领域逻辑隔离，并使用现有的 application/service/facade/hook/orchestrator 边界。）

### Key Entities *(include if feature involves data)*（关键实体 *（如果功能涉及数据则填写）*）

- **EvolutionActivator**: Coordinates activation, guard evaluation, loop lifecycle, health monitoring, retry, and degradation handling.（`EvolutionActivator`：协调激活、守卫评估、循环生命周期、健康监控、重试与降级处理。）
- **ActivationGuard**: Represents pre-start checks that decide whether activation may proceed.（`ActivationGuard`：表示决定是否允许激活继续的启动前检查。）
- **EvolutionHealthState**: Captures active, degraded, and recovering runtime states for the evolution loop.（`EvolutionHealthState`：捕获自进化循环的激活、降级和恢复运行时状态。）
- **RetryPolicy**: Defines retry limits, backoff, and failure classification for activation and health checks.（`RetryPolicy`：定义激活和健康检查的重试限制、退避和失败分类。）

## Success Criteria *(mandatory)*（成功标准 *（必填）*）

### Measurable Outcomes（可衡量结果）

- **SC-001**: A guarded activation attempt either starts the evolution loop or returns a clear blocked reason, with no silent partial activation.（受守卫保护的激活尝试要么启动自进化循环，要么返回清晰的阻断原因，不允许静默的部分激活。）
- **SC-002**: Transient failures are retried according to the configured retry policy before degradation is declared.（瞬时失败会按照配置的重试策略进行重试，然后才宣布降级。）
- **SC-003**: Persistent failures cause the activator to enter degraded mode and pause loop progression.（持续失败会使激活器进入降级态并暂停循环推进。）
- **SC-004**: Recovery from degraded mode resumes activation without duplicating active workers.（从降级态恢复后可以恢复激活，同时不会重复创建活跃 worker。）
- **SC-005**: Activation behavior can be validated with mocked guards, health checks, and retry policies in unit tests.（激活行为可以通过 mock 守卫、健康检查和重试策略在单元测试中验证。）

## Assumptions（假设）

- The underlying self-evolution capability already exists and only needs a dedicated activation lifecycle.（底层自进化能力已经存在，只需要一个专用的激活生命周期。）
- Existing application/service/facade/hook/orchestrator boundaries are available for integration.（现有的 application/service/facade/hook/orchestrator 边界可用于集成。）
- Degraded mode is a safe, explicit state that favors stopping progression over speculative continuation.（降级态是一个安全且显式的状态，优先停止推进而不是投机性继续运行。）
- Health checks and retry classification can be implemented using existing runtime signals and dependency checks.（健康检查和重试分类可以使用现有运行时信号和依赖检查来实现。）
