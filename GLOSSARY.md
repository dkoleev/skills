# Multi-Harness Agent Skills

Shared vocabulary for authoring and operating multi-harness coding-agent skills in this repository.

## Language

**Harness**:
A specific coding-agent runtime and interface (such as Codex, Claude Code, Antigravity, Kimi Code, or OpenCode) that executes prompts inside a terminal session.
_Avoid_: Agent tool, CLI wrapper, model

**Orchestration Backend**:
The workspace and terminal multiplexer layer through which a coordinator creates isolated worktrees, launches agent panes, and relays prompts across harnesses.
_Avoid_: Terminal app, multiplexer, supervisor

**Task Source**:
The system of record that holds queued tasks, statuses, dependencies, assignees, and acceptance criteria.
_Avoid_: Issue tracker, backlog tool, ticket board

**Runner**:
The coordinating agent session invoked by the user in the primary checkout to select queued tasks, choose models and harnesses, supervise progress, archive evidence, and integrate approved work.
_Avoid_: Orchestrator, manager, main agent

**Worker**:
An isolated agent instance assigned to implement and locally commit a single task inside its dedicated worktree.
_Avoid_: Implementer, coder, executor

**Reviewer**:
A fresh, independent agent instance assigned to evaluate a Worker's submitted commit against the task specification and repository standards.
_Avoid_: Verifier, QA agent, auditor

**Summary Pane**:
A dedicated terminal pane opened beside the Worker and Reviewer after review finishes to present what changed, how it was tested, the review outcome, and links to evidence.
_Avoid_: Report tab, output window, log pane

**Run Record**:
The durable per-task record owned by the Runner that tracks branch ownership, assigned harnesses, tokens, lifecycle phase, and reviewed revisions across restarts.
_Avoid_: State file, checkpoint, metadata

**Review Loop**:
The bounded direct exchange between a Reviewer and a Worker in which findings are raised, addressed, and re-evaluated against each new commit until approval or escalation.
_Avoid_: Feedback cycle, fix loop, chat loop

**Correction Round**:
A single numbered iteration within a Review Loop consisting of one consolidated critique from the Reviewer and the Worker's corresponding response or fix commit.
_Avoid_: Turn, attempt, retry
