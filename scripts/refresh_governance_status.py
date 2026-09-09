"""Scan and, with explicit approval, refresh the private governance status ledger."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = Path("config/status-refresh-policy.json")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def resolve_status(root: Path, policy: dict[str, Any]) -> Path:
    candidates = policy.get("status_candidates", ["STATUS.local.json", "STATUS.json"])
    for name in candidates:
        path = root / str(name)
        if path.is_file() and path.name == policy.get("preferred_private_status"):
            return path
    for name in candidates:
        path = root / str(name)
        if path.is_file():
            return path
    raise ValueError("no status ledger found")


def run_inventory(root: Path) -> dict[str, Any]:
    command = [sys.executable, str(root / "scripts" / "build_governance_inventory.py"), "--root", str(root)]
    result = subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    output = root / "reports" / "local" / "project-governance-inventory.json"
    inventory = read_json(output)
    inventory["refresh_command_output"] = result.stdout.strip()
    return inventory


def build_proposal(root: Path, policy: dict[str, Any], status_path: Path, inventory: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    timestamp = now()
    run_id = f"status-refresh-{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    current = read_json(status_path)
    proposed = copy.deepcopy(current)
    summary = inventory.get("summary", {})
    projects = inventory.get("projects", []) if isinstance(inventory.get("projects"), list) else []
    missing_roots = sum(1 for item in projects if not item.get("exists"))
    inventory_ref = "reports/local/project-governance-inventory.json"
    dashboard_ref = "reports/local/governance-dashboard-state.json"
    ledger_registry_ref = "reports/local/ledger-refresh/registry.json"
    proposed["generated_at"] = timestamp.isoformat()
    proposed["last_verified_at"] = timestamp.isoformat()
    proposed["run_id"] = run_id
    proposed["evidence"] = [ref for ref in (inventory_ref, dashboard_ref, ledger_registry_ref) if (root / ref).is_file()]
    reconciliation_status = "matched" if missing_roots == 0 else "drift"
    proposed["reconciliation"] = {
        "status": reconciliation_status,
        "scope": "registered_projects_and_local_state_ledgers",
        "checked_at": timestamp.isoformat(),
        "evidence_ref": inventory_ref,
        "projects_scanned": len(projects),
        "missing_project_roots": missing_roots,
        "stale_project_ledgers": summary.get("stale_state_ledger", 0),
    }
    proposed["metrics"] = {
        **(current.get("metrics") if isinstance(current.get("metrics"), dict) else {}),
        **summary,
        "private_runtime_loaded": True,
    }
    proposed["last_update"] = {
        "mode": "approved_status_refresh",
        "run_id": run_id,
        "updated_at": timestamp.isoformat(),
        "approval_ref": None,
    }
    previous_time = parse_time(current.get("generated_at"))
    ttl = float(current.get("freshness_ttl_hours", 24))
    age_hours = ((timestamp - previous_time).total_seconds() / 3600) if previous_time else None
    risks: list[str] = []
    recommendations: list[str] = []
    if age_hours is None or age_hours > ttl:
        risks.append(f"status ledger was stale before refresh ({round(age_hours, 2) if age_hours is not None else 'unknown'}h > {ttl}h)")
    if reconciliation_status != "matched":
        risks.append(f"local reconciliation found {missing_roots} missing registered project roots")
        recommendations.append("Resolve missing registered project roots and rerun reconciliation")
    proposal_warning = "Downstream ledger freshness is tracked in inventory, not promoted to the governance root risk field."
    if summary.get("stale_state_ledger", 0):
        proposal_warning = f"{summary['stale_state_ledger']} registered project ledgers remain stale in the downstream monitoring queue"
        recommendations.append(proposal_warning)
        recommendations.append("Review the stale-project queue and refresh each project through its own approved workflow")
    proposal = {
        "schema_version": "governance-status-refresh-proposal@1.0.0",
        "created_at": timestamp.isoformat(),
        "run_id": run_id,
        "target": str(status_path.relative_to(root)).replace("\\", "/"),
        "current": current,
        "proposed": proposed,
        "auto_refresh_fields": policy.get("auto_refresh_fields", []),
        "protected_fields": policy.get("protected_fields", []),
        "warnings": ["This proposal refreshes facts only; protected human judgment fields are unchanged.", proposal_warning if summary.get("stale_state_ledger", 0) else "Downstream ledger freshness is tracked in inventory, not promoted to the governance root risk field."],
        "stale_before_refresh": bool(age_hours is None or age_hours > ttl),
        "risks": risks,
        "recommendations": recommendations,
        "approval_ref": None,
        "applied": False,
    }
    return run_id, proposal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--apply", action="store_true", help="apply the proposed private status refresh")
    parser.add_argument("--approval-ref", help="required when --apply is used")
    parser.add_argument("--fail-if-stale", action="store_true", help="return non-zero when the current ledger is stale")
    args = parser.parse_args()
    root = args.root.resolve()
    policy = read_json(root / POLICY_PATH)
    status_path = resolve_status(root, policy)
    if status_path.name != policy.get("preferred_private_status") and args.apply:
        raise ValueError("refusing to apply to public STATUS.json; private STATUS.local.json is required")
    inventory = run_inventory(root)
    run_id, proposal = build_proposal(root, policy, status_path, inventory)
    proposal_dir = root / policy.get("proposal_output_dir", "reports/local/status-refresh")
    proposal_path = proposal_dir / f"{run_id}.json"
    if args.apply:
        if not args.approval_ref:
            raise ValueError("--apply requires --approval-ref")
        proposal["approval_ref"] = args.approval_ref
        proposal["proposed"]["last_update"]["approval_ref"] = args.approval_ref
        proposal["applied"] = True
        proposal["applied_at"] = now().isoformat()
        write_json(status_path, proposal["proposed"])
    write_json(proposal_path, proposal)
    stale = bool(proposal["stale_before_refresh"])
    print(json.dumps({"status": "applied" if args.apply else "proposal_ready", "target": str(status_path), "proposal": str(proposal_path), "run_id": run_id, "stale_before_refresh": stale, "risks": proposal["risks"], "recommendations": proposal["recommendations"]}, ensure_ascii=False, indent=2))
    return 2 if args.fail_if_stale and stale else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
