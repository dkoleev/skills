---
id: TASK-1.6
title: Prefer an independent Reviewer across harnesses and model families
status: To Do
assignee: []
created_date: '2026-11-27T07:22:52Z'
labels:
  - ready-for-agent
dependencies:
  - TASK-1.3
  - TASK-1.5
parent_task_id: TASK-1
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Parent

TASK-1

## What to build

Make the project's cross-vendor Reviewer preference editable and use the actual model family when a Harness serves multiple providers. Keep role, quota and per-run eligibility in force when applying the preference.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The editor supplies a known family when available and accepts a manual correction per Harness/model pair. Every rule using the pair sees that family after save and reopen.
- [ ] #2 The maintainer can configure the Reviewer preference and see it reflected in the preview and saved routing policy.
- [ ] #3 When enabled, the Runner first prefers an eligible independent Reviewer differing from the Worker in both Harness and known model family, then a different known family, then an available independent Reviewer.
- [ ] #4 With unknown family information a different Harness can guide selection. An exhausted or role-ineligible candidate is skipped, and the Run Record identifies the actual Reviewer choice.
<!-- AC:END -->
