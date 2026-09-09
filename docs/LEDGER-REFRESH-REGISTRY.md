# Registered Ledger Refresh

The governance repository owns a central refresh registry for every project in the private project registry.

## Register all projects

```powershell
python scripts/register_ledger_refresh.py
```

This creates the private runtime registry at `reports/local/ledger-refresh/registry.json`. It records the state ledger, freshness, next due time, and two triggers for every project:

- scan trigger: read-only proposal generation;
- apply trigger: writes only after `--approval-ref` is supplied.

## Refresh one ledger

```powershell
python scripts/refresh_registered_ledger.py --project-id <project-id>
python scripts/refresh_registered_ledger.py --project-id <project-id> --apply --approval-ref <approval-ref>
```

The refresh preserves human judgment fields such as `stage`, `status`, `owner`, `next_action`, `decision`, and `rollback_ref`. It updates verification metadata and local source-reference reconciliation only.

## Batch operation

The registry is the batch queue. A scheduler should run `register_ledger_refresh.py` at least every 24 hours, then execute scan triggers. Apply triggers must be reviewed and approved before they write project ledgers. A project with no state ledger remains `missing_ledger`; registration does not conceal that gap.

## Built-in cross-platform scheduler

The repository includes a Python scheduler that does not depend on Windows Task Scheduler:

```powershell
python scripts/ledger_refresh_scheduler.py --once
python scripts/ledger_refresh_scheduler.py --interval-hours 24
```

The first form runs one cycle. The second remains active, writes a heartbeat to `reports/local/ledger-refresh/scheduler/state.json`, registers all projects, generates due-project proposals, and repeats after the configured interval. It is scan-only by default and never applies project writes without a separate approved command.
