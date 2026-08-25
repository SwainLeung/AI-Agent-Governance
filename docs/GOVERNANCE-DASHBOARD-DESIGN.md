# Governance Dashboard Design

The governance Dashboard adopts the operating shape of a detailed project root Dashboard while keeping governance-specific source boundaries and approval controls.

## Design rules

- The Dashboard is a read-only projection. It cannot approve, publish, deploy, or mutate a project.
- `config/dashboard-tabs.json` defines the tab information architecture; `reports/governance-dashboard-state.json` is the generated view model.
- Inventory, status ledgers, checklist items, execution contract, decisions, evidence, rollback, and adoption queue remain separate source records.
- Missing, stale, unknown, and TODO states remain visible. They are never converted to `pass` through a summary score.
- Every summary metric must be traceable to a source reference or generated evidence report.

## Tab mapping

| Tab | Purpose | Primary source |
|---|---|---|
| Overview | portfolio health, current decision, freshness, checklist progress | Dashboard state + `STATUS.json` |
| Projects | bounded registry, risk, state ledger, first blind spot | inventory report |
| Governance Audit | system-theory blind spots and execution-chain coverage | inventory + execution contract |
| Features | governance capabilities and adoption state | `config/dashboard-tabs.json` |
| Functions | entrypoint, trigger, output, approval boundary | `config/dashboard-tabs.json` |
| Architecture | policy/control/project/external planes | system model |
| Control Plane | routing, checkpoints, retries, recovery, failure taxonomy | execution contract |
| External Plane | human review, deploy, verify, observe, rollback gates | execution contract + human review standard |
| Actions | checklist and project adoption TODO queue | governance checklist + adoption queue |
| Sections | stage entry/exit evidence and re-entry behavior | execution contract |
| Sources | freshness and source existence | state ledger + source refs |
| Records | evidence, decisions, rollback, reconciliation | status ledger + record directories |
| Metrics | coverage and risk metrics, not approval score | generated Dashboard state |
| Lineage | checklist item → exit evidence → next action | governance checklist |

## Checklist statistics

The Dashboard reads `config/governance-checklist.json` and calculates:

- total items;
- completed, in-progress, pending, blocked, and not-applicable counts;
- completion percentage based only on `completed` items;
- priority distribution;
- item-level owner, dependency, exit evidence, and next action.

The percentage is a planning indicator. A project or release cannot become `pass` because the percentage is high.

## Adoption queue

The inventory refresh generates `reports/governance-adoption-queue.json`. It includes only existing L2/L3 registered projects with unresolved governance blind spots. L3 entries are P0 queue items; L2 entries are P1 queue items. Each entry lists the missing control and the smallest safe first action.

The first adoption action is read-only preflight. Project mutation begins only after the target project's local `AGENTS.md`, owner, test command, and scope are confirmed.
