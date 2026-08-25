# Documentation Contract

## Four existing documents are not interchangeable

| Document | Role | Must contain | Must not claim |
|---|---|---|---|
| `README.md` | stable orientation and operating contract | purpose, boundaries, entrypoints, ownership, supported commands | that current work is complete merely because the file exists |
| `CHANGELOG.md` | append-only event history | date, change, reason, affected scope, evidence reference, rollback note | current state or approval by implication |
| `CHECKLIST.md` | executable work queue | owner, status, dependency, exit criteria, evidence path, next action | completion without evidence |
| `dashboard.html` | read-only projection | current status, freshness, blockers, links to evidence and decisions | authority to publish or replace source records |

## Required companion records

Every non-trivial project needs:

- `status.json` or equivalent current-state ledger;
- `evidence/` or a report directory with immutable run IDs;
- `decisions/` or a decision record containing reviewer, scope, timestamp, and artifact hash;
- `rollback/` or a previous-version reference for reversible changes;
- a runtime/credential health report that never includes secret values.

The minimum machine-readable state fields are `schema_version`, `project_id`, `stage`, `status`, `owner`, `generated_at`, `evidence`, and `next_action`. For execution-capable projects, also record `run_id`, `last_verified_at`, `freshness_ttl_hours`, dependencies, failure classification, reconciliation result, and rollback metadata.

## Freshness rules

- Static documentation: review when architecture or ownership changes.
- Changelog: append in the same change loop as implementation.
- Checklist: update when work starts, pauses, fails, or completes.
- Dashboard: expose `generated_at`, source timestamps, stale thresholds, and the source report links.
- A stale Dashboard is an observation failure, not a successful project state.
- A checklist item is not complete until its exit evidence paths resolve and its dependencies are complete or explicitly waived.
- A status of `pass` is invalid when required evidence is missing or stale.
- A rollback reference must resolve to a manifest with a verified restore artifact, not only a descriptive note or hash.
