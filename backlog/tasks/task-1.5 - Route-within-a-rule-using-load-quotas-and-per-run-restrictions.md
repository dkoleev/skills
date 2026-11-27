---
id: TASK-1.5
title: Route within a rule using load, quotas and per-run restrictions
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T07:22:49Z'
updated_date: '2026-11-27T09:18:58Z'
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
- [x] #1 Concurrent tasks use available capacity within their first matching rule according to load and quota. The Run Records identify eligible assignments.
- [x] #2 A launch instruction such as codex only narrows the selected rule for that invocation. A subsequent ordinary invocation can use the full saved pool.
- [x] #3 When one eligible candidate exhausts its quota, other available candidates within the matching rule can take new work.
- [x] #4 When filtering or quota exhaustion leaves no eligible candidate, the Runner reports the reason and keeps the task queued, including when a lower-priority rule could have supplied a candidate.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Pass invocation restrictions and live capacity signals to the Runner selector without writing project settings. 2. Filter and distribute assignments within the first match and expose queue reasons when blocked. 3. Exercise load, quota, failover, and one-run restrictions against controlled inputs.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Workflow tests supply controlled active counts, capacity, quotas, and run filters to the Runner command. They verify distribution across Harnesses, retry routing, queued reasons with a lower-priority match, and unchanged saved settings between invocations.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added live-capacity selection, quota failover, and transient restrictions within the first matching Routing Rule. The Runner records reservations before dispatch.
<!-- SECTION:FINAL_SUMMARY:END -->
