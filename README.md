# AI Agent Governance

Public policy plane for governing AI Agent projects.

Status: public template + private-local runtime separation established. Last documented verification: 2026-08-25.

## What this project provides

- lifecycle and execution-chain contracts;
- state, evidence, decision, rollback, and reconciliation schemas;
- human-review and fail-closed external-write rules;
- a detailed read-only Dashboard information architecture;
- local inventory, Dashboard, validation, and rollback generators;
- sanitized examples that are safe to publish.

This repository defines governance. It does not own project business code, credentials, production logs, external deployment, or publication decisions.

## Public/private boundary

The repository is intentionally usable without a private project inventory.

Public Git contains:

- policy documents and standards;
- machine-readable schemas and execution contracts;
- Dashboard tab definitions and generation code;
- public checklists and anonymized examples.

Private local runtime contains:

- the actual project registry;
- local paths and project identifiers;
- generated inventory, Dashboard state, adoption queue, evidence, and rollback archives;
- rendered `dashboard.html`.

The local registry belongs in ignored `config/project-roots.local.json`. The public `config/project-roots.json` contains only registration fields, allowed roles, risk tiers, and privacy instructions.

## Operating flow

```text
Public policy and schemas
  -> private local registry
  -> bounded inventory
  -> private evidence and Dashboard state
  -> human decision
  -> approved project operation
  -> live verification and observation
  -> feedback and next cycle
```

The Dashboard is a read-only projection. It cannot approve, publish, deploy, or mutate a project.

## Repository map

- `config/` - public contracts, templates, and Dashboard information architecture.
- `docs/` - system model, execution chain, human review, security, migration, and Dashboard design.
- `scripts/` - local inventory, Dashboard, validation, and rollback tooling.
- `decisions/` - sanitized public examples only; real decisions belong to ignored local runtime records.
- `reports/` - public report policy and sanitized assessments; generated runtime reports are ignored.
- `STATUS.json` - public template state; local runtime may use ignored `STATUS.local.json`.

## Local workflow

In a private workspace, populate `config/project-roots.local.json`, then run:

```powershell
python scripts/build_governance_inventory.py
python scripts/validate_governance.py
python scripts/create_rollback_manifest.py
```

With the local registry present, outputs are written under ignored `reports/local/` and the rendered Dashboard remains local. Without it, the public template produces an empty, non-personal inventory.

## Development stages

1. Policy: define boundaries, invariants, risk tiers, and stage gates.
2. Runtime separation: keep registries, paths, reports, traces, and rendered HTML private.
3. Verification: validate schemas, freshness, evidence references, and rollback readiness.
4. Adoption: apply the minimum contract to private registered projects by risk tier.
5. Operations: add reconciliation, live verification, observation windows, and feedback metrics.

## Change gates

Before merging a public change:

- run the public-template validator;
- run the local validator when a private registry is available;
- scan the staged public tree for local paths, project identifiers, credentials, and generated runtime files;
- keep rendered HTML and runtime reports ignored;
- update README, CHANGELOG, and CHECKLIST when behavior or boundaries change.

See [CHECKLIST.md](CHECKLIST.md) for the current work queue.
