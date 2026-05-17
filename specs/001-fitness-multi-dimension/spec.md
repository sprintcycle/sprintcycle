# Feature Specification: Multi-Dimension Fitness（多维度 Fitness）

**Feature Branch**: `001-fitness-multi-dimension`（功能分支：`001-fitness-multi-dimension`）

**Created**: 2026-05-17（创建时间：2026-05-17）

**Status**: Draft（状态：草稿）

**Input**: User description: "统一 Fitness 评分入口，整合多维质量工具"（输入：用户描述：“统一 Fitness 评分入口，整合多维质量工具”）

## Clarifications（澄清）

### Session 2026-05-17
- Q: `MultiDimensionFitness` 的职责边界应该是什么？ → A: 它负责协调执行和产出治理建议，不直接承载底层工具实现。
- Q: 最终覆盖哪些质量维度？ → A: 7 个维度：`quality`、`security`、`architecture`、`types`、`coverage`、`maintainability`、`performance`。
- Q: 这 7 个维度的权重是否需要可配置？ → A: 权重可配置，带默认值。
- Q: 统一 Fitness 入口的通过阈值应该是多少？ → A: 80 分通过。

## User Scenarios & Testing *(mandatory)*（用户场景与测试 *（必填）*）

### User Story 1 - Unified fitness evaluation（统一 Fitness 评估） (Priority: P1)（用户故事 1 - 统一 Fitness 评估（优先级：P1））

As a maintainer, I want a single `MultiDimensionFitness` entry point so that I can evaluate code quality across multiple dimensions from one place.（作为维护者，我希望拥有一个统一的 `MultiDimensionFitness` 入口，以便可以从一个位置评估代码质量的多个维度。）

**Why this priority**: This is the primary user value and the core reason for the feature.（为什么是这个优先级：这是最核心的用户价值，也是该功能存在的主要原因。）

**Independent Test**: Run the evaluator against a sample project and verify the returned payload includes all configured dimensions, weighted scores, total score, and pass/fail status.（独立测试：对一个示例项目运行评估器，验证返回结果包含全部配置维度、加权分数、总分以及通过/失败状态。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** a project root with quality tools available, **When** `evaluate()` runs, **Then** it returns a total score and dimension breakdown for all configured dimensions.（**Given** 一个可用质量工具的项目根目录，**When** `evaluate()` 运行，**Then** 它返回总分以及所有配置维度的明细。）
2. **Given** a project whose weighted total is at least 80, **When** evaluation completes, **Then** the result is marked as passed.（**Given** 一个加权总分至少为 80 的项目，**When** 评估完成，**Then** 结果标记为通过。）
3. **Given** a project whose weighted total is below 80, **When** evaluation completes, **Then** the result is marked as failed.（**Given** 一个加权总分低于 80 的项目，**When** 评估完成，**Then** 结果标记为失败。）

---

### User Story 2 - Orchestrate multi-tool checks（编排多工具检查） (Priority: P2)（用户故事 2 - 编排多工具检查（优先级：P2））

As a developer, I want `MultiDimensionFitness` to orchestrate the underlying quality tools so that the checks run through one coordinated flow.（作为开发者，我希望 `MultiDimensionFitness` 能协调底层质量工具，使检查通过一个统一流程执行。）

**Why this priority**: Tool orchestration is required for the unified entry point to be useful in practice.（为什么是这个优先级：要让统一入口真正可用，就必须具备工具编排能力。）

**Independent Test**: Stub the individual tool adapters and verify the evaluator invokes each dimension check and aggregates the returned values.（独立测试：对单个工具适配器做 stub，验证评估器会调用每个维度检查并聚合返回值。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** all adapters are available, **When** evaluation starts, **Then** the dimension checks run and their results are aggregated into a single response.（**Given** 所有适配器都可用，**When** 评估开始，**Then** 各维度检查运行，并聚合成一个统一响应。）
2. **Given** one dimension check fails, **When** evaluation completes, **Then** the failure is reflected in that dimension without preventing the other dimensions from being reported when possible.（**Given** 某一维度检查失败，**When** 评估完成，**Then** 该失败会体现在对应维度中，同时在可行时不阻止其他维度结果的汇报。）

---

### User Story 3 - Provide governance suggestions（提供治理建议） (Priority: P3)（用户故事 3 - 提供治理建议（优先级：P3））

As a reviewer, I want the fitness result to include governance-oriented suggestions so that I can decide what to fix first.（作为评审者，我希望 fitness 结果包含治理建议，以便决定优先修复什么。）

**Why this priority**: Suggestions improve the value of the score, but they are secondary to the scoring entry point itself.（为什么是这个优先级：建议能提升评分结果的实用性，但它们次于评分入口本身。）

