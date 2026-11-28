# Herdr Dispatch, Status Pane, Review Loop, Summary Pane, and Recovery

## Select backend and prepare shared state

Detect the Orchestration Backend from the current session environment:

- **Herdr GUI (primary):** `HC_TERMINAL_ID` is set. Use `herdr-app` for window layout (`space.new`, `tab.new`, `pane.split`, `pane.rename`, `space.close`) and `hc` for terminal lifecycle and messaging (`run`, `ls`, `get`, `read`, `send`, `keys`, `wait`, `kill`, `rm`). Verify `herdr-app ls` and `hc ls --json` succeed before dispatching. Never fall back to `herdr` TUI commands inside Herdr GUI.
- **Herdr TUI (fallback):** `HC_TERMINAL_ID` is unset and `HERDR_ENV=1`. Use `herdr` CLI (`herdr worktree`, `herdr tab`, `herdr pane`, `herdr agent`).

Discover the primary checkout root (`git rev-parse --show-toplevel`), current branch, resolved `delivery_mode` (`"local"` or `"pr"`), pinned `baseSha` (`git rev-parse HEAD` after any `In Progress` card commit in `local` mode, or `git rev-parse "origin/$primary_branch"` after `git fetch` in `pr` mode), and absolute Git common directory:

```sh
git_common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
```

Ensure `.implement-tasks/` is listed in `"$git_common_dir/info/exclude"` (create `info/` if missing, append `.implement-tasks/` once). Using `info/exclude` keeps ephemeral worktree files untracked across all linked worktrees without touching the project's committed `.gitignore`.

Store durable Runner state, session state (`session.json`, `status.md`), Run Records (`run.json`), `summary.md`, and archived artifacts in:

```text
<git-common-dir>/implement-tasks/
<git-common-dir>/implement-tasks/<task-id>/
```

Store ephemeral Worker/Reviewer runtime files inside each task worktree in:

```text
<worktreePath>/.implement-tasks/<task-id>/
```

---

## Runner Status Pane (`status.md`)

Persist session-level state in `<git-common-dir>/implement-tasks/session.json` storing: `backend` (`"gui"` | `"tui"`), `delivery_mode` (`"local"` | `"pr"`), `mode` (`"auto"` | `"handle"`), `review_mode` (`"default"` | `"no-review"`), `rules_file`, `rules_configured` (`true` | `false`), `primary_checkout`, `primary_branch`, `base_sha`, `status_pane_id`, `status_terminal_id`, and `throttled_harnesses`.

When at least one eligible or resumable task exists for the run, open or reuse the Runner's Status Pane without stealing focus:

- **Herdr GUI (`backend == "gui"`):**
  1. Check whether `status_terminal_id` in `session.json` is still alive (`hc get "$status_terminal_id" --json`).
  2. Otherwise locate the Runner's pane ID from `herdr-app ls` (matching `$HC_TERMINAL_ID`) and split right (`direction: "right"`, or `"down"` if the Runner pane is too narrow) with an interactive shell (`["powershell", "-NoLogo"]` on Windows, `["sh"]` on POSIX). Note: `pane.split` inherits the target pane's folder and does not accept a `folder` argument; on Windows PowerShell, invoke `herdr-app do ...` without capturing stdout into a pipeline variable to avoid Rust `os error 232` pipe-close panics:
     ```sh
     herdr-app do pane.split '{"direction":"right","pane":"<runner_pane_id>","argv":[...]}'
     ```
  3. Read `status_pane_id` (`pane`) and `status_terminal_id` (`terminal`) from the JSON response, rename via `herdr-app do pane.rename '{"pane":"<status_pane_id>","name":"implement-tasks-status"}'`, and save both IDs in `session.json`.
  4. Redraw by sending a single self-terminating render command with `hc send "$status_terminal_id" "<clear-and-render-cmd>"`.
