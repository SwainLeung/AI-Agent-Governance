---
description: Claim one eligible governance checklist item as a bounded goal. Use an optional project ID with full access only after the required preflight.
---

# Claim governance goal

Turn exactly one actionable checklist item into a bounded goal. Use `$ARGUMENTS` as the reason. The optional form is `--project-id <id> --full-access <reason>`; without it, remain at the governance root.

## Preflight

1. Run from the AI Agent Governance repository root and read its `AGENTS.md` and `README.md`.
2. Run the required control-plane route with this repository's own scripts. Environment-specific agent adapters (for example an external agent-manager) run from the operator's private environment and are never referenced by absolute local path from this public contract.

3. If `$ARGUMENTS` contains `--full-access`, require `--project-id <id>`. Run `prepare_project_context.py` for that private registered project. Stop if its status is not `ready`.
4. Never infer `project_root_execution`, a project ID, or full-access permission. The caller's environment must already grant full access.

## Plan

- Without `--full-access`, create a governance-root goal using the default `goal` write-authorized envelope; gates are advisory and reporting is mandatory.
- With `--full-access --project-id <id>`, create a project-root goal using the ready private startup-context record.
- Emit exactly one goal. Do not start a second checklist item until this one has a recorded outcome.

## Commands

For governance-root work:

```powershell
python scripts/checklist_loop.py goal --reason "$ARGUMENTS" --execution-scope governance_root_only
```

For an already-authorized full-access project run, first create the startup context, read its resolved project root, then use that project's machine-readable checklist:

```powershell
${governanceRoot} = (Get-Location).Path
python scripts/prepare_project_context.py --project-id <id> --reason "$ARGUMENTS"
${contextPath} = Join-Path ${governanceRoot} 'reports/local/startup-context/latest.json'
${context} = Get-Content -Raw ${contextPath} | ConvertFrom-Json
Set-Location ${context}.project_root
python "${governanceRoot}\scripts\checklist_loop.py" --root ${context}.project_root --contract "${governanceRoot}\config\checklist-loop-contract.json" --checklist 'config/governance-checklist.json' --output-dir '.agent-manager/checklist-loop' --startup-context ${contextPath} goal --reason "$ARGUMENTS" --execution-scope project_root_execution --permission-mode full_access
```

The project must expose `config/governance-checklist.json`; if it does not, stop and bootstrap its governance files before claiming a goal. Use the emitted `objective`, `exit_evidence`, and `next_action` to create one bounded Codex goal. Follow the target project's nearest `AGENTS.md` before edits.

## Verification

Confirm that the command returns `status: ready`, a `run_id`, one `checklist_item_id`, and an ignored runtime record under `reports/local/checklist-loop/`. If the project-root preflight is not ready, report the blocker and do not run project commands.

## Summary

Report the claimed checklist ID, goal objective, execution scope, runtime-record reference, and the exit evidence required for completion. Do not expose private project paths or unrelated registry details.

## Next Steps

Perform only the bounded goal. When its evidence is ready, invoke `/governance:advance-goal <checklist-id> completed`; use `--write --approval-ref <ref>` only when an approved checklist update is actually required.
