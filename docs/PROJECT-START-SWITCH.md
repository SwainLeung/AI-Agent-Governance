# Project Start and Switch Gate

This is the operational gate for starting work or switching between registered projects. The machine-readable policy is `config/project-operation-policy.json`; the private project registry selects one `execution_scope` for each project.

## Scope classification

| `execution_scope` | Where work happens | Project commands | Required transition |
|---|---|---:|---|
| `governance_root_only` | Governance repository root | No | Refresh governance context and stop at the root |
| `governance_observation` | Registered target inspected from governance root | No | Read-only observation; record missing controls as evidence |
| `project_root_execution` | Registered project root after root preflight | Yes | Pass root preflight, then apply the project's nearest contract |
| missing/unknown | Nowhere | No | Block and classify the project explicitly |

## Required transition

Run from the governance repository root:

```powershell
python scripts/prepare_project_context.py --project-id <project-id> --reason "<why starting or switching>"
```

The preflight must resolve the project, validate its execution scope, check the governance root's `AGENTS.md` and `README.md`, and write a private startup context report. For `project_root_execution`, it must also check the target project's root contract and orientation files before any project command is run.

`governance_observation` is a read-only exception for governance monitoring. It may inspect a registered target and record missing or unknown controls, but it may not run project commands, mutate the target, use credentials for a target action, publish, deploy, or approve a change. Missing target documentation is an observation finding, not by itself a blocker; a missing target root remains a blocker because there is nothing to inspect.

At each transition:

1. Read and verify the nearest `AGENTS.md` and `README.md`.
2. Refresh `CHECKLIST.md` and `STATUS` when the active context or next action changes.
3. Append `CHANGELOG.md` only when an actual change occurs.
4. Keep the startup context, local paths, and project identifiers in ignored runtime output.
5. If a required file, scope, state ledger, or project root is missing, stop and record the blocker for execution. In `governance_observation`, missing target controls are recorded as findings and only a missing target root blocks observation.

For a checklist-selected goal in a `full_access` runtime, generate the goal only after selecting `project_root_execution`; then run this preflight before any project command. Full access lets the already-authorized runtime execute the resulting bounded work directly, but does not replace this transition or authorize broader scope.

README and AGENTS are stable contracts, not heartbeat files. Routine starts and switches verify them; they do not create meaningless edits.
