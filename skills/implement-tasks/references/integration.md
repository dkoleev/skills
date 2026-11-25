# Approval and Integration

For each task the user explicitly approves for integration, read its Run Record (`<git-common-dir>/implement-tasks/<task-id>/run.json`) and `backlog instructions task-finalization`. Verify that:
- The destination matches the recorded `primary_checkout` and `primary_branch`.
- The worktree belongs to the task and its branch and `HEAD` still match the reported, passing `reviewed_sha`.
- The task worktree is clean and archived evidence (`summary.md` and listed artifacts) exists in `<git-common-dir>/implement-tasks/<task-id>/`.

If the task commit changed since the passing review, re-run review and obtain fresh user approval before integrating. Handle close-only requests for unmerged work separately and confirm whether the branch or any uncommitted changes should be preserved.

## Merge and verify sequentially

1. Verify the primary checkout has no merge in progress, a clean Git index, and no local edits overlapping incoming files. Distinguish ordinary uncommitted `Backlog.md` metadata changes from code changes under test, keeping pre-existing edits outside the merge.
2. Prepare the merge using the repository's merge convention (for standard merges: `git merge --no-ff --no-commit <approved-sha>`) and run the relevant verification checks against the combined state **before** committing.
3. If merging introduces conflicts or test failures, preserve the task worktree and pre-existing primary edits. Resolve conflicts in the task worktree if needed, then repeat review and obtain approval for the resulting SHA.
4. Commit the merge and verify `<approved-sha>` is incorporated (`git merge-base --is-ancestor <approved-sha> HEAD`).

## Update Backlog.md to Done

After the code merge commit succeeds:
- Use the `backlog` CLI in the primary checkout to check off acceptance criteria with evidence, write the final summary, and move the task to `Done`.
- Commit **only** the updated task card file (`git commit --only -m "<task-id>: Done" -- "<card-path>"`) so unrelated files stay untouched and the primary checkout remains clean.
- Run `git push` only with separate explicit user authorization.

## Automatic post-merge cleanup

Unless the user explicitly asked to keep the task's workspace/worktree open, automatically clean up all runtime resources for the merged task:

1. Confirm the task worktree is clean (`git -C "<worktree_path>" status --porcelain` is empty) and `<reviewed_sha>` is an ancestor of `HEAD` in the primary checkout. Never clean up unmerged or dirty worktrees without explicit user confirmation.
2. **Herdr GUI (`backend == "gui"`):**
   - Terminate and remove the task's recorded terminals if still present (`hc kill <t>` then `hc rm <t>` for `worker_terminal_id`, `review_terminal_id`, `summary_terminal_id`, ignoring `not_found`).
   - Close the task's Herdr space (`herdr-app do space.close '{"id":"<space_id>","confirmed":true}'`).
   - Remove the linked Git worktree (`git -C "<primary_checkout>" worktree remove "<worktree_path>"`).
   - Delete the merged task branch safely (`git -C "<primary_checkout>" branch -d "<task_branch>"`, never `-D`).
3. **Herdr TUI (`backend == "tui"`):**
   - Verify `workspace_id` against `herdr worktree list --cwd "<primary_checkout>"`.
   - Remove the workspace and worktree via `herdr worktree remove --workspace "<workspace_id>"`.
   - Delete the merged task branch safely (`git -C "<primary_checkout>" branch -d "<task_branch>"`, never `-D`).
4. Never use `--force` on `git worktree remove` or `-D` on `git branch`. If any cleanup step fails, preserve the checkout and report its exact state.

End with the per-task outcome, destination merge commit SHA, card `Done` commit SHA, verification results, cleanup status, and links to the durable `summary.md` and archived artifacts.
