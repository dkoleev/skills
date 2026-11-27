# Multi-Harness Routing, Permissions, and Guardrails

## Supported harnesses and launch matrix

Discover the Runner's own harness with `hc get "$HC_TERMINAL_ID" --json` (Herdr GUI) or `herdr agent get "$HERDR_PANE_ID"` (Herdr TUI), and inspect installed harness CLIs (`codex`, `claude`, `agy`, `kimi`, `opencode`, `gemini`, `cursor`, `copilot`, `grok`, `pi`, and others).

- In **Herdr GUI**, launch via `argv` in `herdr-app do space.new` / `pane.split` (see Windows PowerShell wrapper below when `.ps1` shims or user profile env vars are needed).
- In **Herdr TUI**, pass native CLI flags after `--` in `herdr agent start <name> --kind <kind> --pane <pane-id> -- <args...>`.

| Harness (`--kind`) | Auto-approve / full permissions | Model & reasoning effort flags | Live catalog / stats check | Runtime & Herdr notes |
| :--- | :--- | :--- | :--- | :--- |
| `codex` | `--dangerously-bypass-approvals-and-sandbox` (or `--approve-for-me` if repo uses Codex rules) | `-m <model> -c "model_reasoning_effort=<low\|medium\|high>"` | `codex debug models` | **Herdr GUI (`hc`) requires `--no-daemon`** or Codex commands run outside `hc`. Windows may require PowerShell / `.ps1` shim launch. |
| `claude` | `--dangerously-skip-permissions` | `--model <model> --effort <low\|medium\|high\|xhigh\|max>` | Built-in aliases (`haiku`, `sonnet`, `opus`) or custom endpoint IDs; `claude --help` | If the project docs specify a custom endpoint (e.g., z.ai GLM Coding Plan `glm-5.3-flash`, `glm-5.3`, `glm-5.4`), use those documented model IDs instead of `haiku`/`sonnet`/`opus`. Windows may require PowerShell / `.ps1` shim launch. |
| `agy` | `--dangerously-skip-permissions` | `--model <model> --effort <low\|medium\|high\|xhigh\|max>` | `agy models` | Native binary. **Herdr caveat:** `agy` can show `idle` while background tasks/subagents continue — always gate on completion line, token, and SHA. |
| `kimi` | `--auto` | `-m <model>` (no CLI `--effort` flag; send `/effort <level>` + `Enter` after `idle` if needed) | `kimi provider list` / `config.toml` aliases | Native binary. |
| `opencode` | `--auto` | None in interactive mode (omit model/effort flags unless configured) | `opencode models`; `opencode stats` | Windows may require PowerShell / `.ps1` shim launch. |
| Other `herdr` kinds (`gemini`, `grok`, `cursor`, etc.) | Check `<kind> --help` for equivalent non-interactive/auto flag | Check `<kind> --help`; omit unsupported flags cleanly | `<kind> --help` | `grok` shares the `agy` Herdr caveat where `idle` does not prove background work finished. |

Never hardcode stale model names in prompts or scripts. Inspect live model catalogs or project-documented model tables at run time and only interpolate validated values into launch commands. If a harness does not support `--model` or `--effort` in interactive CLI mode, omit the unsupported flag and rely on that harness's configured default.

## Harness pool, complexity routing, and subscription limits

1. **Determine the allowed harness pool:** Read any harness preferences, role assignments (for example, `worker=codex, reviewer=claude`), model mappings, or subscription/quota priorities from the launch prompt, `<repo-root>/.agents/implement-tasks-auto-merge.md` (`## Harness Pool & Routing`), `AGENTS.md`, or `CLAUDE.md`. If none are specified, default the pool to the Runner's own active harness so unauthenticated or unconfigured CLIs are never launched blindly.
2. **Select model and effort by complexity — never inherit the Runner's model:**
   - **Mechanical** (boilerplate, renames, small localized edits, docs/config): fast/economical model at `low` reasoning effort.
   - **Typical** (standard features, bug fixes, tests, single-module refactors): fast general-purpose model at `medium` reasoning effort.
   - **High-risk / architectural** (ambiguous requirements, concurrency, data migrations, security/auth, cross-cutting refactors): strongest available model at `high` reasoning effort.
   Assess Worker and Reviewer risk independently (when a Reviewer is launched) and record the chosen harness, model, and effort in the Run Record and `summary.md`.
