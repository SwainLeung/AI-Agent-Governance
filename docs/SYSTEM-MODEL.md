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

External writes require `human_review` approval bound to the exact artifact and scope. Failure, timeout, stale evidence, or unknown state must enter `blocked` or `recovery`, never `pass`.

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

Before an external write, the loop must compare the approved scope and artifact hash with the current plan, check freshness and dependencies, and reconcile the last known external state. If any comparison is unknown, the loop enters `blocked` or `recovery` and fails closed.

## Invariants

- No secret in source, reports, logs, Dashboard, or changelog.
- No external mutation without an explicit adapter and approval.
- No `pass` when required evidence is missing or stale.
- Every status has an owner, timestamp, source, and next action.
- Every write has a before/after hash and rollback reference.
