---
status: accepted
---

# Post-Diff Review Gate for Trivial Tasks and Orthogonal `--no-review` Mode

Running an independent Reviewer for every task wastes tokens, quota, and latency on tiny mechanical changes (such as typo fixes, docs edits, or localized config tweaks), while some workflows intentionally trade peer review for speed across an entire batch. At the same time, skipping review upfront from a task card alone is unsafe if the Worker's actual diff grows beyond trivial scope, and skipping review must not weaken the project's **Approval Gate**. We introduce a post-diff **Review Gate** after Worker completion (`ready`) that automatically skips launching a Reviewer on verified trivial mechanical diffs (even under `--handle`), plus an orthogonal `--no-review` flag that skips Reviewers for all tasks while keeping Runner diff inspection, `.agents/implement-tasks-auto-merge.md` enforcement, and the Approval Gate intact.

## Considered Options

- **Always launch a Reviewer (unless `--no-review`):** Simple, but burns Reviewer tokens and latency on trivial mechanical edits, and makes `--handle` pay review overhead on trivial changes that a human will inspect anyway.
- **Skip review upfront from task card metadata alone:** Risks unreviewed scope creep when a supposedly trivial task touches unexpected files, alters logic, or misses verification.
- **`--no-review` forces unconditional auto-merge or unconditional `--handle`:** Either silently auto-merges risky/sensitive unreviewed changes, or blocks routine verified changes behind manual `approve` when the user only wanted to skip peer review.
- **Post-diff Review Gate with built-in baseline + optional project `Skip Review` rules, and orthogonal `--no-review`:** Evaluates the actual `git diff "$base_sha...$submitted_sha"` before splitting a Reviewer pane, preserves the built-in baseline when `.agents/implement-tasks-auto-merge.md` omits `Skip Review`, keeps `--handle` and `--no-review` independent, and requires the Runner to enforce the Approval Gate alone whenever review is skipped.

## Consequences

- Trivial mechanical tasks automatically skip Reviewer creation when their verified diff satisfies the conservative baseline (and optional `## Skip Review (Trivial Tasks)` rules), while tasks whose diff expands beyond trivial scope still receive peer review.
- Under `--no-review`, no Reviewers are spawned, yet risky, sensitive-path, high-risk, or unverified tasks still pause in `summary-<task-id>` for `approve <task-id>` unless project rules allow auto-merge; missing/unfilled `.agents/implement-tasks-auto-merge.md` still blocks silent auto-merge.
- Because `--no-review` and `--handle` are orthogonal, trivial-task review skipping continues to operate under `--handle`, and `--no-review --handle` executes all tasks without Reviewers while pausing every task for manual `approve`.
