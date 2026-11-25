# Auto-Merge Rules and Approval Gate

## Why project rules live outside the skill folder

- **Skill reference (`references/auto-merge-rules.md`):** Defines the risk-evaluation protocol, startup onboarding flow, conservative universal baseline, and copy-ready template.
- **Project rules file (`<repo-root>/.agents/implement-tasks-auto-merge.md`, or an override path declared in `AGENTS.md` / `CLAUDE.md`):** Lives inside the target repository so `npx skills add` / `npx skills update` never overwrites project-specific rules and global skill installations never leak rules between projects.

## Startup onboarding when project rules are missing or unfilled

When running in default mode (without `--handle`), check `<repo-root>/.agents/implement-tasks-auto-merge.md` (or the documented override path) before auto-merging any task:

1. Verify the file exists and contains concrete, configured rules (not empty or left as unedited template placeholders).
2. **If missing or unfilled:** The Runner **warns the user** that project auto-merge rules are not configured yet and asks how to proceed, offering three choices:
   - **Analyze the repository and draft rules:** The Runner inspects the repo's directory layout, tech stack, `AGENTS.md`/`CLAUDE.md`, CI/build/deploy scripts, and auth/security/persistence/migration/API/UI paths, presents a tailored draft of auto-merge vs `approve`-required rules for confirmation, and writes `<repo-root>/.agents/implement-tasks-auto-merge.md`.
   - **Write rules from user input:** The user specifies the rules in chat and the Runner writes `<repo-root>/.agents/implement-tasks-auto-merge.md`.
   - **Safe fallback for this run:** Proceed without writing rules by treating the run as manual-approval (`--handle` behavior — every passing task pauses for `approve <task-id>`).
3. **Hard safety invariant:** Never silently auto-merge any task when project rules are missing or unfilled.

## Strictest-gate evaluation (Runner + Reviewer)

Both the **Runner** (evaluating task complexity, touched files/diff stat, verification gaps, and `.agents/implement-tasks-auto-merge.md`) and the **Reviewer** (inspecting the actual `git diff "$base_sha...$reviewed_sha"` and emitting `approval=auto` or `approval=human` with a concrete reason) evaluate the Approval Gate. The strictest verdict wins.

### Auto-merge + auto-cleanup allowed ONLY when ALL hold

- Not running with `--handle`.
- Project rules file (`<repo-root>/.agents/implement-tasks-auto-merge.md`) exists and is configured.
- Review verdict is `pass` with zero unresolved findings and zero meaningful verification gaps.
- Task scope satisfies the project's `Auto-Merge Allowed` rules and touches no `Require Human Approve` rule or `Sensitive Paths & Domains`.
- Both Runner and Reviewer agree on `approval=auto`.

### Human `approve <task-id>` required whenever ANY holds

- Running with `--handle`.
- Project rules are missing or unfilled (safe fallback).
- Task matches any `Require Human Approve` rule or touches `Sensitive Paths & Domains` in `.agents/implement-tasks-auto-merge.md`.
- Task complexity is `high-risk/architectural`, or has meaningful verification gaps (for example, manual/visual inspection needed or required checks unavailable in the environment).
- Reviewer flags `approval=human` based on the diff (non-trivial architectural trade-offs, unexpected scope expansion, subtle compatibility risk, or unverified edge cases).
- Review ended `escalated` or auto-merge encountered a conflict, overlapping primary edit, or combined-verification failure.

---

## Project template (`.agents/implement-tasks-auto-merge.md`)

Use this template when drafting `<repo-root>/.agents/implement-tasks-auto-merge.md` (replace placeholder examples with repository-specific paths and rules):

```markdown
# Implement Tasks — Auto-Merge Rules

## Auto-Merge Allowed
- Mechanical or routine single-module changes (`mechanical` or low-risk `typical` complexity) with passing review (`pass`) and zero verification gaps.
- Isolated bug fixes, unit/integration tests, refactors without public contract changes, and documentation updates.

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
- All task-relevant tests and linters must pass inside the task worktree AND against the combined state before merge commit.

## Notes
- `git push` is never executed automatically; remote pushes always require separate explicit user authorization.
```