3. **Balance and respect subscription limits:**
   - Check available local usage clues when supported (for example `opencode stats --days 0 --models`) alongside explicit budget hints from the user (for example, conserving a primary subscription for high-risk tasks or reviews).
   - Spread concurrent work across enabled harnesses in the pool when multiple subscriptions are available instead of exhausting a single provider unnecessarily.
4. **Reactive failover on rate limits or quota exhaustion:**
   - If `hc read` / `herdr agent read` reveals a rate-limit, usage-cap, or exhausted-subscription error on a Worker or Reviewer, mark that `(harness, model-tier)` throttled for the remainder of the run.
   - Route new dispatches to another enabled harness/tier in the pool.
   - If an in-flight Worker or Reviewer stalls on quota exhaustion, respawn that role in the same task worktree using an alternative harness/model from the pool, passing the existing branch, current `HEAD`, and `<worktree>/.implement-tasks/<task-id>/review-state.json` so completed work and round counts are preserved. Report to the user if no alternative harness remains.

## Windows launch and `.ps1` npm-shim fallback

On Windows, `codex`, `claude`, and `opencode` are commonly installed as npm `.ps1` shims or wrapped by user PowerShell `$PROFILE` settings (such as clearing or setting `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`).

- **In Herdr GUI (`herdr-app do space.new` / `pane.split`):** pass `argv` through PowerShell **without** `-NoProfile`, e.g.:
  ```json
  ["powershell", "-NoLogo", "-Command", "codex -m <model> -c 'model_reasoning_effort=\"medium\"' --dangerously-bypass-approvals-and-sandbox --no-daemon"]
  ```
  (Use `pwsh` if preferred, or `powershell`.) Launching via PowerShell loads `$PROFILE` first, resolves `.ps1` shims cleanly, and starts the agent interactively inside `hc`.
- **In Herdr TUI (`herdr agent start`):** if `herdr agent start` times out on a PowerShell function or `.ps1` shim, inspect the pane first. If at an interactive PowerShell prompt and `<kind>.ps1` exists, launch directly via `herdr pane run`:
  ```powershell
  $scriptPath = (Get-Command "$kind.ps1" -CommandType ExternalScript -ErrorAction Stop).Source
  $launch = "& `"$scriptPath`" $($validatedArgs -join ' ')"
  herdr pane run $targetPane $launch
  ```
  Wait until `herdr agent get $targetPane` detects the expected agent kind, then assign its name with `herdr agent rename $targetPane $agentName`. Prompt the agent only after it becomes ready.

## Mandatory prompt guardrails

Because Workers and Reviewers are launched with auto-approve and maximum permissions (no interactive approval prompts or OS sandbox), **every** Worker and Reviewer prompt MUST include these non-negotiable guardrails:

1. **Worktree boundary:** Read and modify project files ONLY inside `<worktreePath>` (plus `<worktreePath>/.implement-tasks/<task-id>/` for ephemeral logs, screenshots, and `review-state.json`). Never modify the primary checkout, `Backlog.md` tracker files in the primary checkout or worktree, or any sibling worktree.
2. **Git safety:** Never run `git push`, `git worktree remove`, `git branch -D` on branches you do not own, or destructive history rewrites on shared branches during implementation or review. Commit only inside `<worktreePath>` on `<taskBranch>`. In `pr` delivery mode, pushing `HEAD:<taskBranch>` and running `gh pr create`/`gh pr edit` is permitted **only** for the Worker **after** receiving the Runner's explicit post-review `SHIP_PR` message carrying `$ship_token` (never push `<primary_branch>` or force-push shared branches).
3. **Herdr boundary:** Never close, kill, rename, move, or prompt Herdr spaces, workspaces, tabs, terminals, or panes (`hc kill`, `hc rm`, `herdr-app do space.close/tab.close/pane.close`, `herdr workspace/pane/tab close`, `herdr worktree remove`) other than messaging your assigned peer and the Runner (when reporting completion/escalation).
4. **Host safety:** Never install global packages, alter user/system configs outside `<worktreePath>`, kill unrelated processes, or touch files outside `<worktreePath>` unless explicitly instructed by a verified project test script.
