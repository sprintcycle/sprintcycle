# SprintCycle Cursor Team Playbook

This document defines the project-specific AI operating team for SprintCycle development work.

## 1. Team model

SprintCycle work should be handled by a small, explicit team with clear ownership:

- `team-commander` — intake, task classification, routing, and work breakdown
- `arch-guardian` — layer boundaries, ownership, and cross-layer coupling
- `graph-orchestrator` — LangGraph flow, state transitions, and dispatch orchestration
- `lifecycle-auditor` — runtime, observability, promotion, and execution continuity
- `test-risk-reviewer` — regression, edge cases, compatibility, and missing tests
- `review-commander` — final synthesis across specialist reviews

## 2. Role ownership

### `team-commander`
Use first when the request is broad, multi-step, or ambiguous.

Responsibilities:
- classify the task
- identify the owning subsystem
- choose the minimum specialist path
- propose the execution order
- ask for the smallest missing detail when needed

### `arch-guardian`
Use for structure, ownership, imports, exports, and boundary risks.

Responsibilities:
- keep API and presentation layers thin
- prevent cross-layer business logic leakage
- detect duplicate or misplaced responsibilities
- preserve the current SprintCycle architecture skeleton

### `graph-orchestrator`
Use for graph runtime changes, node responsibilities, and stage transitions.

Responsibilities:
- keep graph nodes orchestration-only
- verify plan/sprint split and dispatch flow
- ensure explicit and minimal state transitions
- avoid embedding domain rules in graph nodes

### `lifecycle-auditor`
Use for runtime lifecycle, observability, and promotion/evolution continuity.

Responsibilities:
- validate execution chain continuity
- check runtime registry and execution state consistency
- verify trace, replay, and evidence capture
- detect breaks in recovery or promotion paths

### `test-risk-reviewer`
Use for risky behavior changes or after implementation to identify coverage gaps.

Responsibilities:
- find missing tests for changed behavior
- identify failure-path and edge-case gaps
- call out compatibility concerns
- recommend concrete test names and assertions

### `review-commander`
Use at the end of a multi-review workflow.

Responsibilities:
- consolidate specialist findings
- remove duplicates
- prioritize blockers
- produce a single final verdict

## 3. Command entry points

Use commands when you want a fixed entry that maps to a specific role.

- `/team-command` → `team-commander`
- `/review-arch` → `arch-guardian`
- `/review-graph` → `graph-orchestrator`
- `/review-lifecycle` → `lifecycle-auditor`
- `/review-tests` → `test-risk-reviewer`
- `/review-final` → `review-commander`
- `/commit-message` → summarize current changes and draft commit text

## 4. Recommended workflows

### A. New feature or multi-step change
1. Run `/team-command`
2. Follow the routing plan
3. Implement in the owning layer only
4. Run the relevant review command(s)
5. Finish with `/review-final`

### B. Architecture or refactor work
1. Run `/team-command`
2. Review with `/review-arch`
3. If graph or lifecycle is involved, add `/review-graph` and/or `/review-lifecycle`
4. Add `/review-tests` if behavior changed
5. End with `/review-final`

### C. Bug fix with regression risk
1. Run `/team-command`
2. Implement the smallest safe fix
3. Run `/review-tests`
4. If the fix touches boundaries or lifecycle, add the specialist review

### D. Final shipping pass
1. Specialist review(s)
2. `/review-final`
3. `/commit-message`

## 5. Decision rules

- Start with the smallest relevant role.
- Escalate only when more than one subsystem is involved.
- Prefer review before rewrite when ownership is unclear.
- Keep implementation localized to the owning layer.
- Use final review only after specialist reviews are complete.

## 6. SprintCycle-specific principles

- Public API should stay thin.
- Graph should orchestrate, not own business rules.
- Lifecycle and observability must remain continuous.
- Governance, suggestion handling, and evolution flows must not be bypassed.
- Tests should cover changed behavior and failure paths, not just happy paths.

## 7. Practical examples

- HTTP/API routing change → `team-commander` → `arch-guardian`
- LangGraph node refactor → `team-commander` → `graph-orchestrator`
- Execution/runtime change → `team-commander` → `lifecycle-auditor`
- API contract change → `team-commander` → `arch-guardian` + `test-risk-reviewer`
- Large cross-layer PR → all relevant specialists → `review-commander`

## 8. Maintenance

When adding a new agent, command, or rule:

- add its ownership and trigger conditions here
- keep naming aligned with the existing team vocabulary
- update the routing rule if the new role affects priority
- update the README so contributors can discover the new capability quickly
