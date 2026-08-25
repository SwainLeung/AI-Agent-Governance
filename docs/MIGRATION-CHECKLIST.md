# Project Adoption Checklist

- [ ] Register project root, owner, control plane, external systems, and risk tier.
- [ ] Add `AGENTS.md` or equivalent local contract.
- [ ] Define README, CHANGELOG, CHECKLIST, status, evidence, decision, and rollback ownership.
- [ ] Add machine-readable `status.json` and run/evidence IDs.
- [ ] Make every checklist item include owner, dependency, exit evidence, and next action.
- [ ] Add human approval records with scope and artifact hash.
- [ ] Add stale-state detection and reconciliation against external systems.
- [ ] Add rollback metadata and test one rollback path.
- [ ] Add secret-safe credential health and index reporting.
- [ ] Add Dashboard projection only after the source records exist.
- [ ] Run local tests, governance checks, and a human review before external writes.

## Execution-chain preflight

Before an L2/L3 operation is allowed to leave the project plane, the project must also provide:

- a stable run ID and route/checkpoint reference;
- a dependency and blast-radius declaration;
- a fresh reconciliation result for the target external state;
- a decision bound to exact scope, artifact hash, evidence IDs, expiry, and rollback reference;
- a bounded retry policy and an idempotency statement for the adapter;
- an observation window and post-release feedback reference.

If any item is unknown or stale, the operation enters `blocked` or `recovery`; it does not become `pass` by default.
