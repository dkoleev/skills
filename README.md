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
| [`implement-tasks`](skills/implement-tasks/SKILL.md) | Dispatches `Backlog.md` `To Do` tasks into isolated Git worktrees via Herdr GUI (`hc` + `herdr-app`) or Herdr TUI (`herdr`), evaluates a post-diff Review Gate (peer-to-peer review with automatic skip for trivial diffs, or `--no-review` for all tasks), shows live progress in a Runner Status Pane, and applies risk-gated auto-merge by default across local merge and GitHub PR + CI delivery modes (requesting `approve` for risky changes, or all tasks with `--handle`). | [Herdr](https://herdr.dev/), [Backlog.md](https://github.com/MrLesk/Backlog.md), [Git](https://git-scm.com/), 1+ supported harness CLI (and [GitHub CLI](https://cli.github.com/) for PR mode) | [Jump to guide](#implement-tasks) |

---

## Companion Skills (`mattpocock/skills`)

`implement-tasks` integrates opportunistically with companion engineering skills from [`mattpocock/skills`](https://github.com/mattpocock/skills). Rather than vendoring or bundling external skills inside `dkoleev/skills` ([ADR-0006](docs/adr/0006-external-companion-skills-installation.md)), each companion skill is installed independently into target repositories via the `skills` CLI. When present under `.agents/skills/`, Workers and Reviewers adopt their specialized conventions; when absent, `implement-tasks` falls back to its built-in universal protocols.

### Lifecycle & Companion Skills Roles

| Lifecycle Phase | Skill | Role in Workflow |
| :--- | :--- | :--- |
| **Planning & Architecture** | [`codebase-design`](https://github.com/mattpocock/skills) | Guides high-level codebase design, modularization, and architectural patterns before tasks are drafted. |
| **Planning & Architecture** | [`domain-modeling`](https://github.com/mattpocock/skills) | Establishes domain models, entity boundaries, ubiquitous domain language, and domain ADRs. |
| **Planning & Architecture** | [`grill-with-docs`](https://github.com/mattpocock/skills) | Probes design trade-offs, resolves ambiguities against existing docs, and updates `GLOSSARY.md` and ADRs. |
| **Planning & Architecture** | [`to-spec`](https://github.com/mattpocock/skills) | Synthesizes architectural discussions and requirements into structured, comprehensive technical specifications. |
| **Planning & Architecture** | [`to-tickets`](https://github.com/mattpocock/skills) | Slices technical specifications into dependency-ordered, agent-ready implementation tasks in `Backlog.md`. |
| **Implementation (TDD)** | [`tdd`](https://github.com/mattpocock/skills) | Guides Workers to write red-before-green automated tests strictly at public module seams before writing implementation code. |
| **Peer Review** | [`code-review`](https://github.com/mattpocock/skills) | Powers independent two-axis peer review evaluating **Standards** (coding standards, ADRs, Fowler smells) and **Spec** (AC completeness and scope creep) separately. |
| **PR Delivery** | [`pr`](https://github.com/mattpocock/skills) | Formats clear, comprehensive GitHub Pull Request bodies with summaries, issue references, verification evidence, and domain terminology upon post-review `SHIP_PR` handoff. |
| **Retrospectives** | [`retro`](https://github.com/mattpocock/skills) | Conducts engineering retrospectives across completed task runs to extract lessons and turn recurring agent issues into automated checks and rules. |

### Installing Companion Skills

Install all companion skills into your project with a single command:

```bash
npx skills add mattpocock/skills --skill codebase-design --skill domain-modeling --skill grill-with-docs --skill to-spec --skill to-tickets --skill tdd --skill code-review --skill pr --skill retro
```

Or install individual skills as needed:

```bash
npx skills add mattpocock/skills --skill codebase-design
npx skills add mattpocock/skills --skill domain-modeling
npx skills add mattpocock/skills --skill grill-with-docs
npx skills add mattpocock/skills --skill to-spec
npx skills add mattpocock/skills --skill to-tickets
npx skills add mattpocock/skills --skill tdd
npx skills add mattpocock/skills --skill code-review
npx skills add mattpocock/skills --skill pr
npx skills add mattpocock/skills --skill retro
```

> **Note on authoring-time dependencies:** A maintainer's checkout of `dkoleev/skills` may hold local, gitignored authoring-time skills under `.agents/skills/` (such as `domain-modeling`, `grill-with-docs`, and `grilling`) used exclusively for developing and maintaining this repository itself. They are not bundled into or distributed with `skills/implement-tasks/` for downstream users.

---

## Skill Guides

### `implement-tasks`

Orchestrates an entire implementation queue from your primary Git checkout inside **Herdr GUI** (`HC_TERMINAL_ID`, via `herdr-app` + `hc`) or **Herdr TUI** (`HERDR_ENV=1`, via `herdr`):

- **Parallel worktree queue:** Picks ready `To Do` tasks from `Backlog.md` (and resumes existing `In Progress` runs with a Run Record), commits `In Progress` in the primary checkout before creating each worktree (rolling back to `To Do` if setup fails before prompt delivery), skips blocked dependencies, parent grouping tickets, owner-only cards, and overlapping shared-file conflicts, and runs up to **10** independent tasks concurrently in isolated Git worktrees.
- **Two Delivery Modes (`local` and `pr`):**
  - **Local merge (`local`, default):** Task worktrees branch from primary checkout `HEAD`, integrate sequentially via `git merge --no-ff --no-commit`, verify combined checks, commit `Backlog.md` `Done`, clean up worktree and branch, and advance `base_sha`. `git push` remains strictly manual across all tasks.
  - **PR delivery (`pr`, enabled via `--pr` or `## Delivery Mode` in `.agents/implement-tasks-auto-merge.md`):** Task worktrees branch cleanly from `origin/<primary_branch>` (`base_sha`) so local `Backlog.md` card commits stay out of task branches and parallel PRs never conflict on tracker files. `git push` is forbidden during coding and review. Only after passing the Review Gate (`verdict=pass` or trivial-skip), the Runner issues a `SHIP_PR` message with `$ship_token` to the Worker, authorizing `git push -u origin HEAD:<task_branch>` and opening/updating a GitHub PR (`gh pr create`) formatted with `.agents/skills/pr/SKILL.md` (when present) and `GLOSSARY.md` vocabulary. The Runner monitors GitHub Actions checks (`gh pr checks <pr-url> --watch`), feeds failing run logs (`gh run view --log-failed`) back to the Worker to fix and re-verify within the 5-round cap, and once CI passes merges via `gh pr merge --merge --delete-branch`, synchronizes the primary checkout (`git pull --ff-only origin <primary_branch>`), commits `Backlog.md` `Done`, and pushes `<primary_branch>` to `origin`.
- **Live Runner Status Pane (`implement-tasks-status`):** Opens a Markdown status pane right beside the Runner (`<git-common-dir>/implement-tasks/status.md`) displaying real-time queue progress, active phases, harnesses/models, PR links and CI status (in `pr` mode), tasks awaiting `approve`, completed merge SHAs, summaries, and clickable links to archived screenshots and reports.
- **Cross-harness routing & quota failover:** The Runner picks the harness, model, and reasoning effort per Worker and Reviewer based on task complexity (`mechanical`, `typical`, `high-risk/architectural`), project-documented pools/model tables, and available subscription capacity — supporting mixed pairs (for example, Codex Worker + Claude Reviewer) and reactive failover if a subscription hits rate limits.
- **Full-permission execution with guardrails:** Launches Workers and Reviewers with auto-approve / maximum permissions while enforcing worktree, tracker, Git-push, and Herdr boundary guardrails in every prompt (using `--no-daemon` for `codex` in Herdr GUI and launching through `powershell -NoLogo` on Windows to preserve `$PROFILE` env vars and `.ps1` npm shims).
- **Post-diff Review Gate & peer-to-peer review (or `--no-review`):** After a Worker finishes, the Runner evaluates the actual diff: truly trivial mechanical changes (such as typos, docs, or tiny localized config tweaks with passing checks) automatically skip launching a Reviewer (configurable via an optional `## Skip Review (Trivial Tasks)` section in `.agents/implement-tasks-auto-merge.md`), while all other tasks open a fresh Reviewer beside the Worker for up to **5 correction rounds** before escalating unresolved disputes. Pass `--no-review` to skip Reviewers for an entire run.
- **Risk-gated auto-merge & onboarding (orthogonal to `--handle` and `--no-review`):** Evaluates each verified completion (`pass` review, or review-skipped diff checked directly by the Runner, plus green GitHub Actions checks in `pr` mode) against your project's `.agents/implement-tasks-auto-merge.md` rules. If `.agents/implement-tasks-auto-merge.md` is missing or unfilled, the Runner warns you and offers to analyze the repo and draft the rules, take your rules directly, or fall back safely to manual `approve`. Routine verified changes merge automatically (`--no-ff --no-commit` in `local` mode or `gh pr merge` in `pr` mode), pass combined/CI checks, commit `Backlog.md` `Done`, clean up their Herdr terminals/space/worktree/branch, advance `base_sha`, and report in the **Status Pane**. Risky, sensitive-path, or unverified changes (and all tasks under `--handle`, including `--no-review --handle`) pause with an open task-tab **Summary Pane** (`summary-<task-id>`) until you reply `approve <task-id>`.

#### How to use `implement-tasks`

1. **Prepare tasks:** Move ready tasks to `To Do` in `Backlog.md`. Optionally document repo-specific conflict surfaces, shared-resource locks (such as a single local database or device), owner-only card rules (such as `project: owner`), test/screenshot expectations, custom model/endpoint tables, and preferred harness pools in your project's `AGENTS.md` or `CLAUDE.md`.
2. **Configure auto-merge and delivery rules (once per project):** Define delivery mode (`local` or `pr`), which changes may auto-merge vs require human `approve`, and optional `Skip Review` criteria for trivial tasks in `.agents/implement-tasks-auto-merge.md` (or let the Runner analyze the project and generate a draft on first run).
3. **Start in Herdr:** Open your repository's primary checkout inside a Herdr GUI (`HC_TERMINAL_ID`) or Herdr TUI (`HERDR_ENV=1`) session using your preferred coding-agent harness.
4. **Invoke explicitly:** Run `implement-tasks` (or `/implement-tasks` / `$implement-tasks` depending on your harness). By default it applies risk-gated auto-merge and skips review only on verified trivial mechanical diffs; pass `--handle` to require `approve` for every task, `--no-review` to skip Reviewers across the run, or `--pr` / `--local` to select delivery mode:
   - *"Use implement-tasks on TASK-12 and TASK-15. Prefer Codex for workers, Claude for review, and conserve Claude quota for high-risk tasks."*
   - *"Use implement-tasks --pr"*
   - *"Use implement-tasks --handle"*
   - *"Use implement-tasks --no-review"*
   - *"Use implement-tasks --pr --no-review --handle"*
5. **Watch Status Pane & approve gated tasks:** Track active tasks, PR links, and merged summaries in `implement-tasks-status` beside the Runner. When a task requires approval (or in `--handle` mode), inspect its `summary-<task-id>` pane and run `approve TASK-12` (or `approve all` / `merge TASK-12`). In `local` mode, `git push` remains strictly manual; in `pr` mode, pushing task branches and merging PRs follows the post-review `SHIP_PR` handoff, CI verification, and Approval Gate rules.

#### Required & Supported Tools

| Tool | Role | Link |
| :--- | :--- | :--- |
| **Herdr** | Required Orchestration Backend (GUI via `hc` + `herdr-app`, or TUI via `herdr`) | [herdr.dev](https://herdr.dev/) · [GitHub](https://github.com/herdrdev/herdr) |
| **Backlog.md** | Required Task Source (`backlog` CLI for tasks, dependencies, plans, statuses) | [GitHub](https://github.com/MrLesk/Backlog.md) |
| **Git** | Worktree isolation, common-dir state storage, sequential integration | [git-scm.com](https://git-scm.com/) |
| **GitHub CLI (`gh`)** | Required for PR delivery mode (`pr`) for PR creation, CI watching, and auto-merge | [cli.github.com](https://cli.github.com/) |
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
- [Architecture Decision Records](docs/adr/) — key design trade-offs:
  - [ADR-0001: Herdr as the Orchestration Backend](docs/adr/0001-herdr-as-orchestration-backend.md)
  - [ADR-0002: Two-Tier State and Artifact Storage](docs/adr/0002-two-tier-state-and-artifact-storage.md)
  - [ADR-0003: Full Permissions with Prompt Guardrails](docs/adr/0003-full-permissions-with-prompt-guardrails.md)
  - [ADR-0004: Risk-Gated Auto-Merge with Project Rules and `--handle` Opt-Out](docs/adr/0004-auto-merge-default-with-handle-opt-out.md)
  - [ADR-0005: Post-Diff Review Gate for Trivial Tasks and Orthogonal `--no-review` Mode](docs/adr/0005-review-gate-trivial-skip-and-no-review-mode.md)
  - [ADR-0006: External Companion Skills Installation and Opportunistic Integration](docs/adr/0006-external-companion-skills-installation.md)
  - [ADR-0007: GitHub PR Delivery Mode and Continuous Integration Gate](docs/adr/0007-pr-delivery-mode-and-ci-gate.md)
