---
id: TASK-6
title: 'Routing: fair tie-breaks, effort escalation, editor warnings'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-27T13:21:23Z'
updated_date: '2026-11-27T13:24:34Z'
labels: []
dependencies: []
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Apply the routing review list: quota and least-assigned tie-breaks, unreachable-candidate and sample-description warnings, escalate_to effort, Claude effort table, custom Claude endpoint family warning, no __pycache__, docs on rule order and Crush .gitignore, minimal inline code padding.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Equal-load Candidates are ordered by remaining quota, then by fewest assignments in the invocation
- [x] #2 Editor warns about Candidates that can never be selected, sample rule descriptions, and Claude models on a custom endpoint without an explicit Model Family
- [x] #3 A Candidate can set escalate_to, validated against the model's efforts, and the Runner docs say when it applies
- [x] #4 Claude catalog models carry their supported efforts
- [x] #5 Running routing.py writes no __pycache__ into the skill
- [x] #6 Docs state that the first matching rule wins and that sample descriptions must be adapted; README notes the Crush .gitignore
- [x] #7 Inline code only pads with spaces when needed
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Equal-load Candidates now rank by known remaining quota, then by fewest assignments this invocation (new runtime field assigned, counted from Run Records). Candidates may set escalate_to (validated against the model's efforts and only for Workers); the Runner applies it from Correction Round 2. Preview and save return warnings: unreachable same-model Candidates, sample rule descriptions, and claude models without a family when ANTHROPIC_BASE_URL or the claude Launch Note points at a custom endpoint. The editor shows these warnings and adds a retry-effort select. Claude catalog aliases list low through max. routing.py sets dont_write_bytecode. Docs cover first-match rule order, adapting descriptions, tie-breaks, escalation, and the Crush .gitignore. inline() pads only when needed. Weighted shares were skipped. Unreachable Candidates produce a warning, not a rejection, so existing configs still load.
<!-- SECTION:FINAL_SUMMARY:END -->
