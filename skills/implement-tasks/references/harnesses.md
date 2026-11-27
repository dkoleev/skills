# Multi-Harness Routing, Permissions, and Guardrails

## Supported harnesses and launch matrix

Discover the Runner's own harness with `hc get "$HC_TERMINAL_ID" --json` (Herdr GUI) or `herdr agent get "$HERDR_PANE_ID"` (Herdr TUI), and inspect installed harness CLIs (`codex`, `claude`, `agy`, `kimi`, `opencode`, `crush`, `gemini`, `cursor`, `copilot`, `grok`, `pi`, and others).

- In **Herdr GUI**, launch via `argv` in `herdr-app do space.new` / `pane.split` (see Windows PowerShell wrapper below when `.ps1` shims or user profile env vars are needed).
- In **Herdr TUI**, pass native CLI flags after `--` in `herdr agent start <name> --kind <kind> --pane <pane-id> -- <args...>`.

| Harness (`--kind`) | Auto-approve / full permissions | Model & reasoning effort flags | Live catalog / stats check | Runtime & Herdr notes |
| :--- | :--- | :--- | :--- | :--- |
| `codex` | `--dangerously-bypass-approvals-and-sandbox` (or `--approve-for-me` if repo uses Codex rules) | `-m <model> -c "model_reasoning_effort=<effort>"` | `codex debug models` (`supported_reasoning_levels` lists each model's efforts) | **Herdr GUI (`hc`) requires `--no-daemon`** or Codex commands run outside `hc`. Windows may require PowerShell / `.ps1` shim launch. |
| `claude` | `--dangerously-skip-permissions` | `--model <model> --effort <low\|medium\|high\|xhigh\|max>` | Built-in aliases (`haiku`, `sonnet`, `opus`) or custom endpoint IDs; `claude --help` | If the project docs specify a custom endpoint (e.g., z.ai GLM Coding Plan `glm-5.3-flash`, `glm-5.3`, `glm-5.4`), use those documented model IDs instead of `haiku`/`sonnet`/`opus`. Windows may require PowerShell / `.ps1` shim launch. |
| `agy` | `--dangerously-skip-permissions` | `--model <base model> --effort <effort>`; a model rejects efforts it lacks, and a suffixed variant ID such as `gemini-4-neon-high` conflicts with any other `--effort` | `agy models` (one row per effort variant; the editor merges them into base models) | Native binary. **Herdr caveat:** `agy` can show `idle` while background tasks/subagents continue — always gate on completion line, token, and SHA. |
| `kimi` | `--auto` | `-m <model>` (no CLI `--effort` flag; send `/effort <level>` + `Enter` after `idle` if needed) | `kimi provider list` / `config.toml` aliases | Native binary. |
| `opencode` | `--auto` | None in interactive mode (omit model/effort flags unless configured) | `opencode models`; `opencode stats` | Windows may require PowerShell / `.ps1` shim launch. |
| `crush` | `-y` | Use the configured default or choose **Switch Model** and the supported reasoning effort in the interactive UI before sending the task. Verify the selection in the pane. | `crush models`; `crush stats` | In GUI, launch through `argv`. Choose **Nope** if Crush offers to initialize the project, then wait for the input prompt. In TUI, check `herdr agent start --help` for `crush` before marking the Harness available. Windows may require PowerShell / `.ps1` shim launch. |
| Other `herdr` kinds (`gemini`, `grok`, `cursor`, etc.) | Check `<kind> --help` for equivalent non-interactive/auto flag | Check `<kind> --help`; omit unsupported flags cleanly | `<kind> --help` | `grok` shares the `agy` Herdr caveat where `idle` does not prove background work finished. |

Never hardcode stale model names in prompts or scripts. Inspect live model catalogs or project-documented model tables at run time and only interpolate validated values into launch commands. If a harness does not support `--model` or `--effort` in interactive CLI mode, omit the unsupported flag and rely on that harness's configured default.

## Structured project routing

From the primary checkout, run `python "<implement-tasks skill directory>/scripts/routing.py" rules` once before selecting new work. The command reads `.agents/implement-tasks-routing.json`. JSON `null` selects the existing [prose workflow](#harness-pool-complexity-routing-and-subscription-limits). If Python is unavailable and the file is absent, use the prose workflow directly. Report malformed or unreadable settings and keep new work queued until they can be read.

Compare the task's title, description, and acceptance criteria with each rule's `description`. Pass the matching 1-based positions to `python "<implement-tasks skill directory>/scripts/routing.py" select --role worker --matches <positions>`. For the Reviewer use `--role reviewer` and the same matching positions. Leave `--matches` empty when no descriptions apply. The command applies role eligibility within the first matching rule. Use `assignment` when `status` is `selected`. When `status` is `queued`, display its `reason` in the Status Pane and leave the task queued. If Worker work already exists, keep its worktree and evidence and defer review until an eligible assignment exists.

Treat the assignment's `harness`, `model`, and `effort` as data and pass them as separate launch arguments using the [launch matrix](#supported-harnesses-and-launch-matrix). A saved custom model ID is a valid explicit choice. A pool entry's `efforts` list, when present, comes from the live catalog and names the efforts that model accepts. When `model` is JSON `null`, omit the model flag and record the Harness default. For `default` effort, omit the effort flag. If the Harness cannot apply an explicit model through a supported launch or interactive selection, explain the reason and retain the queue entry. Use the actual assignment in the role's `*_harness`, `*_model`, and `*_effort` fields in the Run Record. For a Harness that only supports its default effort, record `default`.

Apply `launch_notes.project` and `launch_notes.harnesses[assignment.harness]` when present. They describe project launch conventions, such as the PowerShell profile or a custom endpoint. Keep the selected assignment and mandatory prompt guardrails in force.

### Runtime restrictions and capacity

For each structured `select`, pass `--runtime` and send a JSON object on stdin. Map an explicit launch restriction such as `codex only` to `allowed_harnesses`. Use `allowed_models` for a restriction on specific Harness/model pairs. Store restrictions in the invocation or Session Record for its lifetime, including retries. A new invocation reads the full project configuration with only its own restrictions.

```json
{
  "allowed_harnesses": ["codex"],
  "harnesses": {"codex": {"active": 1, "capacity": 2}},
  "models": [{"harness": "codex", "model": "custom-id", "active": 1, "quota_remaining": 1}]
}
```

Read active assignments from Run Records and confirm their terminal state in the Orchestration Backend. Count reserved or starting assignments and live work across roles. Supply `active` for each Harness and model in use. Include `capacity`, `quota_remaining`, and `available` when known from local usage clues, enabled Harnesses, launch capabilities, or user limits. An observed throttle sets `quota_remaining` to `0` for the affected Harness or model for the remainder of the invocation. Missing limits leave capacity or quota unknown. `allowed_models` takes a list of `{ "harness": ..., "model": ... }` pairs, using JSON `null` for a Harness default.

Resolve and reserve assignments one at a time in the Runner. Persist the assignment and `phase=starting` in the Run Record before spawning, and count that reservation in the next selection. Advance the record when launch succeeds, or release the reservation on failure. For a structured assignment failure or quota failover, refresh runtime data and select again from the same first matching rule. Keep the task queued with the reported reason if no candidate remains. For an in-flight task, retain its branch, worktree, evidence, and review round.

### Reviewer selection

For structured routing, give `select --role reviewer` the same matching rule positions and runtime restrictions. Include `worker` in the runtime object with the actual `harness`, `model`, and `family` from the Run Record, using JSON `null` for an unresolved Harness default or unknown family. New Reviewers always start in a fresh terminal and session, including fallback Reviewers using the same Harness or model as the Worker.

When the saved preference is enabled, selection ranks a different Harness and known family first, then a different known family. When either family is unknown, a different Harness ranks ahead of the final fallback to any available independent Reviewer. Role, restrictions, availability, and quota always apply. Use the same capacity selection as for Workers within each preference level. Record the actual chosen Harness, model, effort, and known family in the Run Record.

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

On Windows, `codex`, `claude`, `opencode`, and `crush` may be installed as npm `.ps1` shims or wrapped by user PowerShell `$PROFILE` settings (such as clearing or setting `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`).

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
