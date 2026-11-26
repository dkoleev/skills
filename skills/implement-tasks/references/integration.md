# Integration, Approval Gate, Auto-Merge, PR Delivery, and Cleanup

## Integration modes

- **Risk-gated auto-merge (default):** Evaluates the [Approval Gate](auto-merge-rules.md) after a verified `pass` review OR after a verified Worker `ready` report when review was skipped (trivial-task skip or `--no-review`), plus green PR checks in `pr` mode. Only when project rules in `<repo-root>/.agents/implement-tasks-auto-merge.md` are configured and satisfied, verification has no meaningful gaps, and `approval=auto` holds (from both Runner and Reviewer when reviewed, or from the Runner alone when review was skipped), the Runner automatically integrates (`--no-ff --no-commit` + combined verification in `local` mode, or `gh pr merge` + `git pull --ff-only` in `pr` mode), commits `Backlog.md` `Done`, cleans up the task's Herdr terminals, space/workspace, Git worktree, and merged branch, advances `base_sha` in `session.json`, reassesses deferred conflicting tasks, and updates `status.md` in the Runner's **Status Pane** with the PR link (if `pr` mode), merge commit SHA, `Done` commit SHA, verification results, and clickable links to archived `summary.md` and screenshots/artifacts.
- **Human approval (`approve` / `--handle`):** Never auto-merges when running with `--handle`, when `.agents/implement-tasks-auto-merge.md` is missing/unfilled, when `approval=human` (from Reviewer or Runner), when `escalated`/`blocked`, when CI failed in `pr` mode, or when merge/verification fails. Instead, the task remains `In Progress` (`awaiting approval`) with its worktree, PR (in `pr` mode), and **Summary Pane** (`summary-<task-id>`) open, and the Runner asks the user for `approve <task-id>` in chat and in **Status Pane**.
- **Accepted approval commands:** `approve <task-id>` (for example `approve TASK-12`), `approve all` (authorizes all currently `awaiting approval` tasks at their verified target commit: `reviewed_sha` when reviewed, or `submitted_sha` when `review_skipped == true`), and synonym `merge <task-id>` authorize sequential merge, combined verification (or PR merge in `pr` mode), committing `Done`, and automatic cleanup unless the user explicitly asks to keep the workspace open. Handle close-only requests for unmerged work separately and confirm whether the branch or any uncommitted changes should be preserved.
- **`git push` rule:** In `local` delivery mode, never run `git push` automatically; remote pushes always require separate explicit user authorization. In `pr` delivery mode, pushing `<task_branch>` is authorized once review completes via `$ship_token`, and pushing `<primary_branch>` is authorized after PR merge when updating `Backlog.md` `Done`.

## Pre-merge verification

For every task entering integration (automatically via `approval=auto`, or on `approve <task-id>` / `approve all` / `merge <task-id>`), read its Run Record (`<git-common-dir>/implement-tasks/<task-id>/run.json`) and `backlog instructions task-finalization`. Verify that:
- The destination matches the recorded `primary_checkout` and `primary_branch`.
- The worktree belongs to the task and its branch and `HEAD` still match the verified target commit (`reviewed_sha` when reviewed, or `submitted_sha` when `review_skipped == true`).
- The task worktree is clean and archived evidence (`summary.md`, listed artifacts, and `review-state.json` when review ran) already exists in `<git-common-dir>/implement-tasks/<task-id>/`.
- In `pr` delivery mode, verify via `gh pr view <pr-url> --json state,headRefOid,mergeStateStatus,statusCheckRollup` that `headRefOid` still matches the verified target commit and checks are green (`ci_status` is `"pass"` or `"no-checks"`), or detect cleanly if the PR was already merged manually on GitHub.

If the task commit changed since verified completion, re-evaluate the Review Gate (and re-run peer review if required) and obtain fresh user `approve` if required before integrating.

## Merge and verify sequentially

### Path A: `local` delivery mode

1. Verify the primary checkout has no merge in progress, a clean Git index, and no local edits overlapping incoming files. Distinguish ordinary uncommitted `Backlog.md` metadata changes from code changes under test, keeping pre-existing edits outside the merge.
2. Prepare the merge using the repository's merge convention (for standard merges: `git merge --no-ff --no-commit <approved-sha>`) and run the relevant combined verification checks **before** committing.
3. **Failure handling:** If merging introduces conflicts, overlaps uncommitted primary edits, or fails combined verification checks, run `git merge --abort`, preserve the task worktree and pre-existing primary edits, open the task's **Summary Pane** (`summary-<task-id>`) if not already open, update `status.md` (`needs attention`) and redraw the Runner's **Status Pane**, and do not mark `Done`. Routine merge conflicts may be reconciled inside the task worktree followed by a fresh review pass (or fresh diff/verification check when `--no-review` or when the reconciled diff still satisfies trivial-skip rules); non-trivial conflicts or combined-test failures escalate to the user.
4. Commit the merge and verify `<approved-sha>` is incorporated (`git merge-base --is-ancestor <approved-sha> HEAD`).

