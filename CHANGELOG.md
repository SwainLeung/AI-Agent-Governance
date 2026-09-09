# AI Agent Governance Changelog

## [Unreleased]

### 2026-08-29 Checklist-to-goal loop

- Added a machine-readable checklist-loop contract plus `goal` and `loop` commands that create private run records and select one bounded actionable item at a time.
- Completion writes to the checklist only on an explicit `--write` action after dependency and exit-evidence checks pass; the command then emits the next eligible goal.
- Documented `full_access` as a pre-authorized runtime envelope for `project_root_execution`, not a way to bypass preflight, local contracts, or external-write controls.
- Extended the validator to require the checklist-loop contract and its command implementation.

### 2026-08-29 Governance slash commands

- Added the repo-local `governance` Codex plugin and marketplace entry.
- Added `/governance:claim-goal` and `/governance:advance-goal` command contracts for the bounded checklist loop.
- Kept `scripts/checklist_loop.py` as the plugin-independent CLI fallback.

### 2026-08-26 Project start and switch gate

- Added explicit `governance_root_only` and `project_root_execution` scopes for registered projects.
- Added a fail-closed private preflight for every project start or context switch.
- Extended inventory and Dashboard coverage to expose unclassified execution scopes.
- Kept README/AGENTS verification separate from state refresh and actual CHANGELOG events.

### 2026-08-26 Documentation contract layering

- Separated `README.md` orientation responsibilities from `AGENTS.md` Agent operating responsibilities.
- Added directory-level Agent contracts for configuration, documentation, tooling, decisions, and reports.
- Added validator coverage so the required directory contracts cannot silently disappear.

### 2026-08-25 Documentation and public-release update

- Synchronized README, CHECKLIST, and CHANGELOG with the public-policy/private-runtime architecture.
- Documented the repository status, development stages, release gates, and local refresh workflow.
- Confirmed that public validation works without a project registry and that private local runtime data remains ignored.
- Retained Dashboard configuration, schemas, generators, and sanitized examples as public development assets.

### 2026-08-25 Public repository sanitization

- Replaced the public project registry with a template containing only registration fields, role options, and risk-tier options.
- Moved local registry, generated inventory, Dashboard state, evidence, adoption queue, rollback archives, traces, and rendered HTML out of public Git.
- Replaced concrete runtime decisions and reports with sanitized public examples.
- Rewrote the public `main` history as a single sanitized root commit.

### 2026-08-25 Governance hardening

- Added machine-readable execution stages, failure taxonomy, evidence binding, freshness controls, and recovery semantics.
- Added detailed Dashboard tab architecture, Checklist statistics, and lineage views.
- Added local inventory, Dashboard, validator, and rollback generators.

## Public repository rule

Policy, schemas, generators, and anonymized examples may be committed. Personal project names, local paths, generated runtime reports, rendered HTML, credentials, traces, and production details may not.
