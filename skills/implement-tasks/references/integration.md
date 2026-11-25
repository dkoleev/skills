# Integration, Approval Gate, Auto-Merge, and Cleanup

## Integration modes

- **Risk-gated auto-merge (default):** Evaluates the [Approval Gate](auto-merge-rules.md) after a verified `pass` review OR after a verified Worker `ready` report when review was skipped (trivial-task skip or `--no-review`). Only when project rules in `<repo-root>/.agents/implement-tasks-auto-merge.md` are configured and satisfied, verification has no meaningful gaps, and `approval=auto` holds (from both Runner and Reviewer when reviewed, or from the Runner alone when review was skipped), the Runner automatically performs sequential local merge + combined verification, commits `Backlog.md` `Done`, cleans up the task's Herdr terminals, space/workspace, Git worktree, and merged branch, advances `base_sha` in `session.json`, reassesses deferred conflicting tasks, and updates `status.md` in the Runner's **Status Pane** with the merge commit SHA, `Done` commit SHA, verification results, and clickable links to archived `summary.md` and screenshots/artifacts.
- **Human approval (`approve` / `--handle`):** Never auto-merges when running with `--handle`, when `.agents/implement-tasks-auto-merge.md` is missing/unfilled, when `approval=human` (from Reviewer or Runner), when `escalated`/`blocked`, or when merge/verification fails. Instead, the task remains `In Progress` (`awaiting approval`) with its worktree and **Summary Pane** (`summary-<task-id>`) open, and the Runner asks the user for `approve <task-id>` in chat and in **Status Pane**.
- **Accepted approval commands:** `approve <task-id>` (for example `approve TASK-12`), `approve all` (authorizes all currently `awaiting approval` tasks at their verified target commit: `reviewed_sha` when reviewed, or `submitted_sha` when `review_skipped == true`), and synonym `merge <task-id>` authorize sequential merge, combined verification, committing `Done`, and automatic cleanup unless the user explicitly asks to keep the workspace open. Handle close-only requests for unmerged work separately and confirm whether the branch or any uncommitted changes should be preserved.
- **`git push` rule (all modes):** Never run `git push` automatically in any mode. Pushing to a remote always requires separate explicit user authorization.

## Pre-merge verification

For every task entering integration (automatically via `approval=auto`, or on `approve <task-id>` / `approve all` / `merge <task-id>`), read its Run Record (`<git-common-dir>/implement-tasks/<task-id>/run.json`) and `backlog instructions task-finalization`. Verify that:
- The destination matches the recorded `primary_checkout` and `primary_branch`.
- The worktree belongs to the task and its branch and `HEAD` still match the verified target commit (`reviewed_sha` when reviewed, or `submitted_sha` when `review_skipped == true`).
- The task worktree is clean and archived evidence (`summary.md`, listed artifacts, and `review-state.json` when review ran) already exists in `<git-common-dir>/implement-tasks/<task-id>/`.

If the task commit changed since verified completion, re-evaluate the Review Gate (and re-run peer review if required) and obtain fresh user `approve` if required before integrating.

## Merge and verify sequentially

1. Verify the primary checkout has no merge in progress, a clean Git index, and no local edits overlapping incoming files. Distinguish ordinary uncommitted `Backlog.md` metadata changes from code changes under test, keeping pre-existing edits outside the merge.
2. Prepare the merge using the repository's merge convention (for standard merges: `git merge --no-ff --no-commit <approved-sha>`) and run the relevant combined verification checks **before** committing.
3. **Failure handling:** If merging introduces conflicts, overlaps uncommitted primary edits, or fails combined verification checks, run `git merge --abort`, preserve the task worktree and pre-existing primary edits, open the task's **Summary Pane** (`summary-<task-id>`) if not already open, update `status.md` (`needs attention`) and redraw the Runner's **Status Pane**, and do not mark `Done`. Routine merge conflicts may be reconciled inside the task worktree followed by a fresh review pass (or fresh diff/verification check when `--no-review` or when the reconciled diff still satisfies trivial-skip rules); non-trivial conflicts or combined-test failures escalate to the user.
4. Commit the merge and verify `<approved-sha>` is incorporated (`git merge-base --is-ancestor <approved-sha> HEAD`).

## Update Backlog.md to Done and advance `base_sha`

After the code merge commit succeeds:
- Use the `backlog` CLI in the primary checkout to check off acceptance criteria with evidence, write the final summary, and move the task to `Done`.
- Commit **only** the updated task card file (`git commit --only -m "<task-id>: Done" -- "<card-path>"`) so unrelated files stay untouched and the primary checkout remains clean.
- Advance `base_sha` in `<git-common-dir>/implement-tasks/session.json` to the new primary `HEAD`, record `merge_sha` and `done_commit_sha` in `run.json`, and immediately reassess any deferred tasks that were waiting on shared-file conflicts.
- Run `git push` only with separate explicit user authorization.

## Automatic post-merge cleanup

Once a task is merged and verified (either via risk-gated auto-merge or after user `approve`), automatically clean up all runtime resources for the merged task unless the user explicitly asked to keep the task's workspace/worktree open:

1. Confirm the task worktree is clean (`git -C "<worktree_path>" status --porcelain` is empty), archived evidence exists in `<git-common-dir>/implement-tasks/<task-id>/`, and the verified target commit (`reviewed_sha` when reviewed, or `submitted_sha` when `review_skipped == true`) is an ancestor of `HEAD` in the primary checkout. Never clean up unmerged or dirty worktrees without explicit user confirmation.
2. **Herdr GUI (`backend == "gui"`):**
   - Terminate and remove the task's recorded non-null terminals if still present (`hc kill <t>` then `hc rm <t>` for `worker_terminal_id`, `review_terminal_id`, `summary_terminal_id`, skipping `null` entries and ignoring `not_found`).
   - Close the task's Herdr space (`herdr-app do space.close '{"id":"<space_id>","confirmed":true}'`).
   - Remove the linked Git worktree (`git -C "<primary_checkout>" worktree remove "<worktree_path>"`).
   - Delete the merged task branch safely (`git -C "<primary_checkout>" branch -d "<task_branch>"`, never `-D`).
3. **Herdr TUI (`backend == "tui"`):**
   - Verify `workspace_id` against `herdr worktree list --cwd "<primary_checkout>"`.
   - Remove the workspace and worktree via `herdr worktree remove --workspace "<workspace_id>"`.
   - Delete the merged task branch safely (`git -C "<primary_checkout>" branch -d "<task_branch>"`, never `-D`).
4. Never use `--force` on `git worktree remove` or `-D` on `git branch`. If any cleanup step fails, preserve the checkout and report its exact state.
5. Refresh `<git-common-dir>/implement-tasks/status.md` and redraw the Runner's **Status Pane** with the per-task outcome, destination merge commit SHA, card `Done` commit SHA, verification results, cleanup status, and clickable links to the durable `summary.md` and archived artifacts.
