---
id: TASK-1.4
title: Migrate handwritten routing and maintain launch notes
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T07:22:47Z'
updated_date: '2026-11-27T09:16:54Z'
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
- [x] #1 On first use with handwritten routing, the editor shows the existing section beside the form for manual transfer and preview before replacement.
- [x] #2 The maintainer can edit project-wide and per-harness notes, including PowerShell instructions and custom endpoint model guidance.
- [x] #3 Saving writes the previewed routing section including both note scopes, preserving unrelated Markdown. Opening the form alone does not replace existing prose.
- [x] #4 Reopening loads the structured configuration and restores both note scopes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Display a first-use handwritten routing section alongside the editor without writing files. 2. Store and preview project-wide and per-Harness launch notes, preserving surrounding policy during save. 3. Verify migration and reopening in the browser and editor/Runner commands.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Chrome verified the handwritten section beside the form before preview or save, and restoration of both note scopes after reload. Tests verify preview/save equality, preserving adjacent Markdown and a custom policy path, and no policy writes during preview.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added first-use handwritten migration and editable project-wide and per-Harness launch notes, with the same generated Markdown on preview and save.
<!-- SECTION:FINAL_SUMMARY:END -->
