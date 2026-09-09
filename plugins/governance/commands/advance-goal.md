---
description: Record and advance a claimed governance goal. Use a checklist ID and an outcome: in_progress, blocked, or completed.
---

# Advance governance goal

Record the outcome for one claimed checklist item and, after an explicit source update, emit the next eligible goal. Expected arguments are `<checklist-id> <in_progress|blocked|completed>`. The optional project form is `--project-id <id> --full-access <checklist-id> <outcome>`. Use `--approval-ref <ref>` whenever `--write` updates the source checklist.

## Preflight

1. Read the governance repository `AGENTS.md`, the item's declared `exit_evidence`, and the current machine-readable checklist status.
2. For `completed`, run the goal's required tests. Restricted mode enforces evidence gates; goal/full-access mode records missing evidence and risks as advisory findings.
3. When `$ARGUMENTS` contains `--full-access`, require `--project-id <id>` and create a ready startup context with `prepare_project_context.py`. Stop on a blocked context.
4. Do not mark an item complete from a percentage, an assertion, or stale evidence.

## Plan

- Persist exactly the supplied outcome using the explicit `--write` action and an approved `--approval-ref`.
- For a completed outcome, let `checklist_loop.py` enforce dependencies and evidence existence in restricted mode; goal/full-access mode records advisory failures in the report.
- Read the returned `next_goal`; do not execute it until it is claimed as its own bounded goal.

## Commands

For governance-root work:

```powershell
python scripts/checklist_loop.py loop --item-id <checklist-id> --outcome <outcome> --write --approval-ref <approval-ref> --execution-scope governance_root_only
```

For an already-authorized full-access project run, use the project root and checklist resolved by the ready startup context:

```powershell
${governanceRoot} = (Get-Location).Path
python scripts/prepare_project_context.py --project-id <id> --reason "$ARGUMENTS"
${contextPath} = Join-Path ${governanceRoot} 'reports/local/startup-context/latest.json'
${context} = Get-Content -Raw ${contextPath} | ConvertFrom-Json
Set-Location ${context}.project_root
python "${governanceRoot}\scripts\checklist_loop.py" --root ${context}.project_root --contract "${governanceRoot}\config\checklist-loop-contract.json" --checklist 'config/governance-checklist.json' --output-dir '.agent-manager/checklist-loop' --startup-context ${contextPath} loop --item-id <checklist-id> --outcome <outcome> --write --approval-ref <approval-ref> --execution-scope project_root_execution --permission-mode full_access
```

The project must expose `config/governance-checklist.json`; if it does not, stop and bootstrap its governance files before advancing a goal. Replace only the declared placeholders with parsed user arguments. Do not write if the outcome, item ID, or approval reference is ambiguous; ask for the missing value.

## Verification

Confirm `status: advanced` and inspect the emitted private loop record, including authority, warnings, risks, recommendations, and human follow-up. If `source_checklist_updated` is true, confirm the approval reference is recorded.

## Summary

Report the item ID, recorded outcome, whether the source checklist changed, the next goal ID if one exists, and the private runtime-record reference. Keep local paths and project identifiers out of the user-facing result unless the user supplied them.

## Next Steps

If a next goal is present, call `/governance:claim-goal` to start it as a separate bounded task. If the outcome is blocked, report its unblock action and do not widen scope.
