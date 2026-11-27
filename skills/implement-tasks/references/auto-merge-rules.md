# Auto-Merge, Review-Skip, Delivery, and Approval Gate Rules

## Why project rules live outside the skill folder

- **Skill reference (`references/auto-merge-rules.md`):** Defines **Delivery Mode** resolution (`local` vs `pr`), the **Review Gate** (trivial-task skip and `--no-review`), the **Approval Gate** risk-evaluation protocol, startup onboarding flow, conservative universal baseline, and copy-ready template.
- **Project rules file (`<repo-root>/.agents/implement-tasks-auto-merge.md`, or an override path declared in `AGENTS.md` / `CLAUDE.md`):** Lives inside the target repository so `npx skills add` / `npx skills update` never overwrites project-specific rules and global skill installations never leak rules between projects.

## Delivery Mode (`local` vs `pr`)

- **`## Delivery Mode`** in `.agents/implement-tasks-auto-merge.md` (optional, defaults to `local`; overridable per run with `--pr` or `--local`):
  - **`local`**: Tasks integrate locally via `git merge --no-ff --no-commit` in the primary checkout; `git push` is never executed automatically.
  - **`pr`**: Worktrees branch from `origin/<primary_branch>` (`base_sha`), avoiding unpushed `Backlog.md` card commits in `<task_branch>`. After peer review passes (or is skipped), the Runner authorizes the Worker via `$ship_token` to push `<task_branch>` and open a GitHub PR (`gh pr create`). The Runner waits for PR checks (`gh pr checks --watch`) before merging (`gh pr merge` + `git pull --ff-only` + `Backlog.md` `Done` push) or pausing for `approve <task-id>`.

## Startup onboarding when project rules are missing or unfilled

When running in default auto-merge mode (without `--handle`), check `<repo-root>/.agents/implement-tasks-auto-merge.md` (or the documented override path) before auto-merging any task (this applies equally when `--no-review` is combined with default auto-merge mode):

1. Verify the file exists and contains concrete, configured rules (not empty or left as unedited template placeholders).
2. **If missing or unfilled:** The Runner **warns the user** that project auto-merge rules are not configured yet and asks how to proceed, offering three choices:
   - **Analyze the repository and draft rules:** The Runner inspects the repo's directory layout, tech stack, `AGENTS.md`/`CLAUDE.md`, CI/build/deploy scripts, and auth/security/persistence/migration/API/UI paths, presents a tailored draft of auto-merge vs `approve`-required rules for confirmation, and writes `<repo-root>/.agents/implement-tasks-auto-merge.md`.
   - **Write rules from user input:** The user specifies the rules in chat and the Runner writes `<repo-root>/.agents/implement-tasks-auto-merge.md`.
   - **Safe fallback for this run:** Proceed without writing rules by treating the run as manual-approval (`--handle` behavior — every completed task pauses for `approve <task-id>`).
3. **Hard safety invariant:** Never silently auto-merge any task when project rules are missing or unfilled (including under `--no-review` or automatic trivial-task review skip). Automatic trivial-task review skipping may still apply its built-in conservative baseline when the rules file is missing/unfilled (for example under `--handle` or the safe fallback) or omits a `Skip Review` section.

## Skipping Peer Review (Review Gate: Trivial Tasks & `--no-review`)

After verifying the Worker's final `ready` report (matching token, clean worktree, matching `HEAD` SHA) and **before** splitting a Reviewer pane, the Runner evaluates the **Review Gate**:

1. **Explicit `--no-review` mode (orthogonal to `--handle`):**
   - Skips launching a Reviewer for every task in the run (`review_skipped: true`, `review_skip_reason: "no-review-flag"`).
   - Does **not** bypass verification or the **Approval Gate**: the Runner still inspects `git diff "$base_sha...$submitted_sha"`, checks verification outcomes and gaps, enforces `.agents/implement-tasks-auto-merge.md` (including startup onboarding when not running with `--handle`), and decides `approval=auto` or `approval=human` alone.
   - Can be combined with `--handle` (`--no-review --handle`) to skip peer review on all tasks while pausing every task for manual `approve <task-id>`.

2. **Automatic trivial-task skip (default review mode, including under `--handle`):**
   - Evaluated **post-diff** against the **actual** `git diff "$base_sha...$submitted_sha"` (`--stat` and changed hunks), never solely from the upfront task card description.
   - Skip launching a Reviewer (`review_skipped: true`, `review_skip_reason: "trivial: <concise reason>"`) ONLY when **all** of the following built-in baseline criteria hold (as refined by any optional `## Skip Review (Trivial Tasks)` section in `.agents/implement-tasks-auto-merge.md`):
     - **Complexity is `mechanical`** (never `typical` or `high-risk/architectural`).
     - **Actual diff is small and localized:** by default, at most **3 changed files** and **50 changed lines** (`+` and `-` combined) — such as typo fixes, comments, Markdown/documentation edits, formatting, localized constant/config/copy tweaks, or trivial single-concern mechanical changes.
     - **No sensitive or contract changes:** touches no `Sensitive Paths & Domains` or `Require Human Approve` paths/patterns and introduces no public API, CLI contract, persisted schema, or non-trivial control-flow/logic changes.
     - **Clean & fully verified:** worktree is clean with zero verification gaps (all applicable checks/linters passed; no manual/visual inspection required).
     - **No explicit review requirement:** neither the task card, the user launch prompt, nor project rules request review for this task or path.
   - **Diff-reality rule:** If a task looked trivial upfront (for example, `mechanical` on the card) but the Worker's actual diff touches unexpected files, exceeds the size/scope threshold, alters control flow or contracts, hits a sensitive path, or has verification gaps, do **not** skip review — launch the Reviewer normally.

