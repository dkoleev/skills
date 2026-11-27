---
id: TASK-1.4
title: Migrate handwritten routing and maintain launch notes
status: To Do
assignee: []
created_date: '2026-11-27T07:22:47Z'
labels:
  - ready-for-agent
dependencies:
  - TASK-1.1
parent_task_id: TASK-1
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Parent

TASK-1

## What to build

Help an existing project adopt structured routing without losing the meaning of its handwritten policy. Give maintainers one editor for shared launch notes and instructions specific to a Harness.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 On first use with handwritten routing, the editor shows the existing section beside the form for manual transfer and preview before replacement.
- [ ] #2 The maintainer can edit project-wide and per-harness notes, including PowerShell instructions and custom endpoint model guidance.
- [ ] #3 Saving writes the previewed routing section including both note scopes, preserving unrelated Markdown. Opening the form alone does not replace existing prose.
- [ ] #4 Reopening loads the structured configuration and restores both note scopes.
<!-- AC:END -->
