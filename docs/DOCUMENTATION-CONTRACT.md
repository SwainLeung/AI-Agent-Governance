# Documentation Contract

## Four existing documents are not interchangeable

| Document | Role | Must contain | Must not claim |
|---|---|---|---|
| `README.md` | stable orientation and operating contract | purpose, boundaries, entrypoints, ownership, supported commands | that current work is complete merely because the file exists |
| `CHANGELOG.md` | append-only event history | date, change, reason, affected scope, evidence reference, rollback note | current state or approval by implication |
| `CHECKLIST.md` | executable work queue | owner, status, dependency, exit criteria, evidence path, next action | completion without evidence |
| `dashboard.html` | read-only projection | current status, freshness, blockers, links to evidence and decisions | authority to publish or replace source records |

## README and AGENTS are complementary

`README.md` is the orientation contract. It explains purpose, boundaries, directory roles, supported entrypoints, and the human operating flow.

`AGENTS.md` is the Agent operating contract. It defines allowed changes, source-of-truth ownership, privacy and mutation boundaries, required checks, and handoff expectations.

The distinction is intentional:

- README answers “what is this and how do I enter it?”
- AGENTS answers “how may an Agent change it and how must the change be verified?”
- A directory may have one `AGENTS.md` when its authority, ownership, privacy, or validation behavior differs from the parent directory.
- Individual source artifacts do not receive their own instruction file by default; the nearest directory contract applies.

The governance repository maintains directory contracts for `config/`, `docs/`, `scripts/`, `decisions/`, and `reports/`. These contracts refine the root [`AGENTS.md`](../AGENTS.md) and must not weaken its public/private boundary or fail-closed rules.

## Project start and switch records

Project operation is classified in `config/project-operation-policy.json` and selected per project in the private registry:

- `governance_root_only` keeps the work at the governance repository root and forbids project commands.
- `project_root_execution` requires a passing governance-root preflight before entering the registered project root.
- An omitted or unknown `execution_scope` is blocked until explicitly classified.

Before every start or switch, verify the applicable README and AGENTS files, refresh the relevant CHECKLIST and STATUS state when the context changes, and write a private startup context record. CHANGELOG is updated only for an actual change event; stable orientation and operating contracts are not rewritten merely because a project was selected.

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
