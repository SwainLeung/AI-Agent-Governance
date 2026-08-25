# Execution Chain Standard

The machine-readable source for the gates below is `config/execution-contract.json`. This document explains the operating rule; the validator enforces the minimum contract before handoff.

Every meaningful Agent operation must be traceable through these stages:

| Stage | Entry condition | Exit evidence | Failure action |
|---|---|---|---|
| Intent | user objective is clear | scoped task record | request clarification |
| Scope | project, files, external systems identified | scope manifest | block expansion |
| Plan | route and dependencies prepared | plan/run ID | revise plan |
| Execute | approved tools and credentials available | trace/checkpoint | retry or fallback |
| Validate | local tests and quality gates run | test report | block |
| Package | artifact, source hash, metadata created | artifact manifest | regenerate |
| Review | human sees evidence and risks | decision record | request changes/reject |
| Deploy | explicit write authorization exists | adapter response | fail closed |
| Verify | live response matches artifact | live verification report | rollback/hold |
| Observe | agreed window and metrics active | observation report + feedback reference | adjust/rollback |

## Execution-chain controls

- Every run has a stable `run_id`, a trace reference, and a resumable checkpoint when the adapter supports it.
- Retries are bounded and stage-specific. A retry cannot silently widen scope or replace a changed artifact.
- Re-entry is explicit: an idempotent operation may resume from its last checkpoint; a scope, dependency, approval, or artifact-hash change requires replanning or a new decision.
- `blocked` means no safe execution path is currently available. `recovery` means an external system may be partially changed or unknown and all further writes stop until reconciliation.
- Failure classes are recorded as `AUTH`, `NETWORK`, `QUALITY`, `SCOPE`, `EVIDENCE`, `ADAPTER`, `DRIFT`, or `APPROVAL`; generic `blocked` without a reason is not sufficient.
- External writes require a fresh, exact-scope approval, a rollback reference, adapter response evidence, before/after hashes, and an independent live verification report.

The Dashboard should show the current stage and the first missing exit evidence, not only a percentage.
