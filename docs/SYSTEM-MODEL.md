# System Model and Blind-Spot Review

## Boundaries

1. **Policy plane** — governance rules, risk classes, approval requirements.
2. **Control plane** — Agent Manager routes, checkpoints, traces, feedback candidates, and reversible changes.
3. **Project plane** — site code, content, assets, tests, adapters, and project-owned state.
4. **External plane** — WordPress, APIs, deployment targets, users, and live observations.

No plane may silently impersonate another. A Dashboard cannot approve an external write; a credential health check cannot approve content; a successful local test cannot prove live correctness.

## Required state machine

```text
intent
 -> scoped
 -> planned
 -> executing
 -> evidence_ready
 -> human_review
 -> approved_sample | changes_requested | rejected
 -> sample_observed
 -> expanded | adjusted | rolled_back
```

In restricted execution, external writes require `human_review` approval bound to the exact artifact and scope. In explicitly authorized `goal` or `full_access` execution, failure, timeout, stale evidence, or unknown state is recorded as a warning/risk and does not automatically stop bounded execution; the post-run report must identify the issue and propose human follow-up.

## Systems-theory blind spots to control

- **State drift:** README, Dashboard, reports, and live system disagree. Fix with source hashes, timestamps, and a state ledger.
- **Observability gap:** a task is marked complete without evidence. Fix with required evidence IDs and exit criteria.
- **Feedback delay:** live failures do not return to the next planning cycle. Fix with observation windows and post-release review.
- **Hidden coupling:** a shared credential, template, or script change affects unrelated sites. Fix with dependency declarations and blast-radius review.
- **False convergence:** repeated local passes hide a live or audience failure. Fix with independent live verification and human sampling.
- **Approval ambiguity:** a person approves a page but not the batch, scope, or version. Fix with explicit approval scope and expiry.
- **Rollback blindness:** a new artifact is deployable but the prior version is not recoverable. Fix with previous hash, mapping, and rollback test.
- **Queue illusion:** a checklist item remains open while a downstream system already changed. Fix with reconciliation jobs.

## Control-loop requirements

The policy plane must observe itself as well as downstream projects. The governance project is therefore registered in `config/project-roots.json`, and the inventory includes its own state ledger, evidence, dashboard, and adoption gaps.

Each control loop records four distinct timestamps when applicable: intent time, artifact time, decision time, and live-observation time. A newer timestamp does not prove a later stage succeeded; the stage exit evidence remains authoritative.

Before an external write in restricted execution, the loop must compare the approved scope and artifact hash with the current plan, check freshness and dependencies, and reconcile the last known external state. In goal/full_access execution, failed or unknown comparisons become recorded warnings and risks rather than automatic blockers, while scope identity and write traceability remain required.

## Invariants

- No secret in source, reports, logs, Dashboard, or changelog.
- No external mutation in restricted execution without an explicit adapter and approval; goal/full_access execution must still use the resolved adapter path and record the authority, warnings, risks, and follow-up report.
- No `pass` when required evidence is missing or stale.
- Every status has an owner, timestamp, source, and next action.
- Every write has a before/after hash and rollback reference.
