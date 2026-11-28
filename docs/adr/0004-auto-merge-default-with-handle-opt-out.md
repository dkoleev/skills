---
status: accepted
---

# Risk-Gated Auto-Merge with Project Rules and `--handle` Opt-Out

Requiring manual per-task approval after every passing review forces the user to micromanage routine tasks, whereas blindly auto-merging every passing task removes human oversight on risky, sensitive, or partially verified changes. We make **risk-gated auto-merge** plus automatic cleanup the default after a passing review (`pass`), governed by per-project rules in `<repo-root>/.agents/implement-tasks-auto-merge.md` (with protocol and template in `references/auto-merge-rules.md`) and a joint Runner + Reviewer Approval Gate, while providing `--handle` to pause every passing task for manual `approve`.

## Considered Options

- **Manual approval always required:** Maximizes pre-merge inspection, but creates friction on routine tasks and stalls queued tasks waiting on shared files.
- **Unconditional auto-merge (with `--handle` opt-out):** Maximizes throughput, but integrates architectural, security, migration, or verification-gapped changes without human sign-off.
- **Store project auto-merge rules inside the installed skill folder:** Ties rules to the skill directory, causing `npx skills update` to overwrite them and global skill installs to leak rules across unrelated repositories.
- **Risk-gated auto-merge with project-owned `.agents/implement-tasks-auto-merge.md` + `--handle` opt-out:** Auto-merges only routine, verified changes that satisfy explicit repository rules and reviewer `approval=auto`, keeps rules versioned inside each target repository, and governs integration across both local and PR delivery pathways.

## Consequences

- When `.agents/implement-tasks-auto-merge.md` is missing or unfilled in default mode, the Runner warns the user and offers to analyze the repository to draft the rules, write user-provided rules, or fall back safely to manual `approve` for that run — never auto-merging unconfigured projects silently.
- Before any auto-merge deletes a worktree or closes a Herdr space/workspace, the Runner must archive `summary.md`, `review-state.json`, and referenced artifacts into `<git-common-dir>/implement-tasks/<task-id>/` so evidence links in the **Status Pane** survive cleanup.
- Tasks flagged `approval=human`, `escalated` reviews, failed merges, and `--handle` runs preserve their worktree, open the adjacent-tab **Summary Pane** (`summary-<task-id>`), and wait for `approve <task-id>`.
- In local delivery mode, `git push` always remains explicit-only; in PR delivery mode ([ADR-0007](0007-pr-delivery-mode-and-ci-gate.md)), remote PR publishing, GitHub Actions CI gating, and primary branch updates are authorized under the Approval Gate.
