# AI Agent Governance Checklist

The machine-readable source is `config/governance-checklist.json`. This document is the public work-queue projection; private project adoption details stay in ignored local runtime reports.

## Current state — 2026-08-26

| ID | Priority | Domain | Status | Exit evidence | Next action |
|---|---|---|---|---|---|
| GOV-P0-001 | P0 | State | completed | state schema, status contract, system model | Apply the ledger to private registered projects. |
| GOV-P0-002 | P0 | Execution chain | completed | execution contract and execution standard | Require adapter idempotency and checkpoint references. |
| GOV-P0-003 | P0 | Evidence/approval | completed | approval, documentation, and execution standards | Reject unbound high-risk approvals. |
| GOV-P0-004 | P0 | Verification | completed | validator and public/local validation paths | Run validation in adoption workflows. |
| GOV-P1-001 | P1 | Reconciliation | completed | inventory generator and drift fields | Schedule pre-write and quarterly reconciliation. |
| GOV-P1-002 | P1 | Dashboard | completed | tab configuration and local projection generator | Keep rendered HTML private. |
| GOV-P1-003 | P1 | Feedback | completed | observation and feedback requirements | Require observation reports after external writes. |
| GOV-P1-004 | P1 | Documentation contracts | completed | README/AGENTS contract and directory AGENTS files | Keep orientation and Agent operating rules separate. |
| GOV-P1-005 | P1 | Project operations | in_progress | execution-scope policy, start/switch gate, private context preflight | Classify every private registered project before running project commands. |
| GOV-P1-006 | P1 | Checklist operations | completed | checklist-loop contract, goal/loop command, validator | Use one goal per actionable checklist item and explicitly record the next loop outcome. |
| GOV-P1-007 | P1 | Codex commands | completed | repo-local governance plugin and slash-command contracts | Use `/governance:claim-goal` and `/governance:advance-goal` for the bounded goal loop. |
| GOV-P2-001 | P2 | Adoption | in_progress | private local adoption queue and project records | Start with the highest-risk registered project. |
| GOV-P2-002 | P2 | Review | pending | private quarterly review report | Schedule after adoption starts. |

## Public release controls

- [x] Public registry contains no concrete project entries.
- [x] Local registry is ignored and remains available for private operation.
- [x] Rendered Dashboard HTML is ignored and removed from public Git history.
- [x] Generated inventory, evidence, adoption queue, rollback, trace, and cache outputs are ignored.
- [x] Public template validation passes without a private registry.
- [x] Local validation passes when the private registry is present.
- [ ] Repeat the public-tree privacy scan at every release.

## Next development queue

1. Complete private L2/L3 adoption one risk tier at a time.
2. Add a reusable project-owner decision and rollback workflow without exposing project identifiers.
3. Add schema-level privacy regression tests for public trees and generated artifacts.
4. Add adapter health and reconciliation summaries that contain no raw logs or credentials.
5. Add observation-window and post-release feedback metrics.
6. Run and record the first private quarterly governance drift review.
7. Assign `execution_scope` to every private registered project and run the start/switch preflight before project commands.
8. Use `scripts/checklist_loop.py goal` to create bounded goals; after evidence is produced, use `loop --write` to continue the queue.
9. Install the repo-local `governance` plugin to expose the bounded loop as Codex slash commands.

## Completion rule

An item is complete only when its exit evidence resolves, its dependencies are satisfied, and its status is reflected in the machine-readable checklist. A percentage is never approval evidence.
