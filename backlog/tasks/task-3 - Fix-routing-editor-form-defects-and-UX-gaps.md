---
id: TASK-3
title: Fix routing editor form defects and UX gaps
status: Done
assignee:
  - '@claude'
created_date: '2026-11-27T11:32:45Z'
updated_date: '2026-11-27T11:38:05Z'
labels: []
dependencies: []
type: bug
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Review of the local routing editor form found defects that corrupt saved routing (Enter saves to disk, untrimmed model IDs, efforts a Harness cannot apply, unordered candidates) and UX gaps (stale preview, no unsaved-changes guard, unconfirmed rule removal, lost focus and catalog status, unexplained rule order).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Pressing Enter in a text field never saves; Ctrl+S saves
- [x] #2 Model IDs with surrounding whitespace are trimmed in the form and rejected by the server
- [x] #3 Each candidate offers and the server accepts only efforts the Harness supports
- [x] #4 Candidates can be reordered within a rule and duplicate candidates are rejected
- [x] #5 Removing a rule or stopping with unsaved edits asks for confirmation; closing the tab with unsaved edits warns
- [x] #6 The preview updates automatically after edits and the save bar with status stays visible
- [x] #7 A save conflict offers to overwrite with the current edits
- [x] #8 The catalog loads when a Harness is added, focus and catalog status survive re-renders, rule order semantics are explained
- [x] #9 Routing tests cover the new server validation and conflict status
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Server: per-Harness efforts, trimmed model IDs, duplicate-candidate check, 409 on revision conflict, policy path in state. 2. Form: block Enter submit, Ctrl+S, auto-preview, dirty tracking with beforeunload, sticky save bar. 3. Rules/candidates: numbering and order hint, candidate reorder, confirm rule removal, smarter default candidate, a11y labels. 4. Pool: auto catalog load, keep focus and catalog status, family override in details, drop notes of removed Harness. 5. Tests and README.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified with scripts/test_routing.py (10 tests) and check_docs.py, plus a scratch headless-Chrome CDP script exercising 20 interactions: Enter no-save, Ctrl+S save, auto preview, unsaved flag and beforeunload, trimmed IDs with kept focus, per-Harness efforts reset, candidate reorder, rule-removal confirm/cancel, unused-model default, duplicate reporting, 409 overwrite preserving external sections, catalog auto-load and persistence, aria labels, stop confirmation. Codex efforts follow the launch matrix (low/medium/high); opencode is default-only. Existing saved configs using xhigh/max with codex now fail validation with a named error.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fixed routing editor form defects and UX gaps. Server: per-Harness efforts, model IDs with padding rejected, duplicate candidates rejected, revision conflicts return 409, state reports the policy path. Form: Enter no longer saves (Ctrl+S does), live preview replaces the Preview button, unsaved-changes flag with tab-close and stop guards, sticky save bar, numbered rules with order hints, reorderable candidates, confirmed rule removal, overwrite option on conflicts, catalog auto-load with persistent status and focus, family override folded into details, launch notes removed with their Harness, contextual aria labels. Risk: codex configs saved with xhigh/max now need editing.
<!-- SECTION:FINAL_SUMMARY:END -->
