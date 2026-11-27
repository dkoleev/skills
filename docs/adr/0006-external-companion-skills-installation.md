---
status: accepted
---

# External Companion Skills Installation and Opportunistic Integration

The `implement-tasks` skill integrates with complementary engineering workflow skills from [mattpocock/skills](https://github.com/mattpocock/skills) (`grill-with-docs`, `to-spec`, `to-tickets`, `tdd`, `code-review`, `pr`, `retro`, `codebase-design`, `domain-modeling`) across planning, red-before-green implementation, two-axis peer review, PR authoring, and retrospectives. We decide how these companion skills are packaged and delivered: whether `dkoleev/skills` should bundle or vendor them, declare a hard package dependency, or rely on independent user installation into target repositories with opportunistic ("when present") integration.

## Considered Options

- **Vendor or bundle upstream skills inside `dkoleev/skills`:** Copies third-party skill definitions directly into this repository (for example under `skills/`). While providing a single installation command, it blurs copyright and repository ownership, creates maintenance drag synchronizing upstream changes, and risks distributing stale or drifted copies.
- **Declare a rigid package dependency or require installation:** Forces every user of `implement-tasks` to install all 9 companion skills upfront, even when a project relies on custom review guidelines, different task planning tools, or alternative testing workflows.
- **Independent user installation with opportunistic "when present" integration:** Users install the specific upstream skills they want directly into their target repository (`npx skills add mattpocock/skills --skill <name>`). `implement-tasks` detects their presence (such as `.agents/skills/tdd/SKILL.md`, `.agents/skills/code-review/SKILL.md`, or `.agents/skills/pr/SKILL.md`) and adopts their specialized protocols when available, while falling back gracefully to universal built-in protocols when absent.

## Consequences

- `dkoleev/skills` distributes only its own first-party skills (such as `skills/implement-tasks/`, licensed under MIT by Dmitry Koleev) and does not vendor `mattpocock/skills`. Upstream licensing (MIT under Matt Pocock), attribution, and release cycles remain cleanly decoupled.
- Local checkouts of `dkoleev/skills` may hold authoring-time skills under gitignored `.agents/skills/` (specifically `domain-modeling`, `grill-with-docs`, and `grilling`) used exclusively for developing and maintaining this repository itself; these authoring-time dependencies are not packaged into or distributed with `skills/implement-tasks/`.
- Target projects install companion skills independently via `skills` CLI commands documented in `README.md`.
- `implement-tasks` inspects `<repo-root>/.agents/skills/` opportunistically: if `tdd`, `code-review`, or `pr` are present, Workers and Reviewers follow their specialized instructions; otherwise, they follow the built-in red-before-green, two-axis review, and standard PR conventions.
