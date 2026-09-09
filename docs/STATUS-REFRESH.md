# Governance Status Refresh

The status refresh mechanism separates observation from mutation.

## Scan

Run:

```powershell
python scripts/refresh_governance_status.py --fail-if-stale
```

The command refreshes the private inventory and writes a proposal under `reports/local/status-refresh/`. It does not update `STATUS.local.json` or the public `STATUS.json`.

## Apply an approved update

After reviewing the proposal and obtaining approval:

```powershell
python scripts/refresh_governance_status.py --apply --approval-ref <approval-ref>
```

Only fact-like fields are refreshed: timestamps, run ID, evidence references, reconciliation observation, metrics, and update metadata. The scanner preserves `project_id`, `stage`, `status`, `owner`, `next_action`, `decision`, and `rollback_ref`.

## Periodic operation

The policy in `config/status-refresh-policy.json` defines the default 24-hour interval. A scheduler should run the scan command, alert on its stale exit code, and leave application of the proposal to an approved follow-up. Repeated scans are idempotent in effect: they create new private proposals and never silently change the source ledger.

Each proposal includes warnings, risks, recommendations, the target file, protected fields, and any approval reference used for application.