- **Herdr TUI (`backend == "tui"`):**
  1. Check whether `status_pane_id` in `session.json` still exists (`herdr pane get "$status_pane_id"`).
  2. Otherwise inspect `herdr pane layout --current`, split `--current --direction right --cwd "$repo_root" --no-focus` (or `--direction down` if narrow), rename via `herdr pane rename "$status_pane" "implement-tasks-status"`, and save `status_pane_id` in `session.json`.
  3. Redraw via `herdr pane run "$status_pane" "<clear-and-render-cmd>"`.

If the user manually closes the Status Pane later, do not fail the run — keep updating `<git-common-dir>/implement-tasks/status.md` cleanly.

Use **event-driven redraws** (never spawn a background `watch` loop): whenever queue or task state changes (dispatch, `ready`, `review skipped`, review started, correction round increment, `pr_open`, `ci_running`/`ci_failed`/`ci_passed`, quota failover, `pass`, `awaiting approval`, `escalated`, `blocked`, merged & cleaned, `needs attention`), rewrite `<git-common-dir>/implement-tasks/status.md` and run a single self-terminating clear + render command (`glow "<status_path>"` -> `bat --paging=never --language=markdown "<status_path>"` -> `cat` on POSIX or `Clear-Host; Get-Content -Raw` on PowerShell; avoid `glow -p` because `-p` opens an interactive pager that blocks the shell). Before the first render of a run, probe the viewers in that order (`command -v` on POSIX, `Get-Command` on PowerShell) and use the first one found for every redraw; fall back to plain output only when neither `glow` nor `bat` is installed.

`status.md` covers the **current invocation only**. When a new invocation opens the Status Pane, write `status.md` from scratch instead of editing the previous file, and never carry over tasks finished in earlier invocations. Their history stays in `<git-common-dir>/implement-tasks/<task-id>/summary.md` and `run.json`.

Include in `status.md`:
- **Header:** delivery mode (`local` | `pr`), integration mode (`risk-gated auto-merge` + rules file status, or `--handle`), review mode (`default (auto-skip trivial)` or `--no-review`), primary branch, current pinned `base_sha`, active concurrency slots (`X/10`), last updated timestamp, and active/throttled harnesses in the pool.
- **Queue Status Table:** `Task ID | Phase / Status | Harness / Model | Round | SHA | PR / CI | Notes / Next Action` (show `skipped (trivial)` or `skipped (--no-review)` in `Round` when review was skipped).
- **Awaiting Human Approval (`approve <task-id>`):** each `awaiting approval` task with its Approval Gate reason, PR link and `ci_status` (in `pr` mode), `summary-<task-id>` tab reference, archived `summary.md` link, and exact command (`approve <task-id>` or `approve all`).
- **Completed & Auto-Merged:** for each task merged during this invocation (whose workspace/worktree was cleaned up), list task ID, review status (`reviewed` vs `review skipped: trivial` / `--no-review`), PR URL (if `pr` mode), merge commit SHA, `Done` commit SHA, concise summary of changes, verification results/gaps, and clickable absolute paths / `file://` links to its archived `summary.md`, screenshots, clips, and logs inside `<git-common-dir>/implement-tasks/<task-id>/`.
- **Needs Attention / Skipped & Deferred:** unresolved `escalated` or failed-CI/failed-merge tasks with exact blockers, plus skipped/deferred tasks with reasons.

---

## Herdr GUI backend (`hc` + `herdr-app`)

### Create the worktree and start the Worker

1. Resolve the worktree checkout root from `$HERDR_APP_HOME/settings.json` (default `~/.config/herdr-app/settings.json`), reading `worktrees.directory` (default `~/.herdr/worktrees`). Place the task checkout at `<worktrees_dir>/<repo_name>/<branch_slug>` (replacing `/` with `-`, e.g. `tasks-task-12` or `task-12` matching project conventions). If a non-absolute path is configured, resolve `~` against home and verify the result is absolute.
2. Create the branch and linked worktree from the pinned `$base_sha`:
   ```sh
   git -C "$repo_root" worktree add -b "$task_branch" "$worktree_path" "$base_sha"
   ```
   Use a stable branch name such as `tasks/task-12` (lowercased/slugified task ID). If the worktree already exists on `$task_branch`, reconcile its Run Record rather than creating a duplicate.
