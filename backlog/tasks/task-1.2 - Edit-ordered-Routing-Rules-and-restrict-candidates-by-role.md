---
id: TASK-1.2
title: Edit ordered Routing Rules and restrict candidates by role
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T07:22:41Z'
updated_date: '2026-11-27T09:11:22Z'
labels:
  - ready-for-agent
dependencies:
  - TASK-1.1
parent_task_id: TASK-1
type: feature
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Parent

TASK-1

## What to build

Let maintainers describe the work in their own words and decide which rule wins when a task matches more than one. Eligibility and effort belong to each candidate row in its rule.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 New projects start with editable High-risk / architectural and Typical / mechanical rules. Rules can be added, renamed, described, reordered and removed.
- [x] #2 A rule accepts multiple candidates. The same model can have different effort across rules, including default effort where applicable. Each row defaults to both roles and can be restricted to Worker or Reviewer.
- [x] #3 Saving and reopening preserves the configured order and candidate rows, and the Markdown reflects the changes.
- [x] #4 For a task matching two rules, reordering them changes the assignment. The Runner only selects candidates eligible for the requested role within the first match.
- [x] #5 With no matching rule or no role-eligible candidate in the first match, the Runner explains the reason and keeps the task queued.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Extend the editor to manage ordered rules and candidate roles, retaining existing saved fields. 2. Resolve the first matching rule through the Runner interface and stop its queue entry on unmatched or ineligible routes. 3. Verify reordering and role-based outcomes through the public workflow.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Exercised rule add, rename, move, remove, candidate rows, roles, save, and reload in Chrome. CLI and automated workflow tests verify first-match order, role-specific effort, and that unmatched or role-ineligible work stays queued.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added ordered rule editing and role-scoped selection through the shared Runner command, with queue reasons and first-match enforcement.
<!-- SECTION:FINAL_SUMMARY:END -->
