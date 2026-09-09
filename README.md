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
- layered documentation contracts that separate human orientation from Agent operating rules.

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

The local registry belongs in ignored `config/project-roots.local.json`. The public `config/project-roots.json` contains only registration fields, allowed roles, risk tiers, execution-scope options, and privacy instructions.

Each registered project must also declare an `execution_scope` from `config/project-operation-policy.json`:

- `governance_root_only` — operate and refresh governance state at this repository root; do not enter or execute project commands in the target project.
- `governance_observation` — inspect a registered target read-only, record missing or unknown controls, and never mutate, publish, deploy, or approve the target.
- `project_root_execution` — pass the governance-root preflight, then enter the registered project root and execute only within its local contract.

An omitted or unknown scope is blocked. Before every project start or switch, check the root `README.md`/`AGENTS.md`, refresh the relevant `CHECKLIST`/`STATUS`, and record the private startup context. Stable README/AGENTS files are verified every time but edited only when their content changes. See [Project start and switch gate](docs/PROJECT-START-SWITCH.md).

## Checklist-to-goal loop

Use the checklist loop to turn exactly one actionable machine-readable checklist item into a bounded Codex goal. It writes its run records only under ignored `reports/local/checklist-loop/`; only `loop --write` changes the checklist source, and completion is rejected unless the declared exit-evidence files and dependencies resolve.

```powershell
# Create a ready private preflight record, then select an actionable goal.
python scripts/prepare_project_context.py --project-id <project-id> --reason "start checklist goal"
python scripts/checklist_loop.py --startup-context reports/local/startup-context/latest.json goal --reason "start the next scoped task" --execution-scope project_root_execution --permission-mode full_access

# After the goal produces its evidence, persist its outcome and get the next goal.
python scripts/checklist_loop.py --startup-context reports/local/startup-context/latest.json loop --item-id <checklist-id> --outcome completed --write --execution-scope project_root_execution --permission-mode full_access
```

`full_access` is an explicitly authorized write envelope for the resolved `project_root_execution` scope. It makes normal quality/evidence thresholds advisory, but still requires scope identity, traceability, warnings/risks reporting, and human follow-up. It does not authorize scope expansion or unrecorded writes. `goal` is the default bounded write mode for the checklist loop; it follows the same advisory-gate/reporting model.

Read-only monitoring and review may use `governance_observation`. It does not require approval. A governance-source update is never automatic: submit the requested change, obtain approval, then run the write with an approval reference.

The repo-local Codex plugin provides the same workflow as `/governance:claim-goal` and `/governance:advance-goal`; see [`plugins/governance/README.md`](plugins/governance/README.md). The CLI remains the portable fallback.

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

- `AGENTS.md` - repository-wide Agent operating contract and public/private boundary.
- `config/` - public contracts, templates, and Dashboard information architecture; see `config/AGENTS.md`.
- `docs/` - system model, execution chain, human review, security, migration, and Dashboard design; see `docs/AGENTS.md`.
- `scripts/` - local inventory, Dashboard, validation, and rollback tooling; see `scripts/AGENTS.md`.
- `decisions/` - sanitized public examples only; real decisions belong to ignored local runtime records; see `decisions/AGENTS.md`.
- `reports/` - public report policy and sanitized assessments; generated runtime reports are ignored; see `reports/AGENTS.md`.
- `STATUS.json` - public template state; local runtime may use ignored `STATUS.local.json`.

## README and AGENTS distinction

`README.md` explains what a project or directory is for and how a human should enter it. `AGENTS.md` explains how an Agent may work there, which artifact is authoritative, what privacy and mutation boundaries apply, and how to verify a change. They are complementary: README is orientation, while AGENTS is enforcement-oriented operating context.

The repository uses directory-level contracts instead of one instruction file per source artifact. A child `AGENTS.md` may narrow responsibilities and checks for its directory, but it cannot override the root public/private boundary, approval rules, or fail-closed requirements.

## Local workflow

In a private workspace, populate `config/project-roots.local.json`, then run:

```powershell
python scripts/build_governance_inventory.py
python scripts/validate_governance.py
python scripts/create_rollback_manifest.py
python scripts/checklist_loop.py goal --reason "start the next scoped task" --execution-scope governance_root_only
python scripts/refresh_governance_status.py --fail-if-stale
```

With the local registry present, outputs are written under ignored `reports/local/` and the rendered Dashboard remains local. Without it, the public template produces an empty, non-personal inventory.

`scripts/refresh_governance_status.py` is the periodic status mechanism. It refreshes the inventory, writes a private proposal under `reports/local/status-refresh/`, and returns a stale signal without modifying the source ledger. Apply only an approved proposal with `--apply --approval-ref <ref>`; it updates `STATUS.local.json` facts while preserving human judgment fields. A scheduler may invoke the scan command every 24 hours.

All registered project ledgers are centrally registered with `python scripts/register_ledger_refresh.py`. Each record receives a scan trigger and an approval-gated apply trigger. Use `python scripts/refresh_registered_ledger.py --project-id <id>` for one project; use the generated private registry to drive an approved batch refresh.

The built-in cross-platform scheduler is `python scripts/ledger_refresh_scheduler.py --interval-hours 24`; use `--once` for a single cycle. It records heartbeat and run reports under ignored `reports/local/ledger-refresh/scheduler/` and is scan-only by default.

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
- update the nearest `AGENTS.md` when ownership, authority, privacy, or validation behavior changes;
- scan the staged public tree for local paths, project identifiers, credentials, and generated runtime files;
- keep rendered HTML and runtime reports ignored;
- update README, CHANGELOG, and CHECKLIST when behavior or boundaries change.

See [CHECKLIST.md](CHECKLIST.md) for the current work queue.
