# Approval and Integration

For each task the user explicitly approves for integration, read its Run Record (`<git-common-dir>/implement-tasks/<task-id>/run.json`) and `backlog instructions task-finalization`. Verify that:
- The destination matches the recorded `primary_checkout` and `primary_branch`.
- The worktree belongs to the task and its branch and `HEAD` still match the reported, passing `reviewed_sha`.
- The task worktree is clean and archived evidence (`summary.md` and listed artifacts) exists in `<git-common-dir>/implement-tasks/<task-id>/`.

If the task commit changed since the passing review, re-run review and obtain fresh user approval before integrating. Handle close-only requests for unmerged work separately and confirm whether the branch or any uncommitted changes should be preserved.

Merge approved commits sequentially:
1. Verify the primary checkout has no merge in progress, a clean Git index, and no local edits overlapping incoming files. Distinguish ordinary uncommitted `Backlog.md` metadata changes from code changes under test, keeping pre-existing edits outside the merge.
2. Prepare the merge using the repository's merge convention (for standard merges: `git merge --no-ff --no-commit <approved-sha>`) and run the relevant verification checks against the combined state **before** committing.
3. If merging introduces conflicts or test failures, preserve the task worktree and pre-existing primary edits. Resolve conflicts in the task worktree if needed, then repeat review and obtain approval for the resulting SHA.
4. Verify the approved commit is incorporated before reporting successful integration.

After the merge commit and combined verification succeed:
- Use the `backlog` CLI in the primary checkout to check off acceptance criteria with evidence, write the final summary, and move the task to `Done`. Keep unrelated files and tracker mutations out of the code merge commit.
- Run `git push` only with separate explicit user authorization.

When worktree cleanup is also explicitly approved:
1. Verify the saved `workspace_id` against `herdr worktree list --cwd <primary-checkout>`, confirm the worktree is clean, and confirm the reviewed commit is already merged.
2. Run `herdr worktree remove --workspace <task-workspace-id>`. Remove only that worktree through Herdr; keep `<task_branch>` unless branch deletion was explicitly authorized.
3. If removal fails, preserve the checkout and report its state rather than forcing deletion. End with the per-task outcome, destination commit SHA, verification results, and links to the durable `summary.md` and archived artifacts.