## Approval Gate evaluation (Runner + Reviewer, or Runner alone when review skipped)

- **When a Reviewer ran:** Both the **Runner** (evaluating task complexity, touched files/diff stat, verification gaps, CI status in `pr` mode, and `.agents/implement-tasks-auto-merge.md`) and the **Reviewer** (inspecting `git diff "$base_sha...$reviewed_sha"` and emitting `approval=auto` or `approval=human` with a concrete reason) evaluate the Approval Gate. The strictest verdict wins.
- **When review was skipped (trivial task or `--no-review`):** The **Runner alone** evaluates the Approval Gate directly from `git diff "$base_sha...$submitted_sha"`, verification evidence, CI status in `pr` mode, and `.agents/implement-tasks-auto-merge.md`.

### Auto-merge + auto-cleanup allowed ONLY when ALL hold

- Not running with `--handle`.
- Project rules file (`<repo-root>/.agents/implement-tasks-auto-merge.md`) exists and is configured.
- Task reached verified completion with zero verification gaps: either review verdict is `pass` with zero unresolved findings, OR review was skipped via the Review Gate (verified trivial diff or `--no-review`) with a clean verified Worker `ready` commit.
- In `pr` delivery mode, the PR is open on `HEAD == reviewed_sha` (or `submitted_sha`) and GitHub Actions checks are green (`pass` or `no-checks`).
- Task scope satisfies the project's `Auto-Merge Allowed` rules and touches no `Require Human Approve` rule or `Sensitive Paths & Domains`.
- `approval=auto` holds (both Runner and Reviewer agree when reviewed; Runner evaluates `approval=auto` when review was skipped).

### Human `approve <task-id>` required whenever ANY holds

- Running with `--handle`.
- Project rules are missing or unfilled (safe fallback).
- Task matches any `Require Human Approve` rule or touches `Sensitive Paths & Domains` in `.agents/implement-tasks-auto-merge.md`.
- Task complexity is `high-risk/architectural`, or has meaningful verification gaps (for example, checks skipped, hardware/environment unavailable, or manual/visual inspection needed).
- Approval Gate evaluates `approval=human`: flagged by the Reviewer when reviewed, or by the Runner when review was skipped (including `--no-review`) based on the diff (non-trivial architectural trade-offs, unexpected scope expansion, subtle compatibility risk, or unverified edge cases).
- Review ended `escalated`, CI checks remain failing/errored in `pr` mode, or merge encountered a conflict or combined-verification failure.

---

## Project template (`.agents/implement-tasks-auto-merge.md`)

Use this template when drafting `<repo-root>/.agents/implement-tasks-auto-merge.md` (replace placeholder examples with repository-specific paths and rules):

```markdown
# Implement Tasks — Auto-Merge Rules

## Delivery Mode
- `local` *(or `pr` to publish a GitHub Pull Request after review passes and gate merge on GitHub Actions checks; overridable per run with `--pr` / `--local`)*

## Auto-Merge Allowed
- Mechanical or routine single-module changes (`mechanical` or low-risk `typical` complexity) with passing review (`pass`) — or verified review-skipped changes (trivial-task skip or `--no-review`) — and zero verification gaps.
- Isolated bug fixes, unit/integration tests, refactors without public contract changes, and documentation updates.

## Skip Review (Trivial Tasks) *(Optional)*
- Leave absent to use the skill's built-in conservative baseline (`mechanical` complexity, `<= 3` files, `<= 50` changed lines, no logic/contract changes, no sensitive paths, zero verification gaps).
- Customize here to tighten, relax, or disable automatic review skipping (for example: allow specific doc/copy globs, lower/raise file and line caps, or list `Never skip review for ...` paths/task types).

## Require Human Approve
- Any `high-risk/architectural` task or change introducing non-obvious design trade-offs.
- Changes with verification gaps (e.g., checks skipped, hardware/environment unavailable, or manual visual verification needed).
- Changes altering public APIs, CLI contracts, persisted data schemas, or cross-module boundaries.

## Sensitive Paths & Domains
- Authentication, authorization, secrets, billing, or security-sensitive code (e.g., `src/auth/**`, `infra/**`).
- Database migrations, persistence schemas, or destructive data scripts (e.g., `migrations/**`, `db/**`).
- CI/CD workflows, release pipelines, and dependency manifests (e.g., `.github/workflows/**`, `package.json`).
- User-facing UI/UX surfaces requiring human visual sign-off (customize paths for this project).

## Required Checks Before Auto-Merge
- All task-relevant tests and linters must pass inside the task worktree AND against the combined state (or GitHub Actions PR checks in `pr` mode) before merge commit.

## Harness Pool & Routing *(Optional)*
- **Allowed pool:** List enabled harnesses for this repository (for example, `codex`, `claude`, `agy`).
- **Default routing:** Map complexity tiers (`mechanical`, `typical`, `high-risk/architectural`) to preferred harnesses/models, and prefer cross-vendor Reviewers when quota allows.
- **Launch notes:** Record repo-specific CLI settings (such as custom `claude` endpoint model IDs, `--no-daemon` for `codex` in Herdr GUI, or Windows PowerShell launch notes).

## Notes
- In `local` delivery mode, `git push` never runs automatically; pushing requires explicit user authorization.
- In `pr` delivery mode, the Worker may push `<task_branch>` and open/update the PR only after receiving the Runner's post-review `$ship_token`, and the Runner merges/pulls on GitHub only when CI is green and the Approval Gate allows (`approval=auto` or explicit `approve <task-id>`).
```
