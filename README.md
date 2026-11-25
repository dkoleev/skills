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
| [`implement-tasks`](skills/implement-tasks/SKILL.md) | Dispatches `Backlog.md` `To Do` tasks into isolated Git worktrees via Herdr GUI (`hc` + `herdr-app`) or Herdr TUI (`herdr`), runs multi-harness peer-to-peer review, opens a summary pane, and merges + cleans up on approval. | [Herdr](https://herdr.dev/), [Backlog.md](https://github.com/MrLesk/Backlog.md), [Git](https://git-scm.com/), 1+ supported harness CLI | [Jump to guide](#implement-tasks) |

---

## Skill Guides

### `implement-tasks`

Orchestrates an entire implementation queue from your primary Git checkout inside **Herdr GUI** (`HC_TERMINAL_ID`, via `herdr-app` + `hc`) or **Herdr TUI** (`HERDR_ENV=1`, via `herdr`):

- **Parallel worktree queue:** Picks ready `To Do` tasks from `Backlog.md` (and resumes existing `In Progress` runs with a Run Record), commits `In Progress` in the primary checkout before creating each worktree (rolling back to `To Do` if setup fails before prompt delivery), skips blocked dependencies, parent grouping tickets, owner-only cards, and overlapping shared-file conflicts, and runs up to **10** independent tasks concurrently in isolated Git worktrees.
- **Cross-harness routing & quota failover:** The Runner picks the harness, model, and reasoning effort per Worker and Reviewer based on task complexity (`mechanical`, `typical`, `high-risk/architectural`), project-documented pools/model tables, and available subscription capacity — supporting mixed pairs (for example, Codex Worker + Claude Reviewer) and reactive failover if a subscription hits rate limits.
- **Full-permission execution with guardrails:** Launches Workers and Reviewers with auto-approve / maximum permissions while enforcing worktree, tracker, Git-push, and Herdr boundary guardrails in every prompt (using `--no-daemon` for `codex` in Herdr GUI and launching through `powershell -NoLogo` on Windows to preserve `$PROFILE` env vars and `.ps1` npm shims).
- **Independent peer-to-peer review loop:** Opens a fresh Reviewer beside the Worker and lets them iterate directly for up to **5 correction rounds** before escalating unresolved disputes to you.
- **Summary Pane (`summary-<task-id>`):** On `pass` or `escalated`, archives evidence and opens a 3rd pane beside the Worker and Reviewer showing what changed, how it was tested, verification gaps, review verdict, and clickable links to archived screenshots/artifacts.
- **Human-gated integration & automatic cleanup:** Leaves tasks `In Progress` until you explicitly approve merging a named task and SHA, then merges sequentially (`--no-ff --no-commit`), tests the combined state, commits `Backlog.md` `Done`, and automatically cleans up the task's Herdr terminals, space/workspace, Git worktree, and merged branch (unless you ask to keep them open).

#### How to use `implement-tasks`

1. **Prepare tasks:** Move ready tasks to `To Do` in `Backlog.md`. Optionally document repo-specific conflict surfaces, shared-resource locks (such as a single local database or device), owner-only card rules (such as `project: owner`), test/screenshot expectations, custom model/endpoint tables, and preferred harness pools in your project's `AGENTS.md` or `CLAUDE.md`.
2. **Start in Herdr:** Open your repository's primary checkout inside a Herdr GUI (`HC_TERMINAL_ID`) or Herdr TUI (`HERDR_ENV=1`) session using your preferred coding-agent harness.
3. **Invoke explicitly:** Run `implement-tasks` (or `/implement-tasks` / `$implement-tasks` depending on your harness). You can narrow the run with task IDs or pass harness/quota hints:
   - *"Use implement-tasks on TASK-12 and TASK-15. Prefer Codex for workers, Claude for review, and conserve Claude quota for high-risk tasks."*
4. **Inspect the Summary Pane:** Once a task finishes review, check its `summary-<task-id>` pane (and any linked screenshots/artifacts) or resolve any `escalated` item.
5. **Authorize integration:** Explicitly tell the Runner which verified task(s) to merge (for example, *"merge TASK-12"*). The Runner merges, checks off acceptance criteria, commits `Done`, and cleans up the task's space, terminals, worktree, and merged branch.

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

> **Optional terminal Markdown viewers:** If [`glow`](https://github.com/charmbracelet/glow) or [`bat`](https://github.com/sharkdp/bat) is installed on `PATH`, the Summary Pane renders `summary.md` with formatted Markdown; otherwise it falls back cleanly to built-in terminal output.

---

## Architecture & Domain Docs

- [Domain Glossary](GLOSSARY.md) — shared terminology across skills in this repository
- [Architecture Decision Records](docs/adr/) — key design trade-offs ([ADR-0001](docs/adr/0001-herdr-as-orchestration-backend.md), [ADR-0002](docs/adr/0002-two-tier-state-and-artifact-storage.md), [ADR-0003](docs/adr/0003-full-permissions-with-prompt-guardrails.md))
