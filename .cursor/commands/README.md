# Cursor Commands Index / 命令索引

This directory contains the fixed command entry points for SprintCycle Cursor workflows.

## Governance references

Before using commands, read:
- `docs/AI_GOVERNANCE.md` for governance, routing, and conflict policy
- `docs/CURSOR_TEAM_PLAYBOOK.md` for the minimum complete AI team and workflow order

## Command groups

### 1. Intake and routing

#### `/team-command`
Use this as the first entry point for new work.

Responsibilities:
- classify task complexity
- choose OpenSpec or Spec-Kit
- route to the right workflow mode
- identify whether Architect is needed
- produce the minimal execution path

Use for:
- new feature planning
- multi-step refactors
- cross-layer changes
- unclear requirements

### 2. Spec and implementation flow

#### `/spec-command`
Use this when you want to turn a request into a task spec.

Responsibilities:
- define goal, non-goals, scope, constraints, and acceptance criteria
- choose OpenSpec for low complexity or Spec-Kit for medium/high complexity
- produce the spec handoff for Implementation or Architect

Use for:
- request clarification
- task scoping
- spec drafting
- complexity-based spec routing

#### `/architect-command`
Use this when you need task decomposition and boundary design.

Responsibilities:
- split work into safe sub-steps
- define dependencies and ownership boundaries
- identify parallelizable parts
- produce an implementation plan

Use for:
- multi-file changes
- boundary-sensitive work
- cross-module design
- refactor planning

#### `/implement-command`
Use this when the spec and breakdown are ready and code changes should begin.

Responsibilities:
- implement only what the spec covers
- keep changes localized
- report files touched, deviations, and self-check notes

Use for:
- code changes
- refactors with approved scope
- feature delivery
- localized fixes

#### `/qa-command`
Use this when implementation is ready for validation.

Responsibilities:
- verify behavior against the spec
- check regressions and edge cases
- identify missing tests or follow-up work
- decide whether the change passes or must loop back

Use for:
- validation
- regression review
- test gap discovery
- release readiness checks

### 3. Review and synthesis

#### `/review-arch`
Runs architecture review through `arch-guardian`.

Use for:
- service migrations
- import/export changes
- public API changes
- layer boundary changes

#### `/review-graph`
Runs LangGraph orchestration review through `graph-orchestrator`.

Use for:
- node responsibilities
- state transitions
- plan / sprint split
- dispatch flow

#### `/review-lifecycle`
Runs lifecycle review through `lifecycle-auditor`.

Use for:
- execution continuity
- runtime registry checks
- observability and promotion continuity
- recovery path validation

#### `/review-tests`
Runs test-risk review through `test-risk-reviewer`.

Use for:
- behavior changes
- critical-path refactors
- API or contract changes
- regression risk checks

#### `/review-final`
Runs final synthesis through `review-commander`.

Use for:
- multi-review changes
- final verdict consolidation
- release-ready decision-making

### 4. Delivery support

#### `/commit-message`
Summarizes the current change and drafts a commit message.

Use for:
- preparing a commit summary
- aligning commit text with the repository's style

## Recommended command flow

### Low complexity
`/team-command` → `/spec-command` → `/implement-command` → `/qa-command` → `/review-final`

### Medium complexity
`/team-command` → `/spec-command` → `/architect-command` → `/implement-command` → `/qa-command` → `/review-final`

### High complexity
`/team-command` → `/spec-command` → `/architect-command` → `/implement-command` → `/qa-command` → specialist reviews → `/review-final`

## Routing summary

- Low complexity -> OpenSpec route
- Medium complexity -> Spec-Kit route
- High complexity -> Spec-Kit route with Architect + QA/Review

## Maintenance

When adding a new command:
- document its purpose here
- link it to the correct role or workflow
- keep terminology aligned with `docs/AI_GOVERNANCE.md`
- keep the index concise and role-oriented
