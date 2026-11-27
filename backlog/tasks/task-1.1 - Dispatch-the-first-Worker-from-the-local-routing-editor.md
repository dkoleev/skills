---
id: TASK-1.1
title: Dispatch the first Worker from the local routing editor
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T07:22:39Z'
updated_date: '2026-11-27T09:07:34Z'
labels:
  - ready-for-agent
dependencies: []
parent_task_id: TASK-1
type: feature
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Parent

TASK-1

## What to build

Give a maintainer a first working route in a new project. From the repository, open the local browser editor, choose a Harness and enter a model ID and reasoning effort, then save and run a matching task. The editor and Runner share the project's structured configuration.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 One documented command from the target repository opens its local editor from a normal terminal or Herdr session.
- [x] #2 The user can select a Harness, enter an exact model ID, assign it with effort to an initial rule and preview the routing Markdown.
- [x] #3 Saving and reopening restores the same selection. The saved routing section matches the preview and preserves surrounding Markdown.
- [x] #4 A matching task launched through implement-tasks uses the configured Worker. Its Run Record identifies the selected Harness, model and effort.
- [x] #5 A project without a structured configuration still follows the existing routing workflow.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add a bundled, dependency-free Python command that opens a local editor for the current Git project and validates, previews, saves, and reopens versioned routing settings under .agents/.
2. Connect Worker selection and Run Record fields to the same configuration through the existing implement-tasks dispatch steps. Preserve the legacy branch when structured settings are absent.
3. Test the documented command, editor round trip, policy preservation, and Worker assignment in a disposable Git project.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified browser preview, save, reload, preservation of surrounding CRLF Markdown, the editor command in Herdr, and legacy detection in disposable Git projects. Exercised the Runner dispatch steps in Herdr with Codex gpt-6.2-sol at low effort. The fixture Run Record and worker output agree, and the Worker committed the expected sample.txt.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a dependency-free local routing editor and the structured Worker assignment path. Verified the browser and Herdr workflow plus automated tests and documentation checks.
<!-- SECTION:FINAL_SUMMARY:END -->
