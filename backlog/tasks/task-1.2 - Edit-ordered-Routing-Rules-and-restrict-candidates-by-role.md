---
id: TASK-1.2
title: Edit ordered Routing Rules and restrict candidates by role
status: To Do
assignee: []
created_date: '2026-11-27T07:22:41Z'
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
- [ ] #1 New projects start with editable High-risk / architectural and Typical / mechanical rules. Rules can be added, renamed, described, reordered and removed.
- [ ] #2 A rule accepts multiple candidates. The same model can have different effort across rules, including default effort where applicable. Each row defaults to both roles and can be restricted to Worker or Reviewer.
- [ ] #3 Saving and reopening preserves the configured order and candidate rows, and the Markdown reflects the changes.
- [ ] #4 For a task matching two rules, reordering them changes the assignment. The Runner only selects candidates eligible for the requested role within the first match.
- [ ] #5 With no matching rule or no role-eligible candidate in the first match, the Runner explains the reason and keeps the task queued.
<!-- AC:END -->
