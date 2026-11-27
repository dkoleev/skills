---
id: TASK-1.3
title: Manage harnesses and models in the project Harness Pool
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T07:22:44Z'
updated_date: '2026-11-27T09:14:35Z'
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
- [x] #1 The editor supports adding a Harness from a list and adding or removing individual models within it.
- [x] #2 The user can select a model from its Harness catalog, enter an exact manual ID or use the Harness default. A catalog refresh preserves custom IDs and their assignments.
- [x] #3 The preview identifies the allowed pool. Saved pool choices survive reopening, and the Runner honors model selection through supported Harness launch capabilities.
- [x] #4 Before deleting a Harness, the editor lists every affected rule. Deletion removes its candidate rows, retains rule descriptions and marks any rule needing a replacement.
- [x] #5 Removing an individual model leaves other models usable and clears references to the removed model.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add pool management and model catalog discovery with exact manual IDs and an explicit Harness default. 2. Reference only pool entries from candidate rows and preview all affected rules before removing a Harness. 3. Verify catalog refresh, save and reopen, and candidate cleanup.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Chrome verified model discovery, an exact custom ID surviving a catalog refresh, Harness defaults, individual model removal, and the impact dialog with a retained empty rule. The HTTP and Runner workflow tests verify persisted pool membership and explicit/default selection.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the editable Harness Pool, catalog discovery, custom and default model choices, and removal of stale candidate references.
<!-- SECTION:FINAL_SUMMARY:END -->
