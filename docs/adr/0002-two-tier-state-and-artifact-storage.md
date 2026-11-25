---
status: accepted
---

# Two-Tier State and Artifact Storage

Workers and Reviewers often run inside restricted project contexts or sandboxed assumptions while generating transient screenshots, logs, and review-loop state, yet their final reports and evidence must survive after a task worktree is removed. We split runtime storage into two tiers: ephemeral task files live inside `<worktree>/.implement-tasks/<task-id>/` (excluded globally via `<git-common-dir>/info/exclude`), while durable Run Records, `summary.md`, and archived artifacts live in `<git-common-dir>/implement-tasks/<task-id>/`.

## Considered Options

- **Store everything inside `<git-common-dir>`:** Agents in worktree-scoped sandboxes or strict file boundaries may be blocked from writing outside their worktree root.
- **Store everything inside a project directory (such as `Builds/` or `.gitignore` edits):** Couples the skill to a specific framework's `.gitignore` or dirties tracked repository files.
- **Two-tier storage (`info/exclude` + `<git-common-dir>` archive):** Agents write only inside their own worktree while keeping `git status` clean across all linked worktrees without touching `.gitignore`, and the Runner archives final evidence before cleanup.

## Consequences

- The Runner must ensure `.implement-tasks/` is appended to `<git-common-dir>/info/exclude` before dispatching Workers.
- Before a worktree can be removed, the Runner must archive referenced artifacts and `review-state.json` into `<git-common-dir>/implement-tasks/<task-id>/`.
