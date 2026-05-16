# SprintCycle Cursor Team Playbook

This document defines the operating model for AI-assisted development work in SprintCycle. It describes the minimum complete team, command entry points, task routing policy, and the relationship between this playbook and the governance document.

## 文档关系 / Document hierarchy

- `AGENTS.md` — 仓库级底线 / repository-level baseline
- `docs/AI_GOVERNANCE.md` — 治理总纲 / governance charter
- `docs/CURSOR_TEAM_PLAYBOOK.md` — 执行手册 / execution manual
- `.cursor/rules/` — 路由和优先级 / routing and priority
- `.cursor/commands/` — 命令入口 / command entry points

## 1. Relationship to AI governance

This playbook is the execution manual.
`docs/AI_GOVERNANCE.md` is the governance source of truth.

- Governance defines the rules
- This playbook defines how the team executes those rules
- Task specs define what a specific task must accomplish
- See the governance overview diagram in `docs/AI_GOVERNANCE.md` for the full layer map

## 2. Team model

SprintCycle’s minimum complete AI development team is intentionally small and explicit:

- `Coordinator` — intake, classification, routing, and work breakdown
- `Spec` — task specification, scope definition, and acceptance criteria
- `Architect` — boundaries, dependencies, and task decomposition
- `Implementation` — code changes and implementation execution
- `QA/Review` — regression checks, spec compliance, and validation

This is the smallest team that can still complete the full loop from intake to validated delivery.

## 3. Role responsibilities

### 3.1 Coordinator
Use first when the request is broad, multi-step, or ambiguous.

Responsibilities:
- classify task complexity
- choose OpenSpec or Spec-Kit
- select the minimum required workflow
- assign the next role
- decide whether a task needs Architect involvement
- collect final results and trigger review loops if necessary

### 3.2 Spec
Responsibilities:
- transform the request into an explicit task spec
- define scope, non-goals, constraints, and acceptance criteria
- choose OpenSpec for low complexity tasks
- choose Spec-Kit for medium/high complexity tasks

### 3.3 Architect
Responsibilities:
- split the task into safe sub-steps
- define dependencies and boundaries
- identify parallelizable parts
- keep the implementation surface small

### 3.4 Implementation
Responsibilities:
- implement only what is covered by the spec
- avoid unrelated refactors
- keep changes localized to the owning layer

### 3.5 QA/Review
Responsibilities:
- verify the change against the spec
- check for regressions and edge cases
- block completion when acceptance criteria are not met
- recommend concrete follow-up fixes

## 4. Command entry points

Use commands when you want a fixed entry that maps to a specific role.

- `/team-command` → `Coordinator`
- `/spec-kit` → `Spec-Kit` template + task spec workflow
- `/review-arch` → `Architect`
- `/review-tests` → `QA/Review`
- `/review-final` → final synthesis
- `/commit-message` → summarize changes and draft commit text

If the repository later introduces commands for spec routing, document them here.

## 5. Routing policy

### 5.1 OpenSpec route
Use OpenSpec for:
- low complexity
- small scope
- low risk
- no architecture change
- no contract change

Recommended flow:
- Coordinator
- OpenSpec
- Implementation
- QA/Review
- Complete

### 5.2 Spec-Kit route
Use Spec-Kit for:
- medium complexity
- high complexity
- boundary-sensitive changes
- cross-module work
- higher regression risk

Recommended flow:
- Coordinator
- Spec-Kit
- Architect
- Implementation
- QA/Review
- Complete

### 5.3 Skipping Architect
Architect can be skipped only when:
- the task is low complexity
- the change is localized
- the boundaries are already obvious

### 5.4 Mandatory review
QA/Review is mandatory for:
- contract changes
- refactors
- cross-layer changes
- anything that may regress behavior

## 6. Complexity decision guide

### Low complexity
Typical signals:
- one file
- limited surface area
- low risk
- simple acceptance criteria

Use OpenSpec.

### Medium complexity
Typical signals:
- multiple files
- some dependencies
- moderate risk
- explicit validation needed

Use Spec-Kit.

### High complexity
Typical signals:
- architecture change
- runtime or governance change
- cross-layer coupling
- migration or refactor work
- high regression risk

Use Spec-Kit and require Architect plus QA/Review.

## 7. Conflict avoidance rules

- Do not maintain duplicate global constraints in both spec systems
- Do not let a task spec override governance rules
- Do not treat OpenSpec as a second governance system
- Do not rewrite the same rule in multiple places
- If a rule changes, update the governance layer first

## 8. Recommended work patterns

### A. Small bug fix
1. Coordinator
2. OpenSpec
3. Implementation
4. QA/Review
5. Complete

### B. Standard feature
1. Coordinator
2. Spec-Kit
3. Architect
4. Implementation
5. QA/Review
6. Complete

### C. Large refactor
1. Coordinator
2. Spec-Kit
3. Architect
4. Implementation
5. QA/Review
6. Loop back if needed
7. Complete

## 9. Workflow protocol

SprintCycle uses a mixed-mode execution protocol so the same five roles can handle both small iterations and larger refactors without changing the team model.

### 9.1 Lightweight flow
Use the lightweight flow when the task is small, localized, and low risk.

```text
Coordinator → Spec → Implementation → QA/Review → Done
```

### 9.2 Strict flow
Use the strict flow when the task is multi-file, boundary-sensitive, or higher risk.

```text
Coordinator → Spec → Architect → Implementation → QA/Review → Done
```

### 9.3 Handoff rules
Every role must pass a compact handoff package to the next role.

- Coordinator → Spec: task summary, complexity, route, risks
- Spec → Architect / Implementation: goals, non-goals, scope, constraints, acceptance criteria
- Architect → Implementation: breakdown, dependencies, boundaries, implementation order
- Implementation → QA/Review: changed files, deviations, self-check summary, validation focus
- QA/Review → Coordinator: verdict, missing checks, risk level, required follow-up

### 9.4 Escalation rules
- If the Spec discovers scope expansion, escalate to the strict flow.
- If Implementation finds hidden dependencies, escalate to the strict flow.
- If QA/Review finds high regression risk, block completion and route back through Coordinator.

### 9.5 Output templates
Each role should keep its output short and structured.

- Coordinator: classification, routing, workflow mode, risks, next step
- Spec: goal, non-goals, scope, constraints, acceptance criteria, recommended route
- Architect: breakdown, dependencies, boundaries, implementation order, risks
- Implementation: changes made, files touched, notes, self-check summary
- QA/Review: validation summary, missing checks, high-risk scenarios, verdict, follow-up

## 10. AI team quick card

### 10.1 Minimum complete team
- Coordinator
- Spec
- Architect
- Implementation
- QA/Review

### 10.2 Default full flow
```text
Coordinator → Spec → Architect → Implementation → QA/Review → Done
```

### 10.3 Lightweight flow
```text
Coordinator → Spec → Implementation → QA/Review → Done
```

### 10.4 Routing rule
- Low complexity → OpenSpec + lightweight flow
- Medium complexity → Spec-Kit + strict flow
- High complexity → Spec-Kit + strict flow + stronger review

### 10.5 One-line rule of thumb
- `Coordinator` decides the route
- `Spec` writes the task contract
- `Architect` breaks down the work
- `Implementation` changes the code
- `QA/Review` decides pass or loop back

## 11. Maintenance

When adding a new agent, command, or routing rule:
- add it here
- define its trigger conditions
- keep the name aligned with the existing team vocabulary
- update `docs/AI_GOVERNANCE.md` if it affects governance
