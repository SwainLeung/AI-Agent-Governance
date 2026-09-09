# Execution Chain Standard

The machine-readable source for the gates below is `config/execution-contract.json`. This document explains the operating rule; the validator enforces the minimum contract before handoff.

Every meaningful Agent operation must be traceable through these stages:

Read-only inventory, review, and governance observation may use a reduced path: intent → scope → plan → observe/report. They do not require a human approval stage unless they would cause an external write, credential-backed action, publication, deployment, or other user-visible effect.

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

## Checklist-to-goal control loop

`config/checklist-loop-contract.json` defines the bounded loop between the public machine-readable checklist and a single executable goal. `scripts/checklist_loop.py goal` selects one eligible item (preferring an existing `in_progress` item), checks its dependencies, and writes a private run record containing the goal objective, exit evidence, and next action. It does not execute project commands or grant permissions.

Clarification is required only when ambiguity could change the target, permissions, scope, risk tier, completion criteria, or external/user-visible effects. Otherwise, choose the smallest safe read-only interpretation, record the assumption, and continue.

After work completes, `scripts/checklist_loop.py loop --item-id <id> --outcome completed ...` records the outcome and emits the next eligible goal. In `restricted` mode, evidence and dependency gates are enforced. In `goal` or `full_access`, those gates are advisory: execution may continue, but missing evidence and risks must be recorded for post-run human review. A source checklist update is never automatic; `--write` requires an explicit approved `--approval-ref`.

When the actual runtime is already configured for `full_access`, `--permission-mode full_access` is allowed only with `project_root_execution` and a ready `--startup-context` produced by `prepare_project_context.py`. It authorizes bounded writes in the resolved scope and makes normal quality/evidence thresholds advisory, but still requires scope identity, local contract handling, traceability, and post-run reporting. It is not permission to expand scope or perform unrecorded writes.

## Execution-chain controls

- Every run has a stable `run_id`, a trace reference, and a resumable checkpoint when the adapter supports it.
- Checklist loop records are private runtime evidence; the checklist source changes only through the explicit `--write` action and only after its completion guards pass.
- Retries are bounded and stage-specific. A retry cannot silently widen scope or replace a changed artifact.
- Re-entry is explicit: an idempotent operation may resume from its last checkpoint; a scope, dependency, approval, or artifact-hash change requires replanning or a new decision.
- `blocked` means no safe execution path is currently available. `recovery` means an external system may be partially changed or unknown and all further writes stop until reconciliation.
- Failure classes are recorded as `AUTH`, `NETWORK`, `QUALITY`, `SCOPE`, `EVIDENCE`, `ADAPTER`, `DRIFT`, or `APPROVAL`; generic `blocked` without a reason is not sufficient.
- External writes require a fresh, exact-scope approval, a rollback reference, adapter response evidence, before/after hashes, and an independent live verification report.

Completion of a task means that the requested work and its report have been delivered. It does not imply a checklist source update. A needed governance-source update must be proposed as an explicit request, approved, and then executed with its approval reference. In `goal` or `full_access`, the report must include warnings, risks, recommendations, and human follow-up items even when execution continued past advisory gates.

The Dashboard should show the current stage and the first missing exit evidence, not only a percentage.