**Independent Test**: Verify the returned payload includes suggestion data when one or more dimensions fall below threshold or emit warnings.（独立测试：验证当一个或多个维度低于阈值或发出警告时，返回结果包含建议数据。）

**Acceptance Scenarios**:（验收场景：）

1. **Given** one or more dimensions are below threshold, **When** evaluation completes, **Then** the result includes suggestions for remediation.（**Given** 一个或多个维度低于阈值，**When** 评估完成，**Then** 结果包含修复建议。）
2. **Given** all dimensions pass cleanly, **When** evaluation completes, **Then** suggestions are empty or indicate no action needed.（**Given** 所有维度都干净通过，**When** 评估完成，**Then** 建议为空或表明无需操作。）

---

### Edge Cases（边界情况）

- What happens when a tool adapter is unavailable?（当某个工具适配器不可用时会怎样？）
- How does the system handle partial results from one or more dimensions?（系统如何处理一个或多个维度的部分结果？）
- What happens if two dimensions return conflicting signals?（如果两个维度返回冲突信号会怎样？）
- How are timeout and async execution failures reported?（超时和异步执行失败如何报告？）

## Requirements *(mandatory)*（需求 *（必填）*）

### Functional Requirements（功能需求）

- **FR-001**: System MUST expose a single `MultiDimensionFitness` entry point for multi-dimension evaluation.（系统必须提供一个统一的 `MultiDimensionFitness` 入口用于多维度评估。）
- **FR-002**: System MUST support 7 evaluation dimensions: `quality`, `security`, `architecture`, `types`, `coverage`, `maintainability`, and `performance`.（系统必须支持 7 个评估维度：`quality`、`security`、`architecture`、`types`、`coverage`、`maintainability` 和 `performance`。）
- **FR-003**: System MUST evaluate dimensions through existing adapters/services rather than embedding tool logic directly in domain aggregation code.（系统必须通过现有 adapter/service 执行维度评估，而不是把工具逻辑直接嵌入领域聚合代码。）
- **FR-004**: System MUST calculate a weighted total score using configurable weights with safe defaults.（系统必须使用可配置权重并带有安全默认值来计算加权总分。）
- **FR-005**: System MUST mark the evaluation as passed when the weighted total score is greater than or equal to 80.（系统必须在加权总分大于或等于 80 时将评估标记为通过。）
- **FR-006**: System MUST return per-dimension scores, weights, and details in the evaluation payload.（系统必须在评估结果中返回每个维度的分数、权重和明细。）
- **FR-007**: System MUST emit governance suggestions when one or more dimensions fail or underperform.（系统必须在一个或多个维度失败或表现不足时输出治理建议。）
- **FR-008**: System MUST remain testable by stubbing or mocking each underlying tool adapter independently.（系统必须能够通过独立 stub 或 mock 每个底层工具适配器来测试。）

### Key Entities *(include if feature involves data)*（关键实体 *（如果功能涉及数据则填写）*）

- **MultiDimensionFitness**: Coordinates evaluation across multiple quality dimensions and returns a unified `FitnessResult`.（`MultiDimensionFitness`：协调多个质量维度的评估并返回统一的 `FitnessResult`。）
- **DimensionScore**: Represents a single dimension’s score, weight, and optional details.（`DimensionScore`：表示单个维度的分数、权重和可选明细。）
- **FitnessResult**: The aggregated output containing total score, dimension breakdown, pass/fail status, suggestions, and a `to_dict()` serialization method.（`FitnessResult`：聚合输出，包含总分、维度明细、通过/失败状态、建议，以及 `to_dict()` 序列化方法。）

## Success Criteria *(mandatory)*（成功标准 *（必填）*）

### Measurable Outcomes（可衡量结果）

- **SC-001**: A single evaluation call returns all configured dimension scores and a weighted total.（一次评估调用返回所有配置维度的分数和加权总分。）
- **SC-002**: The default pass threshold of 80 is applied consistently across evaluations.（默认 80 分通过阈值在所有评估中保持一致应用。）
- **SC-003**: Each dimension can be mocked independently in tests without changing the aggregator contract.（每个维度都可以在测试中独立 mock，而无需改变聚合器契约。）
- **SC-004**: Users can identify the highest-priority remediation items from the returned governance suggestions.（用户可以从返回的治理建议中识别最优先的修复项。）

## Assumptions（假设）

- Existing adapters or services will provide the underlying checks for each dimension.（现有 adapter 或 service 会提供每个维度的底层检查能力。）
- The evaluation runs asynchronously so independent tool checks can be coordinated efficiently.（评估以异步方式运行，以便高效协调独立工具检查。）
- Coverage data is available from the project test workflow or a compatible coverage source.（覆盖率数据来自项目测试流程或兼容的 coverage 来源。）
- Performance scoring is derived from an existing measurable signal rather than heuristic text analysis.（性能评分来自现有可测量信号，而不是启发式文本分析。）