3. Open a Herdr GUI space in `$worktree_path` without stealing focus (`"focus": false`), launching the Worker interactively with validated `argv` per [harness routing](harnesses.md):
   ```sh
   herdr-app do space.new '{"name":"<task-id>","folder":"<worktree_path>","tab":"<task-id>","argv":[...],"focus":false}'
   ```
   Read `space_id` (`space`), `tab_id` (`tab`), `worker_pane_id` (`pane`), and `worker_terminal_id` (`terminal`) from the JSON response and confirm via `herdr-app ls`.
4. Wait for the Worker to become `idle`, then deliver `$worker_prompt` safely:
   - Wait via `hc wait "$worker_terminal_id"` or poll `hc get "$worker_terminal_id" --json` until `status.state == "idle"`. If `status.state == "blocked"` on a workspace trust prompt (such as `agy` asking `"Trust this folder?"`), confirm it with `hc keys "$worker_terminal_id" enter` and keep waiting for `idle` (abort if `state == "finished"` or `status.state == "error"`, or another unexpected block).
   - If the Worker harness needs an interactive post-start command (such as `kimi` `/effort <level>`), send it first and wait for `idle` again.
   - Send the prompt with `hc send --if idle "$worker_terminal_id" "$worker_prompt"`. On `status_mismatch`, wait for `idle` and retry.
   - Verify delivery via `hc get "$worker_terminal_id" --json`: if `status.state` remains `idle` after several seconds, inspect `hc read --lines 40 "$worker_terminal_id"` first (never double-paste if the prompt is already in the buffer) and press Enter with `hc keys "$worker_terminal_id" enter` only if the text is sitting unsent in the input box.
   - For slow commands or waiting on Workers, use `hc wait` (`hc wait "$worker_terminal_id"` or `hc wait --children any`) rather than `sleep` loops.

