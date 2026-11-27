---
id: TASK-1
title: Visual editor for the implement-tasks Harness Pool and Routing Rules
status: To Do
assignee: []
created_date: '2026-11-27T07:18:44Z'
labels:
  - ready-for-agent
dependencies: []
documentation:
  - docs/adr/0008-project-harness-routing-configuration.md
  - GLOSSARY.md
type: feature
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem Statement

Project maintainers describe harness preferences in prose. It is difficult to see which model and reasoning effort can handle a particular task, change a shared model without losing project-specific instructions, or tell which rule wins when a task fits several descriptions. A custom provider can also expose models whose family differs from the name of the Harness that launches them.

## Solution

Open a local browser editor with one command from the target repository. Manage the project's Harness Pool, describe tasks in ordered Routing Rules, and attach eligible candidates to each rule. Preview the policy as Markdown before saving. The Runner reads the same structured project configuration the editor reopens.

## User Stories

1. As a maintainer, I want to open the editor from my repository, so that I configure the intended project from an ordinary terminal or a Herdr session.
2. As a maintainer, I want to add a Harness from a list, so that I control which runtimes the Runner may use.
3. As a maintainer, I want to add and remove individual models within a Harness, so that the pool reflects my subscriptions.
4. As a maintainer, I want to select a discovered model, enter an exact custom ID, or choose the harness default, so that custom endpoints and runtimes with limited model selection are usable.
5. As a maintainer, I want my custom IDs to survive catalog refreshes, so that a missing catalog entry does not erase an assignment.
6. As a maintainer, I want to correct a model family once per harness/model pair, so that every rule uses the same information when selecting a Reviewer.
7. As a maintainer, I want editable starting rules for high-risk/architectural and typical/mechanical work, so that I can begin with familiar categories.
8. As a maintainer, I want to add, rename, describe, reorder, and delete rules, so that the Runner can recognize project-specific work such as Android E2E or a cross-module change.
9. As a maintainer, I want each rule to list several candidate models with their reasoning effort, so that one model can run at different efforts for different tasks.
10. As a maintainer, I want a candidate to serve both roles by default or only Worker or Reviewer, so that I can reserve a model for independent review.
11. As a maintainer, I want to see the impact of removing a Harness, so that I can replace candidates in affected rules without rewriting their descriptions.
12. As a maintainer, I want to edit project-wide and per-harness launch notes, so that PowerShell launch conventions and custom endpoint settings travel with the policy.
13. As a maintainer, I want to see existing handwritten instructions beside the initial form, so that I can transfer their meaning before saving.
14. As a maintainer, I want to preview, save, and reopen the same configuration, so that I can review the Markdown change and continue editing later.
15. As a Runner operator, I want the first matching rule to determine eligibility, so that I can give a specific rule priority over a broader one.
16. As a Runner operator, I want eligible assignments distributed according to load and available quota, so that concurrent work can use more than one subscription.
17. As a Runner operator, I want to prefer a different Harness and model family for review, so that an independent Reviewer can bring a different perspective when quota permits.
18. As a Runner operator, I want to narrow the pool for a single invocation, so that temporary subscription constraints do not change project settings.
19. As a Runner operator, I want a reason when the Runner cannot dispatch, so that I know which rule, candidate, or run restriction to revisit.

## Implementation Decisions

- ADR-0008 defines one structured configuration owned by the project. Save updates the existing project policy's Harness Pool & Routing section with the allowed pool, ordered routing, Reviewer preference, and launch notes. Preserve surrounding Markdown. On first use with handwritten routing, show it alongside the form and allow manual transfer and preview before replacement.
- Each Routing Rule has a name, a free-text task description, and candidate rows. New projects start with two editable rules and project-selected candidates. Candidate rows refer to a Harness and model, record effort (including the harness default where applicable), and specify eligible roles. Preserve exact model IDs independently of effort. Use supported harness capabilities when launching.
- Removing a Harness shows all affected rules before applying the change. Remove its candidate rows, retain rule descriptions, and flag rules that need a replacement model.
- Use the first matching description in displayed order. Apply role, availability, quota and run-specific filters within that rule. A launch prompt may narrow the pool. If no rule matches or no eligible candidate remains, report the reason and keep the task queued. Projects without a structured configuration retain the existing routing workflow.
- Prefer an eligible Reviewer with both a different Harness and a different known family from the Worker, then a different known family, then any available independent Reviewer. When family is unknown, a different Harness can guide selection. All choices respect the selected rule and quota.
- Keep the existing Runner evidence for the selected Harness, model, and effort. Project-wide and per-harness launch notes must be editable and present in the Markdown preview.

## Testing Decisions

- Exercise the public workflow in a disposable project through the editor's normal launch command and the Runner's normal task entry point. Assert observable UI, saved policy, generated Markdown, Run Record, and queue outcome. Control catalogs and quotas to make cases repeatable.
- Cover a blank project and first-time migration of handwritten routing. Save, reopen, and compare the preview with the resulting Markdown. Include unrelated surrounding sections, a custom model ID, editable family, per-rule effort, both note scopes, and removal of the sole candidate.
- Use a task matching two rules. Reorder them and verify the resulting assignment changes. Exercise role restrictions, a one-run pool restriction, unknown family, quota exhaustion, and an unmatched task. Check the reported reason and subsequent run behavior. For load balancing, verify eligibility and use of available capacity without requiring a particular scheduling algorithm.
- The repository's existing automated checks validate published documentation and its links. Keep those checks for the skill instructions and add workflow coverage for the editor and routing behavior.

## Out of Scope

Global or cross-project pools, remote hosting, automatic interpretation of handwritten policies, and changes to the Review Gate, Approval Gate, or Delivery Mode.

## Further Notes

The discussed agy, codex, and claude configurations illustrate a single project's policy. Model IDs, family names, and subscription choices in those examples are project data. Windows launch guidance and custom Claude endpoint notes are examples of editable launch notes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A maintainer can launch the editor from a project, configure its pool, ordered rules, efforts, roles, model families and launch notes, save, and reopen the same settings.
- [ ] #2 Migration displays existing prose, and saving reproduces the preview in the routing section while preserving other sections.
- [ ] #3 Removing a harness identifies affected rules, removes its candidates and visibly retains any empty rule for repair.
- [ ] #4 Runner dispatch respects the first match, per-role eligibility, effort, quota, and invocation filters, and reports when a task must remain queued.
- [ ] #5 Reviewer selection follows the configured preference and its fallbacks within eligible candidates, including unknown model families.
<!-- AC:END -->