### Path B: `pr` delivery mode (GitHub Pull Request + CI gate)

1. Verify the primary checkout has no merge in progress, a clean Git index, and no uncommitted local edits overlapping `<primary_branch>`.
2. Unless `state == "MERGED"` already (merged manually by the user on GitHub), merge the PR via `gh pr merge <pr-url> --merge --delete-branch`. If GitHub reports a merge conflict or branch-protection block:
   - For routine merge conflicts with `origin/<primary_branch>`, instruct the Worker to update `<task_branch>` cleanly from `origin/<primary_branch>`, re-verify locally, push, re-check CI (and pass a delta review when non-trivial), staying within the 5-round cap.
   - Otherwise leave the PR and worktree open, update `status.md` (`needs attention`), open/update `summary-<task-id>`, and escalate to the user.
3. Sync the primary checkout with `git -C "<primary_checkout>" pull --ff-only origin "<primary_branch>"` and verify `<approved-sha>` is an ancestor of `HEAD` (`git merge-base --is-ancestor <approved-sha> HEAD`).

## Update Backlog.md to Done and advance `base_sha`

After the code merge commit (or PR merge + `pull --ff-only`) succeeds:
- Use the `backlog` CLI in the primary checkout to check off acceptance criteria with evidence, write the final summary (including PR URL in `pr` mode), and move the task to `Done`.
- Commit **only** the updated task card file (`git commit --only -m "<task-id>: Done" -- "<card-path>"`) so unrelated files stay untouched and the primary checkout remains clean.
- In `pr` mode, push `<primary_branch>` (`git -C "<primary_checkout>" push origin "<primary_branch>"`) so downstream task worktrees fork from an up-to-date `origin/<primary_branch>`.
- Advance `base_sha` in `<git-common-dir>/implement-tasks/session.json` to the new primary `HEAD` (or `origin/<primary_branch>` in `pr` mode), record `merge_sha` and `done_commit_sha` in `run.json`, and immediately reassess any deferred tasks that were waiting on shared-file conflicts.
- In `local` mode, run `git push` only with separate explicit user authorization.

## Automatic post-merge cleanup

Once a task is merged and verified (either via risk-gated auto-merge or after user `approve`), automatically clean up all runtime resources for the merged task unless the user explicitly asked to keep the task's workspace/worktree open:

1. Confirm the task worktree is clean (`git -C "<worktree_path>" status --porcelain` is empty), archived evidence exists in `<git-common-dir>/implement-tasks/<task-id>/`, and the verified target commit (`reviewed_sha` when reviewed, or `submitted_sha` when `review_skipped == true`) is an ancestor of `HEAD` in the primary checkout. Never clean up unmerged or dirty worktrees without explicit user confirmation.
2. **Herdr GUI (`backend == "gui"`):**
   - Terminate and remove the task's recorded non-null terminals if still present (`hc kill <t>` then `hc rm <t>` for `worker_terminal_id`, `review_terminal_id`, `summary_terminal_id`, skipping `null` entries and ignoring `not_found`).
   - Close the task's Herdr space (`herdr-app do space.close '{"id":"<space_id>","confirmed":true}'`).
   - Remove the linked Git worktree (`git -C "<primary_checkout>" worktree remove "<worktree_path>"`).
   - Delete the merged local task branch safely (`git -C "<primary_checkout>" branch -d "<task_branch>"`, never `-D`; in `pr` mode, `--delete-branch` already handles the remote branch).
3. **Herdr TUI (`backend == "tui"`):**
   - Verify `workspace_id` against `herdr worktree list --cwd "<primary_checkout>"`.
   - Remove the workspace and worktree via `herdr worktree remove --workspace "<workspace_id>"`.
   - Delete the merged local task branch safely (`git -C "<primary_checkout>" branch -d "<task_branch>"`, never `-D`).
4. Never use `--force` on `git worktree remove` or `-D` on `git branch`. If any cleanup step fails, preserve the checkout and report its exact state.
5. Refresh `<git-common-dir>/implement-tasks/status.md` and redraw the Runner's **Status Pane** with the per-task outcome, PR link (in `pr` mode), destination merge commit SHA, card `Done` commit SHA, verification results, cleanup status, and clickable links to the durable `summary.md` and archived artifacts.
