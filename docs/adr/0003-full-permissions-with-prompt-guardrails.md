---
status: accepted
---

# Full Permissions with Prompt Guardrails and Human-Gated Merge

Interactive tool-approval prompts stall parallel Workers and Reviewers across separate Herdr panes, defeating autonomous multi-task execution. We launch all Workers and Reviewers with auto-approve and maximum permissions (`--dangerously-bypass-approvals-and-sandbox`, `--dangerously-skip-permissions`, or `--auto`), while constraining behavior through mandatory prompt-level boundary guardrails and a strict human-approval gate before any branch is merged or pushed.

## Considered Options

- **Default interactive approvals per harness:** Causes frequent `blocked` stalls across up to 10 concurrent worktrees and blocks peer-to-peer review rounds.
- **Maximum permissions with prompt guardrails and human-gated integration:** Enables uninterrupted execution inside isolated worktrees while preventing unapproved changes to the primary checkout, tracker state, or remote repository.

## Consequences

- Every Worker and Reviewer prompt must include explicit boundary guardrails (stay inside `<worktreePath>`, never touch the primary checkout or `Backlog.md`, never run `git push`, never alter foreign Herdr spaces, workspaces, terminals, or panes).
- Explicit per-task user merge approval tied to a verified commit SHA authorizes sequential merge, committing `Backlog.md` `Done`, and automatic cleanup of the merged task's Herdr space/terminals, Git worktree, and merged branch (unless the user explicitly asks to keep them open). Closing or discarding unmerged work and running `git push` still require separate explicit user authorization.
