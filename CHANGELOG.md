# AI Agent Governance Changelog

## [Unreleased]

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
