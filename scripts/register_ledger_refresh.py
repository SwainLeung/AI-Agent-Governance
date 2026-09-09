"""Register every private project for centralized ledger refresh and emit due triggers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
STATE_NAMES = ("STATUS.local.json", "STATUS.json", "status.json", "project-state.json", "pipeline-state.json")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--interval-hours", type=float, default=24)
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "config" / "project-roots.local.json"
    registry = read_json(registry_path)
    now = datetime.now(timezone.utc)
    records = []
    for project in registry.get("projects", []):
        if not isinstance(project, dict):
            continue
        project_root = Path(str(project.get("path", ""))).expanduser()
        state_path = next((project_root / name for name in STATE_NAMES if (project_root / name).is_file()), None)
        state = read_json(state_path) if state_path else {}
        verified = parse_time(state.get("last_verified_at")) or parse_time(state.get("generated_at"))
        due_at = verified + timedelta(hours=args.interval_hours) if verified else None
        due = bool(state_path) and (due_at is None or due_at <= now)
        project_id = project.get("id")
        records.append({
            "project_id": project_id,
            "path": str(project_root),
            "risk_tier": project.get("risk_tier"),
            "execution_scope": project.get("execution_scope"),
            "ledger": str(state_path) if state_path else None,
            "ledger_exists": bool(state_path),
            "last_verified_at": state.get("last_verified_at") or state.get("generated_at"),
            "next_due_at": due_at.isoformat() if due_at else None,
            "trigger_status": "missing_ledger" if not state_path else ("due" if due else "registered"),
            "trigger": {
                "type": "central_governance_runner",
                "scan": f"python scripts/refresh_registered_ledger.py --project-id {project_id}",
                "apply": f"python scripts/refresh_registered_ledger.py --project-id {project_id} --apply --approval-ref <approval-ref>",
                "approval_required_for_apply": True,
            },
        })
    output = root / "reports" / "local" / "ledger-refresh" / "registry.json"
    payload = {
        "schema_version": "governance-ledger-refresh-runtime@1.0.0",
        "generated_at": now.isoformat(),
        "interval_hours": args.interval_hours,
        "source_registry": str(registry_path),
        "trigger_type": "central_governance_runner",
        "summary": {
            "registered": len(records),
            "ledger_present": sum(item["ledger_exists"] for item in records),
            "due": sum(item["trigger_status"] == "due" for item in records),
            "missing_ledger": sum(item["trigger_status"] == "missing_ledger" for item in records),
        },
        "projects": records,
    }
    write_json(output, payload)
    print(json.dumps({"status": "registered", "output": str(output), "summary": payload["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
