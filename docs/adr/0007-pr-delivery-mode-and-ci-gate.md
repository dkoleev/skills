---
status: accepted
---

# GitHub PR Delivery Mode and Continuous Integration Gate

Local sequential merging (`local`) integrates verified tasks directly on the developer machine without publishing remote branches or testing against remote CI pipelines. Projects that require remote review, branch protection, or GitHub Actions validation need a first-class delivery pipeline that publishes pull requests, tests against CI, and merges remotely without causing tracker file conflicts or breaking autonomous queue progression. We introduce **PR Delivery Mode** (`pr`), configured via `## Delivery Mode` in `.agents/implement-tasks-auto-merge.md` or selected per run via `--pr` / `--local`.

## Considered Options

- **Local merge only (current baseline):** Integrates via `git merge --no-ff --no-commit` in the primary checkout and never touches the remote repository. Simple and offline-capable, but cannot gate on remote CI workflows, team branch protections, or GitHub Pull Request discussions.
- **Branch from primary checkout `HEAD` including `In Progress` tracker commit:** Inherits local unpushed `Backlog.md` card status commits in every task branch. When multiple tasks run in parallel, their PRs conflict on `Backlog.md` files upon merge, blocking CI and automated PR merging.
- **Allow Workers to push and create PRs immediately upon startup:** Opens unreviewed, potentially broken or noisy PRs on the remote repository during early implementation iterations, triggering unnecessary CI runs and notification churn.
- **Isolated PR Delivery with clean origin branching, post-review `SHIP_PR` handoff, and CI gating:** Task worktrees branch cleanly from `origin/<primary_branch>` (`base_sha`) so local tracker updates never pollute PR branches. Remote pushes remain forbidden during implementation and review. After the Review Gate completes (`verdict=pass` or trivial-skip), the Runner delegates PR publishing to the Worker via a secure `$ship_token` (`SHIP_PR`), monitors GitHub Actions checks via `gh pr checks --watch`, routes failed run logs (`gh run view --log-failed`) back to the Worker for targeted fixes within the 5-round cap, and merges via `gh pr merge` + `git pull --ff-only` + `Backlog.md` `Done` commit and push under existing Approval Gate rules.

## Consequences

- Delivery mode is governed by `## Delivery Mode` in `.agents/implement-tasks-auto-merge.md` (defaulting to `local`) and can be overridden per invocation with `--pr` or `--local`.
- PR delivery requires the GitHub CLI (`gh`) and Git remote access to `origin`.
- Task branches stay strictly isolated from task tracking files: because worktrees branch from `origin/<primary_branch>`, multiple PRs can merge without merge conflicts in `Backlog.md`.
- Remote repository safety is maintained: Workers cannot push or open PRs until the Runner explicitly issues `SHIP_PR` with `$ship_token` following a successful Review Gate.
- The Approval Gate is extended to require green GitHub Actions checks (`pass` or `no-checks`): routine changes with `approval=auto` auto-merge remotely via `gh pr merge`, pull into the primary checkout, commit `Backlog.md` `Done`, and push `origin/<primary_branch>`, while `--handle` or risky changes pause with PR and CI links in `summary-<task-id>`.
