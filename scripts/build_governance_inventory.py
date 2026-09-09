"""Build a bounded, secret-free governance inventory in a private runtime directory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_REGISTRY_NAME = "project-roots.local.json"
DEFAULT_OUTPUT_DIR = Path("reports/local")
ALLOWED_EXECUTION_SCOPES = {"governance_root_only", "governance_observation", "project_root_execution"}


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def state_snapshot(path: Path, state_files: list[str]) -> dict:
    if not state_files:
        return {"present": False, "stale": False}
    state = read_json(path / state_files[0])
    generated_at = state.get("generated_at")
    last_verified_at = state.get("last_verified_at")
    freshness_timestamp = last_verified_at or generated_at
    ttl = state.get("freshness_ttl_hours", 24)
    stale = False
    age_hours = None
    if isinstance(freshness_timestamp, str):
        try:
            generated = datetime.fromisoformat(freshness_timestamp.replace("Z", "+00:00"))
            if generated.tzinfo is not None:
                age_hours = round((datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600, 2)
                stale = age_hours > float(ttl)
        except (TypeError, ValueError):
            stale = True
    return {
        "present": True,
        "schema_version": state.get("schema_version"),
        "stage": state.get("stage"),
        "status": state.get("status"),
        "generated_at": generated_at,
        "last_verified_at": last_verified_at,
        "freshness_source": "last_verified_at" if last_verified_at else "generated_at",
        "freshness_ttl_hours": ttl,
        "age_hours": age_hours,
        "stale": stale,
        "next_action": state.get("next_action"),
        "reconciliation_status": (state.get("reconciliation") or {}).get("status") if isinstance(state.get("reconciliation"), dict) else None,
        "failure_code": (state.get("failure") or {}).get("code") if isinstance(state.get("failure"), dict) else None,
    }


def project_record(item: dict) -> dict:
    path = Path(str(item["path"]))
    execution_scope = item.get("execution_scope")
    scope_known = execution_scope in ALLOWED_EXECUTION_SCOPES
    docs = {name: (path / name).is_file() for name in ("README.md", "CHANGELOG.md", "CHECKLIST.md", "AGENTS.md")}
    reports = path / "reports"
    state_files = []
    for name in ("STATUS.local.json", "STATUS.json", "status.json", "project-state.json", "pipeline-state.json"):
        candidate = path / name
        if candidate.is_file() and candidate.name.lower() not in {item.lower() for item in state_files}:
            state_files.append(candidate.name)
    evidence_dir = path / "evidence"
    evidence_files = []
    for source_dir in (reports, evidence_dir):
        if source_dir.is_dir():
            evidence_files.extend(p.name for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in {".json", ".md"})
    evidence_files = evidence_files[:20]
    decisions_dir = path / "decisions"
    report_decisions_dir = reports / "decisions"
    rollback_dir = path / "rollback"
    report_rollback_dir = reports / "rollback"
    decision_records_present = decisions_dir.is_dir() or report_decisions_dir.is_dir() or any("decision" in name.lower() or "approval" in name.lower() for name in evidence_files)
    rollback_records_present = rollback_dir.is_dir() or report_rollback_dir.is_dir() or any("rollback" in name.lower() for name in evidence_files)
    reconciliation_records_present = any("reconcil" in name.lower() or "drift" in name.lower() for name in evidence_files)
    dashboard = any((path / name).is_file() for name in ("dashboard.html", "dashboard.json", "reports/dashboard-state.json"))
    snapshot = state_snapshot(path, state_files)
    documentation_score = sum(docs.values())
    state_score = min(2, len(state_files))
    evidence_score = 1 if evidence_files else 0
    return {
        "project_id": item["id"],
        "path": str(path),
        "role": item.get("role"),
        "risk_tier": item.get("risk_tier"),
        "execution_scope": execution_scope if scope_known else None,
        "exists": path.is_dir(),
        "documentation": docs,
        "documentation_score": documentation_score,
        "state_files": state_files,
        "current_state": snapshot,
        "evidence_sample": evidence_files,
        "decision_records_present": decision_records_present,
        "rollback_records_present": rollback_records_present,
        "reconciliation_records_present": reconciliation_records_present,
        "dashboard_present": dashboard,
        "coverage_score": documentation_score + state_score + evidence_score + (1 if dashboard else 0),
        "blind_spots": [
            *([] if state_files else ["no_current_state_ledger"]),
            *([] if not snapshot.get("stale") else ["stale_current_state_ledger"]),
            *([] if evidence_files else ["no_evidence_directory_or_reports"]),
            *([] if decision_records_present else ["no_decision_record"]),
            *([] if rollback_records_present else ["no_rollback_record"]),
            *([] if reconciliation_records_present or item.get("risk_tier") == "L1" else ["no_reconciliation_record"]),
            *([] if dashboard else ["no_dashboard_projection"]),
            *([] if docs["AGENTS.md"] else ["no_local_agent_contract"]),
            *([] if scope_known else ["unclassified_execution_scope"]),
        ],
    }


def resolve_registry(root: Path, requested: Path | None) -> tuple[Path, bool]:
    if requested:
        registry_path = requested if requested.is_absolute() else root / requested
    else:
        local_path = root / "config" / LOCAL_REGISTRY_NAME
        registry_path = local_path if local_path.is_file() else root / "config" / "project-roots.json"
    return registry_path, registry_path.name == LOCAL_REGISTRY_NAME


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path, private_mode = resolve_registry(root, args.registry)
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = read_json(registry_path)
    records = [project_record(item) for item in registry.get("projects", []) if isinstance(item, dict)]
    generated_at = datetime.now(timezone.utc).isoformat()
    result = {
        "schema_version": "project-governance-inventory@1.2.0",
        "generated_at": generated_at,
        "scope": "bounded registry only; credential contents excluded; private runtime output",
        "registry_mode": "private-local" if private_mode else "public-template",
        "summary": {
            "project_count": len(records),
            "readme_present": sum(item["documentation"]["README.md"] for item in records),
            "changelog_present": sum(item["documentation"]["CHANGELOG.md"] for item in records),
            "checklist_present": sum(item["documentation"]["CHECKLIST.md"] for item in records),
            "agent_contract_present": sum(item["documentation"]["AGENTS.md"] for item in records),
            "governance_root_only": sum(item["execution_scope"] == "governance_root_only" for item in records),
            "governance_observation": sum(item["execution_scope"] == "governance_observation" for item in records),
            "project_root_execution": sum(item["execution_scope"] == "project_root_execution" for item in records),
            "unclassified_execution_scope": sum(item["execution_scope"] is None for item in records),
            "state_ledger_present": sum(bool(item["state_files"]) for item in records),
            "stale_state_ledger": sum(bool(item["current_state"].get("stale")) for item in records),
            "decision_record_present": sum(item["decision_records_present"] for item in records),
            "rollback_record_present": sum(item["rollback_records_present"] for item in records),
            "reconciliation_record_present": sum(item["reconciliation_records_present"] for item in records),
            "dashboard_present": sum(item["dashboard_present"] for item in records),
            "projects_with_blind_spots": sum(bool(item["blind_spots"]) for item in records),
        },
        "projects": records,
    }
    output = output_dir / "project-governance-inventory.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Project Governance Inventory", "", f"Generated: {generated_at}", "", "This is a private runtime report. It is ignored by Git.", "", "## Summary", ""]
    lines.extend(f"- {key}: {value}" for key, value in result["summary"].items())
    lines += ["", "## Project coverage", "", "| Project | Risk | Execution scope | Docs | State | Freshness | Decisions | Rollback | Dashboard | Blind spots |", "|---|---|---|---:|---|---|---|---|---|---|"]
    for item in records:
        state = item["current_state"]
        freshness = "stale" if state.get("stale") else (f"{state.get('age_hours')}h" if state.get("age_hours") is not None else "unknown")
        lines.append(f"| {item['project_id']} | {item.get('risk_tier') or '-'} | {item.get('execution_scope') or 'unclassified'} | {item['documentation_score']}/4 | {state.get('stage') or ', '.join(item['state_files']) or 'missing'} | {freshness} | {'yes' if item['decision_records_present'] else 'no'} | {'yes' if item['rollback_records_present'] else 'no'} | {'yes' if item['dashboard_present'] else 'no'} | {', '.join(item['blind_spots']) or '-'} |")
    (output_dir / "project-governance-inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    from build_governance_dashboard import build_dashboard

    dashboard_summary = build_dashboard(root, output_dir=output_dir, private_mode=private_mode)
    print(json.dumps({"output": str(output), "registry": str(registry_path), "private_mode": private_mode, "inventory": result["summary"], "dashboard": dashboard_summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
