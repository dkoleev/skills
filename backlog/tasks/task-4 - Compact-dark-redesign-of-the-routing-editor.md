---
id: TASK-4
title: Compact dark redesign of the routing editor
status: Done
assignee:
  - '@claude'
created_date: '2026-11-27T12:15:40Z'
updated_date: '2026-11-27T12:20:31Z'
labels: []
dependencies: []
type: enhancement
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The routing editor is oversized and hard to scan: nested cards, a 2.75rem title, a permanent 40% preview column, and a long single stream of sections. Maintainers mostly configure once and later glance at or tweak which Candidates serve each Routing Rule, so the screen should answer that at a glance. Decisions from the grilling session: dark-only theme, vanilla HTML/CSS/JS, desktop from 1280px.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Layout is a sticky ~48px header with status, Markdown, Save with an unsaved marker, and Stop; a ~280px Harness Pool sidebar; and Routing Rules in the main area
- [x] #2 With 4 Harnesses, 8 models and 4 rules of up to 3 Candidates, all rules and Candidates fit a 1440x900 viewport without scrolling
- [x] #3 Each Candidate is one row with pool model, effort, a Worker/Reviewer/Both segmented control, and move/remove actions
- [x] #4 Sidebar groups show models with a Model Family badge that opens an override field, a single add-model field with catalog suggestions including Harness default, catalog reload, and a collapsible per-Harness Launch Note
- [x] #5 Independent Reviewer toggle sits in the Routing Rules header and the project Launch Note sits at the bottom of the sidebar
- [x] #6 Markdown preview and handwritten migration open in a right drawer that updates live and opens automatically during migration
- [x] #7 Removal asks for confirmation only when it cascades into rules or drops a Launch Note
- [x] #8 Dark theme meets WCAG AA text contrast; empty required fields show a red border
- [x] #9 Earlier behaviour is kept: live preview, unsaved guard, Ctrl+S, conflict overwrite, per-Harness efforts
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Rewrite index.html into header, sidebar, rules area and drawer templates. 2. Rewrite style.css as a dense dark theme using native field-sizing and :user-invalid. 3. Adapt editor.js renderers to the new templates, keeping state and server calls. 4. Re-run routing tests and a headless Chrome interaction script; capture a screenshot at 1440x900.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified with scripts/test_routing.py, check_docs.py and a scratch headless-Chrome CDP script (36 checks, 1440x900): reference scale (4 Harnesses, 8 models, 4 rules x 3 Candidates) fits with page height 900, header <=50px, sidebar 280px, one-line Candidate rows, WCAG AA for all theme text pairs, drawer live preview and Escape, migration auto-open, first-run hint, cascade-only confirmations, badge family override, datalist add, collapse persistence, Enter/Ctrl+S, conflict overwrite, beforeunload. Deviation: the drawer pushes the rules left instead of overlaying them, because the overlay hid role controls during migration. Glossary gained Candidate, Launch Note and Model Family.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Redesigned the routing editor as a compact dark single screen: sticky header with status, Markdown, Save with unsaved marker and Stop; a 280px Harness Pool sidebar with collapsible Harness groups, Model Family badges, a single add-model field, catalog reload, and per-Harness and project Launch Notes; Routing Rules with text-like name and description fields, one-line Candidate rows and a segmented role control; a live Markdown drawer that opens for migration. Confirmations only on cascading removals. All earlier behaviour retained; README and glossary updated.
<!-- SECTION:FINAL_SUMMARY:END -->
