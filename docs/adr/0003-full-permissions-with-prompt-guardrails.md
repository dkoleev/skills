---
status: accepted
---

# Full Permissions with Prompt Guardrails and Verified Local Integration

Interactive tool-approval prompts stall parallel Workers and Reviewers across separate Herdr panes, defeating autonomous multi-task execution. We launch all Workers and Reviewers with auto-approve and maximum permissions (`--dangerously-bypass-approvals-and-sandbox`, `--dangerously-skip-permissions`, or `--auto`), while constraining behavior through mandatory prompt-level boundary guardrails, verified local merge gates, and explicit-only `git push`.

## Considered Options

- **Default interactive approvals per harness:** Causes frequent `blocked` stalls across up to 10 concurrent worktrees and blocks peer-to-peer review rounds.
- **Maximum permissions with prompt guardrails and verified local integration:** Enables uninterrupted execution inside isolated worktrees while preventing unapproved edits to the primary checkout, tracker state, or remote repository.

## Consequences

- Every Worker and Reviewer prompt must include explicit boundary guardrails (stay inside `<worktreePath>`, never touch the primary checkout or `Backlog.md`, never run `git push`, never alter foreign Herdr spaces, workspaces, terminals, or panes).
- Integration into the primary branch always verifies a clean reviewed worktree and passing combined checks before committing and updating `Backlog.md` `Done`. Closing or discarding unmerged work and running `git push` always require separate explicit user authorization.
