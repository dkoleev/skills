---
id: TASK-1.5
title: Route within a rule using load, quotas and per-run restrictions
status: To Do
assignee: []
created_date: '2026-11-27T07:22:49Z'
labels:
  - ready-for-agent
dependencies:
  - TASK-1.2
parent_task_id: TASK-1
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Parent

TASK-1

## What to build

Allow a Runner operator to conserve a subscription or spread work across eligible candidates while keeping the project's routing policy intact.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Concurrent tasks use available capacity within their first matching rule according to load and quota. The Run Records identify eligible assignments.
- [ ] #2 A launch instruction such as codex only narrows the selected rule for that invocation. A subsequent ordinary invocation can use the full saved pool.
- [ ] #3 When one eligible candidate exhausts its quota, other available candidates within the matching rule can take new work.
- [ ] #4 When filtering or quota exhaustion leaves no eligible candidate, the Runner reports the reason and keeps the task queued, including when a lower-priority rule could have supplied a candidate.
<!-- AC:END -->
