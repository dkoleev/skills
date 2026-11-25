# skills

Reusable, cross-harness agent skills by [dkoleev](https://github.com/dkoleev), structured for automatic discovery by [skills.sh](https://skills.sh/) and compatible with Codex, Claude Code, Antigravity, Kimi Code, OpenCode, and other coding-agent harnesses.

## Installation

Install all skills from this repository via the `skills` CLI:

```bash
npx skills add dkoleev/skills
```

Or install a single skill:

```bash
npx skills add dkoleev/skills --skill implement-tasks
```

## Skills Catalog

| Skill | What it does | Core requirements | Guide |
| :--- | :--- | :--- | :--- |
| [`implement-tasks`](skills/implement-tasks/SKILL.md) | Dispatches `Backlog.md` `To Do` tasks into isolated Git worktrees via Herdr GUI (`hc` + `herdr-app`) or Herdr TUI (`herdr`), runs multi-harness peer-to-peer review, shows live progress in a Runner Status Pane, and applies risk-gated local auto-merge by default (requesting `approve` for risky changes, or all tasks with `--handle`). | [Herdr](https://herdr.dev/), [Backlog.md](https://github.com/MrLesk/Backlog.md), [Git](https://git-scm.com/), 1+ supported harness CLI | [Jump to guide](#implement-tasks) |

---

## Skill Guides

### `implement-tasks`

Orchestrates an entire implementation queue from your primary Git checkout inside **Herdr GUI** (`HC_TERMINAL_ID`, via `herdr-app` + `hc`) or **Herdr TUI** (`HERDR_ENV=1`, via `herdr`):

- **Parallel worktree queue:** Picks ready `To Do` tasks from `Backlog.md` (and resumes existing `In Progress` runs with a Run Record), commits `In Progress` in the primary checkout before creating each worktree (rolling back to `To Do` if setup fails before prompt delivery), skips blocked dependencies, parent grouping tickets, owner-only cards, and overlapping shared-file conflicts, and runs up to **10** independent tasks concurrently in isolated Git worktrees.
- **Live Runner Status Pane (`implement-tasks-status`):** Opens a Markdown status pane right beside the Runner (`<git-common-dir>/implement-tasks/status.md`) displaying real-time queue progress, active phases, harnesses/models, tasks awaiting `approve`, completed merge SHAs, summaries, and clickable links to archived screenshots and reports.
- **Cross-harness routing & quota failover:** The Runner picks the harness, model, and reasoning effort per Worker and Reviewer based on task complexity (`mechanical`, `typical`, `high-risk/architectural`), project-documented pools/model tables, and available subscription capacity — supporting mixed pairs (for example, Codex Worker + Claude Reviewer) and reactive failover if a subscription hits rate limits.
- **Full-permission execution with guardrails:** Launches Workers and Reviewers with auto-approve / maximum permissions while enforcing worktree, tracker, Git-push, and Herdr boundary guardrails in every prompt (using `--no-daemon` for `codex` in Herdr GUI and launching through `powershell -NoLogo` on Windows to preserve `$PROFILE` env vars and `.ps1` npm shims).
- **Independent peer-to-peer review loop:** Opens a fresh Reviewer beside the Worker and lets them iterate directly for up to **5 correction rounds** before escalating unresolved disputes to you.
- **Risk-gated auto-merge & onboarding (or `--handle` for all manual):** Evaluates each passing review against your project's `.agents/implement-tasks-auto-merge.md` rules and the Reviewer's `approval=auto|human` assessment. If `.agents/implement-tasks-auto-merge.md` is missing or unfilled, the Runner warns you and offers to analyze the repo and draft the rules, take your rules directly, or fall back safely to manual `approve`. Routine verified changes merge sequentially (`--no-ff --no-commit`), pass combined checks, commit `Backlog.md` `Done`, clean up their Herdr terminals/space/worktree/branch, advance `baseSha`, and report in the **Status Pane** (never running `git push` automatically). Risky, sensitive-path, or unverified changes (and all tasks under `--handle`) pause with an open task-tab **Summary Pane** (`summary-<task-id>`) until you reply `approve <task-id>`.

#### How to use `implement-tasks`

1. **Prepare tasks:** Move ready tasks to `To Do` in `Backlog.md`. Optionally document repo-specific conflict surfaces, shared-resource locks (such as a single local database or device), owner-only card rules (such as `project: owner`), test/screenshot expectations, custom model/endpoint tables, and preferred harness pools in your project's `AGENTS.md` or `CLAUDE.md`.
2. **Configure auto-merge rules (once per project):** Define which changes may auto-merge vs require human `approve` in `.agents/implement-tasks-auto-merge.md` (or let the Runner analyze the project and generate a draft on first run).
3. **Start in Herdr:** Open your repository's primary checkout inside a Herdr GUI (`HC_TERMINAL_ID`) or Herdr TUI (`HERDR_ENV=1`) session using your preferred coding-agent harness.
4. **Invoke explicitly:** Run `implement-tasks` (or `/implement-tasks` / `$implement-tasks` depending on your harness). By default it applies risk-gated auto-merge; pass `--handle` when you want to require `approve` for every task:
   - *"Use implement-tasks on TASK-12 and TASK-15. Prefer Codex for workers, Claude for review, and conserve Claude quota for high-risk tasks."*
   - *"Use implement-tasks --handle"*
5. **Watch Status Pane & approve gated tasks:** Track active tasks and merged summaries in `implement-tasks-status` beside the Runner. When a task requires approval (or in `--handle` mode), inspect its `summary-<task-id>` pane and run `approve TASK-12` (or `approve all` / `merge TASK-12`). `git push` always stays manual across all modes.

#### Required & Supported Tools

| Tool | Role | Link |
| :--- | :--- | :--- |
| **Herdr** | Required Orchestration Backend (GUI via `hc` + `herdr-app`, or TUI via `herdr`) | [herdr.dev](https://herdr.dev/) · [GitHub](https://github.com/herdrdev/herdr) |
| **Backlog.md** | Required Task Source (`backlog` CLI for tasks, dependencies, plans, statuses) | [GitHub](https://github.com/MrLesk/Backlog.md) |
| **Git** | Worktree isolation, common-dir state storage, sequential integration | [git-scm.com](https://git-scm.com/) |
| **skills.sh** | Skill discovery and installation (`npx skills add`) | [skills.sh](https://skills.sh/) |
| **OpenAI Codex CLI** | Supported harness (`codex`) | [GitHub](https://github.com/openai/codex) · [Docs](https://learn.chatgpt.com/docs/codex/cli) |
| **Claude Code** | Supported harness (`claude`) | [Docs](https://code.claude.com/docs) |
| **Google Antigravity CLI** | Supported harness (`agy`) | [Docs](https://antigravity.google/docs/cli/overview) · [GitHub](https://github.com/google-antigravity/antigravity-cli) |
| **Kimi Code CLI** | Supported harness (`kimi`) | [Docs](https://moonshotai.github.io/kimi-code/) · [GitHub](https://github.com/MoonshotAI/kimi-code) |
| **OpenCode** | Supported harness (`opencode`) | [opencode.ai](https://opencode.ai) · [GitHub](https://github.com/anomalyco/opencode) |

> **Optional terminal Markdown viewers:** If [`glow`](https://github.com/charmbracelet/glow) or [`bat`](https://github.com/sharkdp/bat) is installed on `PATH`, both the Runner Status Pane and task Summary Panes render Markdown cleanly; otherwise they fall back to built-in terminal output.

---

## Architecture & Domain Docs

- [Domain Glossary](GLOSSARY.md) — shared terminology across skills in this repository
- [Architecture Decision Records](docs/adr/) — key design trade-offs ([ADR-0001](docs/adr/0001-herdr-as-orchestration-backend.md), [ADR-0002](docs/adr/0002-two-tier-state-and-artifact-storage.md), [ADR-0003](docs/adr/0003-full-permissions-with-prompt-guardrails.md), [ADR-0004](docs/adr/0004-auto-merge-default-with-handle-opt-out.md))
