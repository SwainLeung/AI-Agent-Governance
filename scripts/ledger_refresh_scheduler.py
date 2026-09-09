"""Run the registered-ledger refresh loop without an OS-specific scheduler."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_json(path: Path, default: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_command(root: Path, args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def run_once(root: Path, interval_hours: float) -> dict[str, Any]:
    started = utc_now()
    run_id = f"scheduler-{started.strftime('%Y%m%dT%H%M%SZ')}"
    runtime_dir = root / "reports" / "local" / "ledger-refresh" / "scheduler"
    registry_args = [str(root / "scripts" / "register_ledger_refresh.py"), "--root", str(root), "--interval-hours", str(interval_hours)]
    register_code, register_out, register_err = run_command(root, registry_args)
    errors: list[str] = []
    if register_code:
        errors.append(register_err or register_out or "ledger registration failed")
        registry = {}
    else:
        registry = read_json(root / "reports" / "local" / "ledger-refresh" / "registry.json", {})
    proposals: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for project in registry.get("projects", []) if isinstance(registry, dict) else []:
        if project.get("trigger_status") != "due":
            if project.get("trigger_status") == "missing_ledger":
                skipped.append({"project_id": project.get("project_id"), "reason": "missing_ledger"})
            continue
        project_id = str(project.get("project_id"))
        code, stdout, stderr = run_command(root, [str(root / "scripts" / "refresh_registered_ledger.py"), "--root", str(root), "--project-id", project_id])
        if code:
            errors.append(f"{project_id}: {stderr or stdout or 'refresh proposal failed'}")
            continue
        try:
            proposals.append(json.loads(stdout))
        except json.JSONDecodeError:
            errors.append(f"{project_id}: refresh output was not JSON")
    governance_code, governance_out, governance_err = run_command(root, [str(root / "scripts" / "refresh_governance_status.py"), "--root", str(root)])
    if governance_code:
        errors.append(f"governance status scan: {governance_err or governance_out or 'scan failed'}")
    finished = utc_now()
    report = {
        "schema_version": "ledger-refresh-scheduler-run@1.0.0",
        "run_id": run_id,
        "started_at": started.isoformat(),
        "completed_at": finished.isoformat(),
        "interval_hours": interval_hours,
        "mode": "scan_only",
        "writes_applied": 0,
        "registered_projects": registry.get("summary", {}).get("registered", 0) if isinstance(registry, dict) else 0,
        "due_projects": registry.get("summary", {}).get("due", 0) if isinstance(registry, dict) else 0,
        "proposals": proposals,
        "skipped": skipped,
        "errors": errors,
        "next_run_at": (finished + timedelta(hours=interval_hours)).isoformat(),
    }
    write_json(runtime_dir / f"{run_id}.json", report)
    state = {
        "schema_version": "ledger-refresh-scheduler-state@1.0.0",
        "status": "error" if errors else "idle",
        "last_run_id": run_id,
        "last_started_at": started.isoformat(),
        "last_completed_at": finished.isoformat(),
        "next_run_at": report["next_run_at"],
        "interval_hours": interval_hours,
        "last_summary": {
            "registered_projects": report["registered_projects"],
            "due_projects": report["due_projects"],
            "proposals": len(proposals),
            "skipped": len(skipped),
            "errors": len(errors),
            "writes_applied": 0,
        },
        "last_report": str((runtime_dir / f"{run_id}.json").relative_to(root)).replace("\\", "/"),
        "approval_required_for_writes": True,
    }
    write_json(runtime_dir / "state.json", state)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--interval-hours", type=float, default=24)
    parser.add_argument("--once", action="store_true", help="run one scan cycle and exit")
    args = parser.parse_args()
    if args.interval_hours <= 0:
        raise ValueError("--interval-hours must be positive")
    root = args.root.resolve()
    while True:
        report = run_once(root, args.interval_hours)
        print(json.dumps({"status": "error" if report["errors"] else "completed", "run_id": report["run_id"], "registered_projects": report["registered_projects"], "due_projects": report["due_projects"], "proposals": len(report["proposals"]), "errors": report["errors"], "next_run_at": report["next_run_at"]}, ensure_ascii=False, indent=2), flush=True)
        if args.once:
            return 1 if report["errors"] else 0
        time.sleep(args.interval_hours * 3600)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(json.dumps({"status": "stopped", "reason": "keyboard_interrupt"}, ensure_ascii=False))
        raise SystemExit(0)
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
