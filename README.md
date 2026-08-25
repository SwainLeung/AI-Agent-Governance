# AI Agent Governance

This repository is the public policy plane for governing AI Agent projects. It contains reusable contracts, schemas, execution controls, Dashboard design, generators, and sanitized examples.

## Public/private separation

The repository is intentionally usable without a project inventory:

- Public: policy documents, schemas, execution contract, Dashboard tab configuration, generators, and anonymized templates.
- Private local: actual project registry, local paths, generated inventories, evidence, rollback archives, adoption queues, and rendered `dashboard.html`.

Populate the ignored `config/project-roots.local.json` locally to generate a private Dashboard. The public `config/project-roots.json` contains only registration fields, allowed roles, and risk-tier options.

## Operating model

```text
Public policy and schemas
  -> private local registry
  -> bounded inventory
  -> private evidence and Dashboard state
  -> human decision
  -> approved project operation
  -> verification and feedback
```

The Dashboard is a read-only projection. It cannot approve, publish, deploy, or mutate a project.

## Main documents

- `docs/SYSTEM-MODEL.md` - boundaries, feedback loops, invariants, and blind spots.
- `docs/EXECUTION-CHAIN.md` - operation stages, evidence gates, retry, recovery, and rollback.
- `docs/HUMAN-IN-THE-LOOP.md` - risk tiers and exact-scope approval fields.
- `docs/DASHBOARD-STANDARD.md` - projection, freshness, uncertainty, and privacy requirements.
- `docs/GOVERNANCE-DASHBOARD-DESIGN.md` - detailed tabs, statistics, and lineage.
- `docs/MIGRATION-CHECKLIST.md` - project adoption contract.

## Machine-readable public assets

- `config/project-roots.json` - public registry template and allowed options.
- `config/project-governance.schema.json` - current-state ledger schema.
- `config/execution-contract.json` - stage gates, failure taxonomy, retry, and recovery rules.
- `config/governance-checklist.json` - public hardening checklist without personal project identifiers.
- `config/dashboard-tabs.json` - Dashboard information architecture and public capability definitions.
- `scripts/build_governance_inventory.py` - private/local bounded inventory builder.
- `scripts/build_governance_dashboard.py` - private/local Dashboard state and HTML generator.
- `scripts/validate_governance.py` - contract and evidence validator.
- `scripts/create_rollback_manifest.py` - local restore-point generator.

## Local refresh

```powershell
python scripts/build_governance_inventory.py
python scripts/validate_governance.py
python scripts/create_rollback_manifest.py
```

With `config/project-roots.local.json` present, generated outputs go to ignored `reports/local/` and `dashboard.html` stays local. Without it, the public template produces an empty, non-personal inventory.
