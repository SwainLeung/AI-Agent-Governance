# AI Agent Governance Changelog

## [Unreleased]

### 2026-08-25 Public repository sanitization

- Separated public policy assets from private local registry and runtime outputs.
- Replaced the public registry with a template containing only registration fields, role options, and risk-tier options.
- Moved local registry, generated inventory, Dashboard state, evidence, adoption queue, and rollback archives to ignored runtime locations.
- Classified rendered `dashboard.html` as local-only.
- Replaced concrete runtime decisions and project reports with sanitized public examples.
- Prepared the public `main` history for rewrite so previously committed local identifiers are not retained in visible history.

### 2026-08-25 Governance hardening

- Added machine-readable execution stages, failure taxonomy, evidence binding, freshness controls, and recovery semantics.
- Added detailed Dashboard tab architecture and Checklist statistics.

## Public repository rule

Policy, schemas, generators, and anonymized examples may be committed. Personal project names, local paths, generated runtime reports, rendered HTML, credentials, and production details may not.
