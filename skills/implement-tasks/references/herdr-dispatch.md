# Herdr Dispatch, Review Loop, Summary Pane, and Recovery

## Prepare shared state and exclude rule

Verify `HERDR_ENV=1`. Discover the primary checkout root (`git rev-parse --show-toplevel`), current branch, pinned `baseSha` (`git rev-parse HEAD`), and absolute Git common directory:

```sh
git_common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
```

Ensure `.implement-tasks/` is listed in "$git_common_dir/info/exclude" (create `info/` if missing, append `.implement-tasks/` once). Using `info/exclude` keeps ephemeral worktree files untracked across all linked worktrees without touching the project's committed `.gitignore`.

Store durable Runner state, reports, `summary.md`, and archived artifacts in:

```text
<git-common-dir>/implement-tasks/<task-id>/
```

Store ephemeral Worker/Reviewer runtime files inside each task worktree in:

```text
<worktreePath>/.implement-tasks/<task-id>/
```

## Create the worktree and start agents

Use `--no-focus` on layout and worktree creation commands so user focus stays untouched. Always pass the absolute primary checkout path (`--cwd "$repo_root"`).

```sh
herdr worktree list --cwd "$repo_root"
herdr worktree create --cwd "$repo_root" --branch "$task_branch" --base "$base_sha" --label "$task_id" --no-focus
```

Use a stable branch name such as `tasks/task-12` (lowercased/slugified task ID). Read `worktree_path` from `.result.worktree.path`, `workspace_id` from `.result.workspace.workspace_id`, and `worker_pane` from `.result.root_pane.pane_id`. Validate branch, checkout path, and base commit with Git before dispatching work.

If a worktree already exists on `$task_branch` (including after a `create` timeout), inspect and recover the prior run rather than creating a duplicate. Use `herdr worktree open --cwd "$repo_root" --branch "$task_branch" --no-focus` to reopen an existing managed worktree whose Herdr workspace was closed.

Choose unique agent names such as `impl-task-12` and `review-task-12`, checking `herdr agent list` for collisions. Select the Worker's `--kind`, model, effort, and auto-approve flags per [harness routing](harnesses.md), then launch and prompt:

```sh
herdr agent start "$worker_name" --kind "$worker_kind" --pane "$worker_pane" -- <native-flags...>
herdr agent prompt "$worker_name" "$worker_prompt"
```

