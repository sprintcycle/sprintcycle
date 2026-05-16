# SprintCycle Spec-Kit Template

This document defines the formal Spec-Kit workflow for medium/high complexity work. Use it when a task needs a standalone specification artifact before architecture and implementation.

## 1. Purpose

Spec-Kit turns a task into an explicit, reviewable contract before code changes begin. It is the required spec layer for medium/high complexity work in SprintCycle.

## 2. When to use

Use Spec-Kit when the task is:
- multi-file
- cross-layer
- boundary-sensitive
- contract-impacting
- architecture-impacting
- likely to need review loops

Do not use Spec-Kit for trivial one-file edits unless the change is still risky or contract-sensitive.

## 3. Required outputs

A Spec-Kit run must produce a task-specific spec artifact under `docs/specs/`.

The artifact must be readable on its own and include:
- goal
- non-goals
- scope
- constraints
- implementation approach
- acceptance criteria
- validation plan
- risks
- rollback / loop-back conditions

## 4. Spec structure

### 4.1 Task summary
- task name
- request source
- owner / requester
- date
- complexity class
- route decision

### 4.2 Goal
State the intended outcome in one or two sentences.

### 4.3 Non-goals
List what this spec will not change.

### 4.4 Scope
Describe the files, modules, or layers included in the task.

### 4.5 Constraints
Record the boundaries the implementation must not cross.

### 4.6 Implementation approach
Describe the recommended implementation path at a high level.

### 4.7 Acceptance criteria
List observable conditions that define success.

### 4.8 Validation plan
Describe the tests, lint checks, or behavioral checks that must be run.

### 4.9 Risks and loop-back conditions
Document the main risks and when the task must return to Coordinator.

## 5. Two-layer artifact model

Spec-Kit has two layers:

### 5.1 Template layer
- File: `docs/SPEC_KIT.md`
- Purpose: reusable structure and rules for all medium/high complexity tasks

### 5.2 Task spec layer
- File: `docs/specs/<date>-<topic>.md`
- Purpose: task-specific working specification for one change

The task spec must follow the template but may be shorter when the task is small within the medium/high category.

## 6. Workflow

```text
Coordinator -> Complexity Check -> Spec-Kit Template -> Task Spec Artifact -> Architect -> Implementation -> QA/Review -> Pass / Loop
```

## 7. Minimal task spec example outline

```text
# Task name

## Summary
## Goal
## Non-goals
## Scope
## Constraints
## Implementation approach
## Acceptance criteria
## Validation plan
## Risks
## Loop-back conditions
```

## 8. Maintenance notes

- Keep this template aligned with `docs/AI_GOVERNANCE.md`, `docs/CURSOR_TEAM_PLAYBOOK.md`, and `docs/IT_RESEARCH_TEAM_FLOW.md`.
- Do not treat this document as governance; it is a workflow template only.
- Update task specs under `docs/specs/` as individual deliverables.
