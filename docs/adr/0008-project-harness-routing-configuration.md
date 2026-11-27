---
status: accepted
---

# Project Harness Routing Configuration

The project owns its routing configuration in a structured file under `.agents/`. One command from the repository opens the local browser editor. The editor and the Runner both read the structured file. Saving in the editor also updates the project's `Harness Pool & Routing` Markdown section, so maintainers can review routing changes alongside existing project instructions.

## Considered Options

The existing free-form Markdown section is easy to edit by hand. An editor that stored selections only in that prose would have to recover model IDs, effort levels, and task descriptions from arbitrary wording every time the project reopened it. Structured settings preserve those selections across edits, and the generated section keeps the policy readable in its existing location.

## Consequences

Each routing rule describes a kind of task and lists eligible combinations of harness, model ID, and reasoning effort. A model can appear in several rules with different efforts. The editor supports model catalogs and manually entered IDs so projects can use custom endpoints. The same editor manages the allowed pool, the preference for a cross-vendor Reviewer when quota allows, and launch notes for individual harnesses and the project.

Each candidate row applies to both Worker and Reviewer by default. A project can restrict an individual row to either role. Model family is shared across rules for each harness and model ID pair. The editor supplies a family when known and allows manual correction, including for custom endpoints.

When the cross-vendor preference is enabled, the Runner first looks for an eligible Reviewer whose harness and known model family both differ from the Worker's. Next it prefers a different known family, then another available independent Reviewer. When family information is missing, a different harness can guide the choice.

A new configuration starts with two editable rules, `High-risk / architectural` and `Typical / mechanical`. The Runner uses the first matching description in the project's chosen order and distributes assignments among its eligible candidates according to load and available quota. If no rule matches or the selected rule has no available candidate, the Runner reports the reason and keeps the task queued.

A launch prompt can narrow the pool for that run. For example, a Codex-only request filters candidates within the first matching rule to its eligible Codex entries. The saved project pool still applies to future runs.

Before removing a harness, the editor shows every affected rule. Removal clears that harness's candidates from those rules and preserves their descriptions so the user can choose replacements.

When a project already has a handwritten routing section, the first editing session shows that section beside the form. The user transfers the policy, checks the Markdown preview, and saves. Subsequent editing sessions load the structured configuration.
