# AI Agent Governance Checklist

The machine-readable source is `config/governance-checklist.json`. This public projection contains no personal project identifiers. Private project adoption progress belongs in ignored local runtime reports.

| ID | Priority | Domain | Status | Exit evidence | Next action |
|---|---|---|---|---|---|
| GOV-P0-001 | P0 | State | completed | state schema, status contract, system model | Apply the ledger to private registered projects. |
| GOV-P0-002 | P0 | Execution chain | completed | execution contract and execution standard | Require adapter idempotency and checkpoint references. |
| GOV-P0-003 | P0 | Evidence/approval | completed | approval, documentation, and execution standards | Reject unbound high-risk approvals. |
| GOV-P0-004 | P0 | Verification | completed | validator and local evidence | Run validation in adoption workflows. |
| GOV-P1-001 | P1 | Reconciliation | completed | inventory generator and drift fields | Schedule pre-write and quarterly reconciliation. |
| GOV-P1-002 | P1 | Dashboard | completed | tab configuration and local projection generator | Keep rendered HTML private. |
| GOV-P1-003 | P1 | Feedback | completed | observation and feedback requirements | Require observation reports after external writes. |
| GOV-P2-001 | P2 | Adoption | in_progress | private local adoption queue and project records | Start with the highest-risk registered project. |
| GOV-P2-002 | P2 | Review | pending | private quarterly review report | Schedule after adoption starts. |

## Privacy controls

- [x] Keep the actual registry in ignored `config/project-roots.local.json`.
- [x] Keep generated Dashboard HTML and runtime reports out of Git.
- [ ] Review public history for previously exposed local identifiers after the history rewrite.
