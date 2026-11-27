# Multi-Harness Agent Skills

Shared vocabulary for authoring and operating multi-harness coding-agent skills in this repository.

## Language

**Harness**:
A specific coding-agent runtime and interface (such as Codex, Claude Code, Antigravity, Kimi Code, or OpenCode) that executes prompts inside a terminal session.
_Avoid_: Agent tool, CLI wrapper, model

**Harness Pool**:
The set of **Harness** and model combinations a project makes available to its **Runner** for implementation and review.
_Avoid_: Installed harnesses, model catalog

**Routing Rule**:
A description of the tasks a rule covers, together with a list of eligible **Harness** and model combinations from the **Harness Pool**. Each candidate has its own reasoning effort for those tasks.
_Avoid_: Launch note

**Orchestration Backend**:
The workspace and terminal multiplexer layer through which a coordinator creates isolated worktrees, launches agent panes, and relays prompts across harnesses.
_Avoid_: Terminal app, multiplexer, supervisor

**Task Source**:
The system of record that holds queued tasks, statuses, dependencies, assignees, and acceptance criteria.
_Avoid_: Issue tracker, backlog tool, ticket board

**Runner**:
The coordinating agent session invoked by the user in the primary checkout to select queued tasks, choose models and harnesses, supervise progress, archive evidence, and integrate completed work.
_Avoid_: Orchestrator, manager, main agent

**Worker**:
An isolated agent instance assigned to implement and locally commit a single task inside its dedicated worktree.
_Avoid_: Implementer, coder, executor

**Reviewer**:
A fresh, independent agent instance assigned to evaluate a Worker's submitted commit against the task specification and repository standards.
_Avoid_: Verifier, QA agent, auditor

**Status Pane**:
A live pane opened beside the Runner in the primary checkout to display overall queue progress, active task phases, assigned harnesses, pending approvals, PR links and CI status in PR delivery mode, and completed-task summaries with links to archived evidence.
_Avoid_: Summary Pane, dashboard tab, log pane

**Summary Pane**:
A dedicated pane opened inside a task's tab beside the Reviewer (or beside the Worker when review was skipped) when that task stays open for human approval or escalation.
_Avoid_: Status Pane, report tab, output window

**Review Gate**:
The post-implementation checkpoint after a Worker's verified `ready` report that decides whether to launch an independent Reviewer or skip review for a trivial mechanical diff or under `--no-review`.
_Avoid_: Approval Gate, skip check, complexity check

**Approval Gate**:
The policy checkpoint after review (or after Worker verification when review is skipped), and following green PR checks in PR delivery mode, that determines whether a verified change may integrate automatically under project rules or must pause for explicit human approval.
_Avoid_: Merge check, risk flag, review gate

**Run Record**:
The durable per-task record owned by the Runner that tracks branch ownership, assigned harnesses, tokens, lifecycle phase, review status, approval decisions, and verified revisions across restarts.
_Avoid_: State file, checkpoint, metadata

**Review Loop**:
The bounded direct exchange between a Reviewer and a Worker in which findings are raised, addressed, and re-evaluated against each new commit until approval or escalation.
_Avoid_: Feedback cycle, fix loop, chat loop

**Correction Round**:
A single numbered iteration within a Review Loop consisting of one consolidated critique from the Reviewer and the Worker's corresponding response or fix commit.
_Avoid_: Turn, attempt, retry

**Delivery Mode**:
The dispatch and integration pathway (`local` or `pr`) that defines how task worktrees branch, publish changes, gate on verification, and incorporate approved commits into the primary branch.
_Avoid_: Merge mode, branch strategy, transport

**PR Delivery**:
The remote integration pathway (`pr`) in which task worktrees branch cleanly from `origin/<primary_branch>`, publish a GitHub Pull Request after verified review via a `$ship_token` handoff, gate integration on GitHub Actions checks, and merge via `gh pr merge`.
_Avoid_: GitHub mode, remote workflow, external PR

**Local Merge**:
The local-only integration pathway (`local`) in which task worktrees branch from the primary checkout `HEAD`, integrate via local `git merge --no-ff --no-commit`, and never execute `git push` automatically.
_Avoid_: Direct merge, internal delivery, offline mode
