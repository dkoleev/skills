---
id: TASK-1.6
title: Prefer an independent Reviewer across harnesses and model families
status: Done
assignee:
  - '@codex'
created_date: '2026-11-27T07:22:52Z'
updated_date: '2026-11-27T09:25:25Z'
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
- [x] #1 The editor supplies a known family when available and accepts a manual correction per Harness/model pair. Every rule using the pair sees that family after save and reopen.
- [x] #2 The maintainer can configure the Reviewer preference and see it reflected in the preview and saved routing policy.
- [x] #3 When enabled, the Runner first prefers an eligible independent Reviewer differing from the Worker in both Harness and known model family, then a different known family, then an available independent Reviewer.
- [x] #4 With unknown family information a different Harness can guide selection. An exhausted or role-ineligible candidate is skipped, and the Run Record identifies the actual Reviewer choice.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add editable shared model families and a Reviewer preference to the pool and policy preview. 2. Rank eligible independent Reviewers by Harness and known family using the actual Worker assignment. 3. Verify preference, fallbacks, unknown families, and filtering together.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
The browser persisted the Reviewer preference and model-family correction. Workflow tests verified distinct Harness and family ranking, a same-Harness different-family fallback, unknown family, and quota, role and run filters. An actual fresh Herdr Reviewer pane confirmed the fixture output with the reported Codex model and effort also in its Run Record.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added per-model family corrections and independent Reviewer preference within the selected Routing Rule. Verified fallback selection in tests and a fresh Reviewer launch in Herdr.
<!-- SECTION:FINAL_SUMMARY:END -->
