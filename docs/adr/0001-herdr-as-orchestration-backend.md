---
status: accepted
---

# Herdr as the Orchestration Backend

Multi-harness agent orchestration requires a single control plane capable of launching different agent runtimes side by side in isolated Git worktrees, routing peer-to-peer messages, and surfacing interactive states to a human operator. We chose **Herdr** (Herdr GUI via `hc` + `herdr-app` when `HC_TERMINAL_ID` is set, or Herdr TUI via `herdr` when `HERDR_ENV=1`) as the mandatory Orchestration Backend for `implement-tasks` instead of implementing parallel orchestration through each harness's native subagent APIs.

## Considered Options

- **Herdr (`hc` + `herdr-app` GUI / `herdr` TUI):** Provides a uniform workspace/worktree/pane lifecycle across 20+ agent kinds (`codex`, `claude`, `agy`, `kimi`, `opencode`, etc.), live terminal visibility, and `blocked` state detection.
- **Native subagents per harness:** Each harness exposes incompatible delegation primitives with no cross-harness peer-to-peer review loop and no shared side-by-side pane inspection.
- **Bare `git worktree` + headless CLI processes:** Loses interactive visibility, live peer correction loops, and mid-run quota failover without building a custom supervisor daemon.

## Consequences

- `implement-tasks` cannot run outside a Herdr session (`HC_TERMINAL_ID` or `HERDR_ENV=1`).
- Supporting a new harness requires only adding its launch flags and runtime caveats rather than rewriting orchestration plumbing.