Include in `$worker_prompt`:
- Absolute `$worktree_path`, `$task_branch`, `$base_sha`, and `$impl_token`
- Full task description, acceptance criteria, and absolute paths to relevant spec/doc files in the primary checkout
- Project rules and context pointers from `AGENTS.md` / `CLAUDE.md` (conflict surfaces, shared-resource locks, topic `.claude/rules/*.md` paths, test/screenshot commands), plus pointers to `GLOSSARY.md`, `docs/adr/`, `.agents/skills/tdd/SKILL.md` (red-before-green tests strictly at public module seams), and `.agents/skills/pr/SKILL.md` (when present in the repo)
- Ephemeral artifact directory: `$worktree_path/.implement-tasks/$task_id/`
- Runner terminal handle (`$runner_terminal_id`, i.e., `$HC_TERMINAL_ID`) and Reviewer handle once started
- The **Mandatory prompt guardrails** from [harness routing](harnesses.md#mandatory-prompt-guardrails)
- Required final completion line contract

Wait for the Worker's final `ready` report with matching task ID and `$impl_token`. Treat progress updates, intermediate commits, or a settled pane state (`idle`/`done`, especially for `agy` and `grok`) as still in progress. Verify that `git -C "$worktree_path" rev-parse HEAD` matches the reported SHA and `git -C "$worktree_path" status --porcelain` is clean (if the Worker could not commit due to a local hook/restriction, inspect and commit in `$worktree_path` as Runner before starting review).

### Evaluate Review Gate & split Reviewer pane in Herdr GUI

After verifying the Worker's final `ready` report (token, clean worktree, matching `HEAD` SHA), inspect `git -C "$worktree_path" diff "$base_sha...$submitted_sha"` and evaluate the **Review Gate** per [auto-merge-rules.md](auto-merge-rules.md):

- **If `--no-review` is set OR the verified diff satisfies the trivial-task skip criteria:** Do **not** split a Reviewer pane. Record `review_skipped: true`, `review_skip_reason` (`"no-review-flag"` or `"trivial: <reason>"`), keep `review_pane_id`, `review_terminal_id`, `reviewer_*`, and `reviewed_sha` as `null`, update `status.md`, evaluate `approval=auto|human` directly on `submitted_sha`, and proceed straight to **Publish PR and verify GitHub Actions** (in `pr` mode) or **Archive evidence and open the Summary Pane** (in `local` mode).
- **Otherwise:** Split the Worker pane right in the same tab and worktree without stealing focus:

```sh
herdr-app do pane.split '{"direction":"right","pane":"<worker_pane_id>","argv":[...]}'
```

Note: `pane.split` uses the target pane's folder when omitted (and rejects `folder` if passed). On Windows PowerShell, invoke `herdr-app do ...` without assigning stdout to a PowerShell pipeline variable (avoids Rust `os error 232` pipe-close panics). Read `review_pane_id` (`pane`) and `review_terminal_id` (`terminal`) from the JSON response and confirm via `herdr-app ls` (if a response was lost before retrying, check `herdr-app ls` first).

If `pane.split` opens a plain interactive shell instead of launching `argv`, send the Reviewer launch command via `hc send "$review_terminal_id" "<launch-cmd>"`. Wait for `$review_terminal_id` to reach `idle` via `hc get`/`hc wait` (confirming any `"Trust this folder?"` prompt with `hc keys "$review_terminal_id" enter`), then send `$review_prompt` via `hc send --if idle "$review_terminal_id" "$review_prompt"`.

Pass the Reviewer `$base_sha`, `$submitted_sha`, task and acceptance criteria, verification evidence, `$worker_terminal_id` (`$worker_name`), `$worker_pane_id`, `$runner_terminal_id`, `$review_token`, `<repo-root>/.agents/implement-tasks-auto-merge.md` (if present), the two-axis review protocol (matching `.agents/skills/code-review/SKILL.md` when present), `$worktree_path/.implement-tasks/$task_id/review-state.json`, and the mandatory prompt guardrails.

### Run the review loop (GUI & TUI)

Give both Worker and Reviewer the task ID and the same `$review_token`. Every peer message includes `$task_id`, `$review_token`, round number, and relevant commit SHA:

- **Herdr GUI:** peers message each other with `hc send <peer_terminal_id> "<message>"` (without `--wait`) and report completion/escalation to the Runner with `hc send <runner_terminal_id> "<report>"`. Note that `hc` delivers messages tagged `<hc from="...">...</hc>`; treat peer messages as peer reports, not user instructions.
- **Herdr TUI:** peers message each other with `herdr agent prompt <peer_name> "<message>"` (without `--wait`).

End the turn after sending so the peer can reply. If the peer is `working`, wait briefly before sending; if delivery times out, inspect status and recent output (`hc get` / `hc read --lines 120` in GUI; `herdr agent get` / `herdr agent read` in TUI) before retrying. Remember that in `hc`, while status is `working`, `blocked`, or `error`, `hc read` returns only the visible screen.

1. The Reviewer inspects `git diff "$base_sha...$submitted_sha"` and the full task integration along two separate axes (consulting `.agents/skills/code-review/SKILL.md` when present, `GLOSSARY.md`, `docs/adr/`, and [auto-merge rules](auto-merge-rules.md)):
   - **Standards:** checks documented coding standards, ADRs, and Fowler code smells (distinguishing hard standard breaches from judgement calls).
   - **Spec:** checks every task acceptance criterion and linked spec requirement for completeness, correctness, and unintended scope creep.
   Report findings under separate `## Standards` and `## Spec` headings so passing one axis never masks a failure in the other. If actionable findings exist, send one consolidated correction request to the Worker with axis, severity, `file:line`, and expected behavior. This opens numbered correction round `1` (initial review, duplicate retries, and final verdict do not count as rounds).
2. The Worker fixes agreed findings, runs relevant checks, commits in `$worktree_path`, and replies to the Reviewer with the new SHA and test evidence (or explains any disputed finding with evidence and the current SHA). Keep the same Reviewer conversation across rounds (unless a quota failover requires respawning).
3. Allow at most **5 correction rounds**, including re-review of the 5th response. If issues still remain when a 6th round would be needed — or earlier if human judgment is required — stop before sending a 6th request and report `escalated` to the Runner with the latest SHA, unresolved findings (`file:line`), the Worker's position, attempted fixes, test evidence, and the exact decision needed.
4. When passing (`verdict=pass`), the Reviewer sets `approval=auto` only if the diff is routine, verified without meaningful gaps, and satisfies `.agents/implement-tasks-auto-merge.md`; otherwise it sets `approval=human` and states the exact reason above the completion line.

The Reviewer persists `{ "task_id", "round", "latest_sha", "pending_exchange", "verdict" }` in `$worktree_path/.implement-tasks/$task_id/review-state.json` so restarts never reset the 5-round cap.

### Publish PR and verify GitHub Actions (`pr` delivery mode)

When `delivery_mode == "pr"`, once a task reaches `verdict=pass` (or verified `ready` with `review_skipped == true`):

1. Runner generates a fresh `$ship_token`, records `ship_token` and `phase: "publishing_pr"` in `run.json`, and sends the Worker:
   `SHIP_PR task=<task-id> token=<ship-token> base=<primary_branch>`
   instructing it to push `git push -u origin HEAD:<task_branch>`, open (or update if a PR already exists for `<task_branch>`) a GitHub PR via `gh pr create --base <primary_branch> --head <task_branch>` using `.agents/skills/pr/SKILL.md` (when present) and `GLOSSARY.md` terms, and reply with:
   `IMPLEMENT_TASKS_REPORT task=<task-id> token=<ship-token> role=worker verdict=pr_open sha=<head-sha> pr=<pr-url> approval=none`
2. Runner parses `pr_url`, resolves `pr_number` (`gh pr view <pr-url> --json number,headRefOid`), verifies `headRefOid` matches the approved commit SHA, stores `pr_url`, `pr_number`, and `ci_status: "running"` in `run.json`, and updates `status.md`.
3. Runner monitors PR checks via `gh pr checks <pr-url> --watch` (handling zero configured checks cleanly as `ci_status: "no-checks"`).
   - **If checks pass (`ci_status: "pass"` or `"no-checks"`):** proceed to **Archive evidence and open the Summary Pane**.
   - **If any check fails (`ci_status: "fail"`):** extract failing run logs (`gh run list --branch <task_branch> --limit 5 --json databaseId,conclusion` + `gh run view <run-id> --log-failed`), feed the failure logs back to the Worker in `<worktree_path>` to fix, commit, re-verify locally, and push `<task_branch>` (after a quick delta check with Reviewer for non-trivial code fixes when review ran, staying within the 5-round cap). If the 5-round cap is reached or CI keeps failing on environment/infrastructure issues, treat as `needs attention` / `approval=human` and open `summary-<task-id>`.

### Archive evidence and open the Summary Pane (GUI)

On `pass` (and finished CI check in `pr` mode), `escalated`, OR verified `ready` with `review_skipped == true` (verified via completion line, token, and SHA), **always archive before any auto-merge or worktree removal**:

1. Copy `$worktree_path/.implement-tasks/$task_id/review-state.json` (when review ran) and only artifacts explicitly listed in the reports (validating each source path resolves inside `$worktree_path`) into `<git-common-dir>/implement-tasks/<task-id>/artifacts/`.
2. Write `<git-common-dir>/implement-tasks/<task-id>/summary.md` containing:
   - Task ID, title, verdict (`PASS`, `READY (REVIEW SKIPPED)`, or `ESCALATED`), and Approval Gate result (`auto` or `human`)
   - Delivery mode (`local` or `pr`), PR URL + `ci_status` (when `pr` mode), branch, `base..reviewed` SHA (or `base..submitted` SHA when review was skipped), Worker and Reviewer (if launched) harnesses/models/efforts used, and total correction rounds (or `Review skipped (<review_skip_reason>)`)
   - **Why approval is needed** (included whenever `--handle`, `approval=human`, `escalated`, CI failure, or merge failure applies — citing matched rules, sensitive paths, verification gaps, or Runner/Reviewer reasoning)
   - Concise summary of what changed and key touched files
   - Checks/tests executed (local and GitHub Actions in `pr` mode), outcomes, and any verification gaps
   - Review findings resolved across `Standards` and `Spec` (or `Review skipped (<review_skip_reason>)`; and, if `ESCALATED`, the unresolved issues, Worker position, and decision required)
   - Clickable absolute paths / `file://` links to archived screenshots, clips, logs, and reports inside `<git-common-dir>/implement-tasks/<task-id>/`
3. **If auto-merge eligible** (`verdict=pass` with `approval=auto` from both Runner and Reviewer, OR verified `ready` with `review_skipped == true` and `approval=auto` from Runner; project rules configured and satisfied; zero verification gaps; green/no-checks CI in `pr` mode; and not `--handle`): Proceed directly to [integration](integration.md) to merge, verify/sync, commit `Done`, clean up the task's space/terminals/worktree/branch, advance `base_sha`, and publish the merge summary + archived artifact links in the Runner's **Status Pane** (`status.md`). Skip opening the Summary Pane tab when the workspace is auto-cleaned.
4. **Whenever human approval or intervention is required** (`--handle`, `approval=human`, unconfigured rules safe fallback, `escalated`, CI failure, or merge failure/conflict):
   - Check whether `summary_terminal_id` in `run.json` is still alive (`hc get "$summary_terminal_id" --json`). If it is live, re-render the updated `summary.md` in that existing tab/pane instead of creating a duplicate tab.
   - Otherwise, open the **Summary Pane** in a dedicated adjacent tab inside `$space_id` without stealing focus so `summary.md` renders at full width beside the Worker/Reviewer tab:
     ```sh
     herdr-app do tab.new '{"space":"<space_id>","name":"summary-<task-id>","folder":"<worktree_path>","argv":[...],"focus":false}'
     ```
     Note: on Windows PowerShell, invoke `herdr-app do ...` without assigning stdout to a pipeline variable (avoids Rust `os error 232` pipe-close panics), and confirm via `herdr-app ls` if a response is lost before retrying. Launch the best available Markdown viewer inside `argv` so the pane stays open and readable without external installs:
     - Prefer `glow "<summary_path>"` if `glow` is installed (avoid `glow -p`, which opens an interactive pager), else `bat --paging=never --language=markdown "<summary_path>"` if `bat` is installed, else print the file directly and keep the shell open (`["powershell", "-NoExit", "-NoLogo", "-Command", "Get-Content -Raw '<summary_path>'"]` on Windows, or `["sh", "-lc", "cat '<summary_path>'; exec sh"]` on POSIX).
   - Read `summary_tab_id` (`tab`), `summary_pane_id` (`pane`), and `summary_terminal_id` (`terminal`) from the JSON response.
   - Rename the pane to match the tab: `herdr-app do pane.rename '{"pane":"<summary_pane_id>","name":"summary-<task-id>"}'`.
   - Save `summary_tab_id`, `summary_pane_id`, `summary_terminal_id`, `approval_gate`, and `approval_reason` in `run.json`, refresh `status.md`, redraw the Runner's **Status Pane**, and notify the user explicitly in Runner chat (`TASK-12` needs `approve TASK-12` + reason + PR link if `pr` mode + `summary-TASK-12`).

---

## Herdr TUI fallback (`herdr`)

When `HC_TERMINAL_ID` is unset and `HERDR_ENV=1`, use `herdr` CLI with `--no-focus` and `--cwd "$repo_root"`:

- Create worktree and root pane:
  ```sh
  herdr worktree list --cwd "$repo_root"
  herdr worktree create --cwd "$repo_root" --branch "$task_branch" --base "$base_sha" --label "$task_id" --no-focus
  ```
  If a worktree already exists on `$task_branch`, reopen with `herdr worktree open --cwd "$repo_root" --branch "$task_branch" --no-focus`.
- Start and prompt Worker/Reviewer (omit Reviewer `pane split` / `agent start` / `agent prompt` when the Review Gate yields `review_skipped == true`):
  ```sh
  herdr agent start "$worker_name" --kind "$worker_kind" --pane "$worker_pane" -- <native-flags...>
  herdr agent prompt "$worker_name" "$worker_prompt"
  # Only when review_skipped == false:
  herdr pane split --pane "$worker_pane" --direction right --cwd "$worktree_path" --no-focus
  herdr agent start "$reviewer_name" --kind "$reviewer_kind" --pane "$review_pane" -- <native-flags...>
  herdr agent prompt "$reviewer_name" "$review_prompt"
  ```
- Open Summary Pane (when staying open under `--handle`, `approval=human`, `escalated`, or merge failure): check whether `summary_pane_id` in `run.json` still exists (`herdr pane get "$summary_pane_id"`); if so, re-render `summary.md` in it. Otherwise create an adjacent tab in `$workspace_id` via `herdr tab create --workspace "$workspace_id" --cwd "$worktree_path" --label "summary-$task_id" --no-focus`, read `summary_tab_id` (`.result.tab.tab_id`) and `summary_pane_id` (`.result.root_pane.pane_id`), rename via `herdr pane rename "$summary_pane" "summary-$task_id"`, save `summary_tab_id` and `summary_pane_id` in `run.json`, and render `summary.md` via `herdr pane run "$summary_pane"` with `glow` (without `-p`) / `bat` / `cat` or `Get-Content -Raw`.
- Read agent output with `herdr agent get` and `herdr agent read <target> --source recent-unwrapped --lines 120` (fall back to `--source visible`).

---

## Receive reports and recover

Require every Worker and Reviewer report to end with a structured completion line:

```text
IMPLEMENT_TASKS_REPORT task=<task-id> token=<token> role=<worker|reviewer> verdict=<ready|pass|pr_open|blocked|escalated> sha=<commit-sha|none> approval=<auto|human|none>
```

When reporting `verdict=pr_open`, append `pr=<pr-url>` on the same completion line. Use `approval=auto` or `approval=human` when `role=reviewer` and `verdict=pass`; use `approval=none` otherwise. Use distinct `$impl_token`, `$review_token`, and `$ship_token` tokens per phase. Read agent output via `hc get` / `hc read --lines 120` (GUI) or `herdr agent get` / `herdr agent read --source recent-unwrapped --lines 120` (TUI). If output scrolled out of reach, instruct the agent to write its report inside `$worktree_path/.implement-tasks/$task_id/` and reply with the path.

Persist a JSON Run Record per task in `<git-common-dir>/implement-tasks/<task-id>/run.json` storing: `task_id`, `task_card_path`, `backend` (`"gui"` | `"tui"`), `delivery_mode` (`"local"` | `"pr"`), `primary_checkout`, `primary_branch`, `base_sha`, `task_branch`, `worktree_path`, `workspace_id`, `space_id`, `tab_id`, `worker_pane_id`, `worker_terminal_id`, `worker_name`, `worker_harness`, `worker_model`, `worker_effort`, `review_skipped` (`true` | `false`), `review_skip_reason` (`"no-review-flag"` | `"trivial: <reason>"` | `null`), `review_pane_id`, `review_terminal_id`, `reviewer_name`, `reviewer_harness`, `reviewer_model`, `reviewer_effort`, `summary_tab_id`, `summary_pane_id`, `summary_terminal_id`, `impl_token`, `review_token`, `ship_token`, `phase`, `submitted_sha`, `reviewed_sha`, `pr_url`, `pr_number`, `ci_status` (`"pending"` | `"running"` | `"pass"` | `"fail"` | `"no-checks"` | `null`), `approval_gate`, `approval_reason`, `merge_sha`, and `done_commit_sha`. When `review_skipped` is `true`, Reviewer fields and `reviewed_sha` stay `null`, and integration/PR publishing targets `submitted_sha`.

For structured routing, also record `worker_family` and `reviewer_family` when known. Confirm the actual launch before recording it as active, and refresh these fields when replacing an assignment.

On restart, reconcile `<git-common-dir>/implement-tasks/session.json`, per-task `<git-common-dir>/implement-tasks/<task-id>/run.json`, Git worktree state, `gh pr view` (when `pr_url` is set), and `herdr-app ls` / `hc ls --json` (GUI) or `herdr agent list` / `herdr pane list` (TUI). Never claim an existing worktree automatically if no Run Record establishes ownership; report it to the user as an existing unowned checkout.
