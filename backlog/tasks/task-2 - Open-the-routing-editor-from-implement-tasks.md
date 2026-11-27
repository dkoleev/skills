---
id: TASK-2
title: Open the routing editor from implement-tasks
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T11:09:33Z'
updated_date: '2026-11-27T11:12:42Z'
labels: []
dependencies:
  - TASK-1
type: enhancement
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A maintainer currently has to locate the installed skill and type its full Python script path each time they open the editor.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An explicit implement-tasks --configure invocation opens the local routing editor for the current Git project without requiring a Herdr session or starting the task queue.
- [x] #2 The launcher returns a working URL while the editor remains available and the maintainer can close the editor from the browser.
- [x] #3 The documentation leads with the new shortcut and retains a direct terminal workflow.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add the explicit configure mode to the installed skill. 2. Reuse the Python editor in a background process with a browser close action and a ready URL. 3. Exercise the shortcut launch and shutdown from a disposable project and document the primary entry point.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified the launcher in a disposable Git project, including the returned URL, foreground compatibility, background availability after launcher exit, and shutdown with a malformed configuration. Opened the returned URL in Chrome and stopped the editor using its button. All nine workflow tests and documentation checks passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the explicit configure mode to implement-tasks, with a project-local background editor, ready URL, and browser shutdown. Updated the README with the shortcut and direct terminal launch.
<!-- SECTION:FINAL_SUMMARY:END -->
