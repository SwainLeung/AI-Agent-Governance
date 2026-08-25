# Dashboard Standard

## Is a reference project Dashboard a reasonable strengthening option?

Yes, as a read-only projection and human decision surface. It is not sufficient as the system of record by itself.

## Required tabs or views

- Overview: portfolio state, freshness, major blockers.
- Projects: ownership, lifecycle, health, adoption level.
- Work queue: checklist items with owner, dependency, and evidence.
- Evidence: run IDs, tests, artifacts, source hashes, live verification.
- Decisions: human approvals, expiry, scope, reviewer, rollback reference.
- Risks: blocked, stale, unknown, security, dependency, and external-system failures.
- Runtime: Agent Manager health, checkpoints, traces, credentials health, adapters.
- Metrics: quality, performance, cost/time, error rate, drift, and post-release observations.
- Lineage: task → artifact → deployment → live URL → feedback.

## Technical requirements

- Render from machine-readable state, not hand-entered HTML.
- Display source path, `generated_at`, freshness threshold, and stale warning.
- Link every summary value to its evidence report.
- Distinguish `pass`, `warn`, `blocked`, `unknown`, `stale`, and `not_applicable`.
- Preserve filters by project, risk tier, owner, stage, and last update.
- Never expose secrets, raw logs, private prompts, or full credentials.
- Keep mutation actions outside the Dashboard or behind an explicit approval adapter.

## Human-centred requirements

- Show the next decision, not only the current score.
- Show why a project is blocked and the smallest unblock action.
- Make uncertainty visible; missing data is not green.
- Provide a comparison with the previous approved version.
- Keep rollback and escalation one click away through evidence links.
- Show the first missing stage exit evidence, state age versus freshness threshold, and the latest reconciliation result.

The governance implementation follows a reference project Dashboard tab pattern with separate views for Overview, Projects, Audit, Features, Functions, Architecture, Control Plane, External Plane, Actions, Sections, Sources, Records, Metrics, and Lineage. Tab definitions are stored in `config/dashboard-tabs.json`; generated values are stored in ignored local runtime output.

## Privacy boundary

The generated `dashboard.html` may contain private project names, paths, and operational summaries. It is a local-only projection, must remain in `.gitignore`, and must be removed from the Git index if previously tracked. Dashboard source configuration and generation code may be committed; the rendered HTML must not be treated as a public artifact.
