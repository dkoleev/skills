---
id: TASK-5
title: Per-model reasoning efforts from live Harness catalogs
status: Done
assignee:
  - '@claude'
created_date: '2026-11-27T12:36:00Z'
updated_date: '2026-11-27T12:39:36Z'
labels: []
dependencies: []
type: bug
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
agy lists one model ID per effort (gemini-4-neon-high, -low, ...) while also taking --effort, so the Harness Pool filled with effort variants and Candidates could pair a variant with a conflicting effort. Verified: agy accepts a base ID with --effort, rejects efforts a model lacks (claude-opus-5-5 has no xhigh) and rejects a variant ID with a different --effort. codex debug models reports supported_reasoning_levels per model (up to xhigh, max, ultra), so the earlier codex low/medium/high restriction was wrong.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The agy catalog merges effort variants into base model IDs with their available efforts
- [x] #2 The codex catalog reports each model's supported efforts and codex is no longer limited to low/medium/high
- [x] #3 Models added from a catalog keep their efforts in the pool; Candidates offer and the server accepts only default plus those efforts
- [x] #4 A suffixed agy variant ID allows only the default effort
- [x] #5 Launch matrix documents base agy IDs with --effort and per-model codex efforts
- [x] #6 Tests cover variant merging and per-model effort validation
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. routing_catalog: return model IDs with efforts; merge agy variants; read codex supported levels; add ultra to known efforts. 2. routing.py: optional pool efforts, per-model candidate validation, drop codex restriction, list efforts in Markdown. 3. editor.js: keep catalog efforts on add, per-model effort options. 4. harnesses.md, tests.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Live probes: agy accepts base ID + --effort, rejects unknown models, rejects efforts a model lacks, and rejects a variant ID with a different --effort. Live catalogs: agy merges into 11 base models (e.g. gemini-4-neon low..xhigh, claude-opus-5-5 low..high, gpt-oss-120b medium only); codex reports up to xhigh/max/ultra per model. Verified with scripts/test_routing.py (11 tests), check_docs.py, and a headless Chrome run adding claude-opus-5-5 from the live agy catalog (efforts stored, Candidate effort list default/low/medium/high, suffixed variant default only, preview lists efforts). ultra is offered only where a catalog lists it; Harness-level fallback lists exclude it. Existing configs that pair a suffixed agy ID with a non-default effort now fail validation.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Catalogs now report per-model efforts: agy effort variants merge into base models and codex reads supported_reasoning_levels. Pool entries added from a catalog keep an efforts list; Candidates offer and the server accepts only default plus those efforts, and suffixed agy variant IDs allow only default. Removed the wrong codex low/medium/high cap, added ultra for models that list it, listed efforts in the Markdown pool, and updated the launch matrix.
<!-- SECTION:FINAL_SUMMARY:END -->
