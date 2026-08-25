# Human-in-the-Loop Standard

## Risk tiers

- **L0:** read-only inventory, parsing, local reports — deterministic automation allowed.
- **L1:** local artifact generation or reversible local edits — automation allowed with tests and diff review.
- **L2:** sample external mutation, public content, credential use, or user-visible change — human approval required.
- **L3:** batch release, deletion, financial/legal/health claims, irreversible migration — dual review or explicit owner approval plus rollback readiness.

## Approval record

An approval must include:

```text
decision: approve_sample | approve_full | request_changes | reject | rollback
reviewer:
scope:
artifact_hash:
source_hash:
evidence_ids:
risk_tier:
approved_at:
expires_at:
rollback_ref:
```

An approval expires when the artifact hash, target scope, credentials, or required evidence changes. “Approved the project” is not a valid substitute for approving a specific artifact and scope.

## Human review surface

The Dashboard must make it possible to answer quickly:

1. What changed?
2. Which files/pages/users are affected?
3. What passed and what remains unknown?
4. What could go wrong?
5. What exact action is being requested?
6. How do I reverse it?

Automation may prepare, compare, score, and recommend. It may not silently convert a recommendation into publication.