Include in `$worker_prompt`:
- Absolute `$worktree_path`, `$task_branch`, `$base_sha`, and `$impl_token`
- Full task description, acceptance criteria, and absolute paths to relevant spec/doc files in the primary checkout
- Project rules from `AGENTS.md` / `CLAUDE.md` (conflict surfaces, shared-resource locks, test/screenshot commands)
- Ephemeral artifact directory: `$worktree_path/.implement-tasks/$task_id/`
- Expected Reviewer Herdr name (`$reviewer_name`)
- The **Mandatory prompt guardrails** from [harness routing](harnesses.md#mandatory-prompt-guardrails)
- Required final completion line contract

Wait for the Worker's final `ready` report with matching task ID and `$impl_token`. Treat progress updates, intermediate commits, or a settled pane state (`idle`/`done`, especially for `agy` and `grok`) as still in progress. Verify that `git -C "$worktree_path" rev-parse HEAD` matches the reported SHA and `git -C "$worktree_path" status --porcelain` is clean (if the Worker could not commit due to a local hook/restriction, inspect and commit in `$worktree_path` as Runner before starting review).

Split the Worker pane right to start the Reviewer in the same tab and worktree:

```sh
herdr pane split --pane "$worker_pane" --direction right --cwd "$worktree_path" --no-focus
```

Read `review_pane` from `.result.pane.pane_id` and confirm it shares the Worker's tab and worktree. Before retrying a split whose response was lost, inspect `herdr pane layout --pane "$worker_pane"`. Start the Reviewer using its selected `--kind`, model, effort, and auto-approve flags:

```sh
herdr agent start "$reviewer_name" --kind "$reviewer_kind" --pane "$review_pane" -- <native-flags...>
herdr agent prompt "$reviewer_name" "$review_prompt"
```

Pass the Reviewer `$base_sha`, `$submitted_sha`, task and acceptance criteria, verification evidence, `$worker_name` and `$worker_pane`, `$review_token`, the review-loop protocol, `$worktree_path/.implement-tasks/$task_id/review-state.json`, and the mandatory prompt guardrails.

## Run the review loop

Give both Worker and Reviewer the task ID and the same `$review_token`. Every peer message includes `$task_id`, `$review_token`, round number, and relevant commit SHA. Send directly with `herdr agent prompt <peer> <message>` (without `--wait`) when the peer is `idle` or `done`, then end the turn so the peer can reply. If the peer is `working`, wait briefly before sending; if delivery times out, inspect `herdr agent get` and `herdr agent read` before retrying.

1. The Reviewer inspects `git diff "$base_sha...$submitted_sha"` and the full task integration against repo standards and acceptance criteria. If actionable findings exist, it sends one consolidated correction request to `$worker_name` with severity, `file:line`, and expected behavior. This opens numbered correction round `1` (initial review, duplicate retries, and final verdict do not count as rounds).
2. The Worker fixes agreed findings, runs relevant checks, commits in `$worktree_path`, and replies to `$reviewer_name` with the new SHA and test evidence (or explains any disputed finding with evidence and the current SHA). Keep the same Reviewer conversation across rounds (unless a quota failover requires respawning).
3. Allow at most **5 correction rounds**, including re-review of the 5th response. If issues still remain when a 6th round would be needed — or earlier if human judgment is required — stop before sending a 6th request and report `escalated` to the Runner with the latest SHA, unresolved findings (`file:line`), the Worker's position, attempted fixes, test evidence, and the exact decision needed.

The Reviewer persists `{ "task_id", "round", "latest_sha", "pending_exchange", "verdict" }` in `$worktree_path/.implement-tasks/$task_id/review-state.json` so restarts never reset the 5-round cap.

## Archive evidence and open the Summary Pane

On `pass` or `escalated` (verified via completion line, `$review_token`, and SHA):

1. Copy `$worktree_path/.implement-tasks/$task_id/review-state.json` and only artifacts explicitly listed in the reports (validating each source path resolves inside `$worktree_path`) into `<git-common-dir>/implement-tasks/<task-id>/artifacts/`.
2. Write `<git-common-dir>/implement-tasks/<task-id>/summary.md` containing:
   - Task ID, title, and verdict (`PASS` or `ESCALATED`)
   - Branch, `base..reviewed` SHA, Worker and Reviewer harnesses/models/efforts used, and total correction rounds
   - Concise summary of what changed and key touched files
   - Checks/tests executed, outcomes, and any verification gaps
   - Review findings resolved (and, if `ESCALATED`, the unresolved issues, Worker position, and decision required)
   - Clickable absolute paths / `file://` links to archived screenshots, clips, logs, and reports inside `<git-common-dir>/implement-tasks/<task-id>/`
3. Open a third pane in the same task tab beside the Worker and Reviewer (reuse `summary_pane_id` from the Run Record if recovering):
   - Inspect `herdr pane layout --pane "$review_pane"`. Split `--direction right` when width allows 3 readable columns, otherwise `--direction down`, preserving `--cwd "$worktree_path" --no-focus`.
   - Read `summary_pane` from `.result.pane.pane_id`, rename it with `herdr pane rename "$summary_pane" "summary-$task_id"`, and save `summary_pane_id` in the Run Record.
4. Render `summary.md` inside `$summary_pane` using the best available terminal viewer without requiring external installs:
   - Prefer `glow -p "$summary_path"` if `glow` is installed, else `bat --paging=never --language=markdown "$summary_path"` if `bat` is installed, else print the file directly (`cat "$summary_path"` on POSIX or `Get-Content -Raw "$summary_path"` on PowerShell) so `summary.md` is immediately readable in the pane.

## Receive reports and recover

Require every Worker and Reviewer report to end with a structured completion line:

```text
IMPLEMENT_TASKS_REPORT task=<task-id> token=<token> role=<worker|reviewer> verdict=<ready|pass|blocked|escalated> sha=<commit-sha|none>
```

Use a distinct `$impl_token` for implementation and a separate `$review_token` for the review loop. Read agent output with `herdr agent get` and `herdr agent read <target> --source recent-unwrapped --lines 120` (fall back to `--source visible` if alternate-screen scrolling is unavailable). If output scrolled out of reach, instruct the agent to write its report inside `$worktree_path/.implement-tasks/$task_id/` and reply with the path.

Persist a JSON Run Record per task in `<git-common-dir>/implement-tasks/<task-id>/run.json` storing: `task_id`, `primary_checkout`, `primary_branch`, `base_sha`, `task_branch`, `worktree_path`, `workspace_id`, `worker_pane_id`, `worker_name`, `worker_harness`, `worker_model`, `worker_effort`, `review_pane_id`, `reviewer_name`, `reviewer_harness`, `reviewer_model`, `reviewer_effort`, `summary_pane_id`, `impl_token`, `review_token`, `phase`, `submitted_sha`, and `reviewed_sha`.

On restart, reconcile `<git-common-dir>/implement-tasks/<task-id>/run.json`, Git worktree state, and `herdr agent list` / `herdr pane list`. Never claim an existing worktree automatically if no Run Record establishes ownership; report it to the user as an existing unowned checkout.
