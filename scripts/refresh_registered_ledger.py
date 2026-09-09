"""Scan or, with approval, refresh one registered project's state ledger."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
STATE_NAMES = ("STATUS.local.json", "STATUS.json", "status.json", "project-state.json", "pipeline-state.json")


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


def safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "project"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approval-ref")
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "config" / "project-roots.local.json"
    registry = read_json(registry_path)
    project = next((item for item in registry.get("projects", []) if isinstance(item, dict) and item.get("id") == args.project_id), None)
    if not project:
        raise ValueError(f"project is not registered: {args.project_id}")
    project_root = Path(str(project.get("path", ""))).expanduser().resolve()
    state_path = next((project_root / name for name in STATE_NAMES if (project_root / name).is_file()), None)
    if not state_path:
        raise ValueError(f"no state ledger found for {args.project_id}")
    current = read_json(state_path)
    timestamp = datetime.now(timezone.utc)
    run_id = f"ledger-refresh-{safe_token(args.project_id)}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}"
    refs = current.get("source_refs", []) if isinstance(current.get("source_refs"), list) else []
    missing_refs = [ref for ref in refs if isinstance(ref, str) and not (project_root / ref).exists()]
    reconciliation = {
        "status": "matched" if refs and not missing_refs else "unknown",
        "scope": "local_source_refs_and_state_ledger",
        "checked_at": timestamp.isoformat(),
        "missing_source_refs": missing_refs,
    }
    proposed = copy.deepcopy(current)
    proposed["last_verified_at"] = timestamp.isoformat()
    proposed["reconciliation"] = reconciliation
    proposed["last_update"] = {
        "mode": "approved_registered_ledger_refresh" if args.apply else "proposed_registered_ledger_refresh",
        "run_id": run_id,
        "updated_at": timestamp.isoformat(),
        "approval_ref": args.approval_ref,
    }
    risks = []
    recommendations = []
    if not refs:
        risks.append("state ledger has no source_refs to reconcile")
        recommendations.append("Add source_refs and a project-specific evidence index before marking the ledger matched")
    if missing_refs:
        risks.append(f"missing source references: {', '.join(missing_refs)}")
        recommendations.append("Restore or correct missing source references before relying on the refreshed ledger")
    proposal = {
        "schema_version": "registered-ledger-refresh-proposal@1.0.0",
        "created_at": timestamp.isoformat(),
        "run_id": run_id,
        "project_id": args.project_id,
        "target": str(state_path),
        "current": current,
        "proposed": proposed,
        "protected_fields": ["project_id", "stage", "status", "owner", "next_action", "decision", "rollback_ref"],
        "risks": risks,
        "recommendations": recommendations,
        "approval_ref": args.approval_ref,
        "applied": bool(args.apply),
    }
    output = root / "reports" / "local" / "ledger-refresh" / f"{run_id}.json"
    if args.apply:
        if not args.approval_ref:
            raise ValueError("--apply requires --approval-ref")
        if state_path.name == "STATUS.json" and project.get("id") == "ai-agent-governance":
            raise ValueError("refusing to update the public governance STATUS.json")
        write_json(state_path, proposed)
    write_json(output, proposal)
    print(json.dumps({"status": "applied" if args.apply else "proposal_ready", "project_id": args.project_id, "target": str(state_path), "proposal": str(output), "reconciliation": reconciliation, "risks": risks, "recommendations": recommendations}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
