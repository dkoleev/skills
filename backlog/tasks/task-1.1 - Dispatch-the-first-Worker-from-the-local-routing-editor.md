---
id: TASK-1.1
title: Dispatch the first Worker from the local routing editor
status: To Do
assignee: []
created_date: '2026-11-27T07:22:39Z'
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
- [ ] #1 One documented command from the target repository opens its local editor from a normal terminal or Herdr session.
- [ ] #2 The user can select a Harness, enter an exact model ID, assign it with effort to an initial rule and preview the routing Markdown.
- [ ] #3 Saving and reopening restores the same selection. The saved routing section matches the preview and preserves surrounding Markdown.
- [ ] #4 A matching task launched through implement-tasks uses the configured Worker. Its Run Record identifies the selected Harness, model and effort.
- [ ] #5 A project without a structured configuration still follows the existing routing workflow.
<!-- AC:END -->
