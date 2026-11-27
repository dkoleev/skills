---
id: TASK-1.3
title: Manage harnesses and models in the project Harness Pool
status: To Do
assignee: []
created_date: '2026-11-27T07:22:44Z'
labels:
  - ready-for-agent
dependencies:
  - TASK-1.1
parent_task_id: TASK-1
type: feature
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Parent

TASK-1

## What to build

Maintain the allowed pool as subscriptions and installed runtimes change. Choose discovered models, preserve custom endpoint IDs, and show the consequences of removing a harness before applying the edit.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The editor supports adding a Harness from a list and adding or removing individual models within it.
- [ ] #2 The user can select a model from its Harness catalog, enter an exact manual ID or use the Harness default. A catalog refresh preserves custom IDs and their assignments.
- [ ] #3 The preview identifies the allowed pool. Saved pool choices survive reopening, and the Runner honors model selection through supported Harness launch capabilities.
- [ ] #4 Before deleting a Harness, the editor lists every affected rule. Deletion removes its candidate rows, retains rule descriptions and marks any rule needing a replacement.
- [ ] #5 Removing an individual model leaves other models usable and clears references to the removed model.
<!-- AC:END -->
