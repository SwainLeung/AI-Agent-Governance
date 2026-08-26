"""Validate the governance contract, checklist, and current-state ledger."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_STAGES = {
    "intent", "scoped", "planned", "executing", "evidence_ready", "human_review",
    "approved_sample", "approved_full", "changes_requested", "rejected", "deploy", "verify", "observe",
    "sample_observed", "expanded", "adjusted", "rolled_back", "blocked", "recovery",
}
ALLOWED_STATUSES = {"pass", "warn", "blocked", "unknown", "stale", "not_applicable"}
ALLOWED_ITEM_STATUSES = {"pending", "in_progress", "blocked", "completed", "not_applicable"}
REQUIRED_DIRECTORY_AGENT_CONTRACTS = ("config", "docs", "scripts", "decisions", "reports")


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: cannot read JSON ({exc})")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: root must be an object")
        return {}
    return value


def parse_datetime(value: object, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{label}: must be an ISO date-time string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}: invalid ISO date-time {value!r}")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label}: timezone is required")
        return None
    return parsed


def validate_status(root: Path, status: dict, errors: list[str], warnings: list[str]) -> dict:
    required = ("schema_version", "project_id", "stage", "status", "owner", "generated_at", "evidence", "next_action")
    for field in required:
        if field not in status:
            errors.append(f"STATUS.json: missing required field {field}")
    if status.get("stage") not in ALLOWED_STAGES:
        errors.append(f"STATUS.json: invalid stage {status.get('stage')!r}")
    if status.get("status") not in ALLOWED_STATUSES:
        errors.append(f"STATUS.json: invalid status {status.get('status')!r}")
    generated = parse_datetime(status.get("generated_at"), "STATUS.json.generated_at", errors)
    ttl = status.get("freshness_ttl_hours", 24)
    if not isinstance(ttl, (int, float)) or ttl <= 0:
        errors.append("STATUS.json.freshness_ttl_hours: must be positive")
        ttl = 24
    stale = False
    if generated:
        age_hours = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600
        stale = age_hours > ttl
        if stale and status.get("status") == "pass":
            errors.append(f"STATUS.json: pass state is stale ({age_hours:.1f}h > {ttl}h)")
        elif stale:
            warnings.append(f"STATUS.json: state is stale ({age_hours:.1f}h > {ttl}h)")
    if status.get("status") == "pass" and not status.get("evidence"):
        errors.append("STATUS.json: pass requires evidence")
    if status.get("stage") in {"blocked", "recovery"} and not status.get("failure"):
        errors.append(f"STATUS.json: {status['stage']} requires a failure/recovery record")
    if status.get("stage") == "human_review":
        decision = status.get("decision")
        if not isinstance(decision, dict):
            errors.append("STATUS.json: human_review requires a decision object")
    return {"stale": stale, "freshness_ttl_hours": ttl}


def validate_checklist(root: Path, checklist: dict, errors: list[str]) -> dict:
    items = checklist.get("items")
    if not isinstance(items, list) or not items:
        errors.append("governance-checklist.json: items must be a non-empty array")
        return {"total": 0, "completed": 0, "pending": 0}
    ids: set[str] = set()
    completed = 0
    pending = 0
    in_progress = 0
    required = ("id", "priority", "domain", "title", "status", "owner", "depends_on", "exit_evidence", "next_action")
    for item in items:
        if not isinstance(item, dict):
            errors.append("governance-checklist.json: every item must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append("governance-checklist.json: item id is required")
            continue
        if item_id in ids:
            errors.append(f"governance-checklist.json: duplicate item id {item_id}")
        ids.add(item_id)
        for field in required:
            if field not in item:
                errors.append(f"{item_id}: missing field {field}")
        if item.get("status") not in ALLOWED_ITEM_STATUSES:
            errors.append(f"{item_id}: invalid status {item.get('status')!r}")
        if item.get("status") == "completed":
            completed += 1
            if not item.get("exit_evidence"):
                errors.append(f"{item_id}: completed item requires exit_evidence")
        elif item.get("status") == "in_progress":
            in_progress += 1
        else:
            pending += 1
    for item in items:
        if not isinstance(item, dict):
            continue
        for dependency in item.get("depends_on", []):
            if dependency not in ids:
                errors.append(f"{item.get('id')}: unknown dependency {dependency}")
    return {"total": len(items), "completed": completed, "in_progress": in_progress, "pending": pending}


def validate_contract(contract: dict, errors: list[str]) -> dict:
    stages = contract.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("execution-contract.json: stages must be a non-empty array")
        return {"stage_count": 0, "failure_class_count": 0}
    stage_ids = set()
    for stage in stages:
        if not isinstance(stage, dict):
            errors.append("execution-contract.json: every stage must be an object")
            continue
        stage_id = stage.get("id")
        if stage_id in stage_ids:
            errors.append(f"execution-contract.json: duplicate stage {stage_id}")
        stage_ids.add(stage_id)
        for field in ("id", "entry_conditions", "exit_evidence", "failure_action", "retry_policy", "reentry_policy"):
            if field not in stage:
                errors.append(f"execution-contract.json.{stage_id}: missing field {field}")
    policy = contract.get("external_write_policy", {})
    for field in ("requires_human_review_stage", "requires_deploy_stage", "requires_live_verification_stage", "fail_closed_when"):
        if field not in policy:
            errors.append(f"execution-contract.json.external_write_policy: missing field {field}")
    for field in ("requires_human_review_stage", "requires_deploy_stage", "requires_live_verification_stage"):
        if policy.get(field) not in stage_ids:
            errors.append(f"execution-contract.json: policy references unknown stage {policy.get(field)!r}")
    failures = contract.get("failure_taxonomy", [])
    if not isinstance(failures, list) or not failures:
        errors.append("execution-contract.json: failure_taxonomy must be non-empty")
    return {"stage_count": len(stage_ids), "failure_class_count": len(failures) if isinstance(failures, list) else 0}


def validate_references(root: Path, status: dict, checklist: dict, errors: list[str]) -> None:
    refs = list(status.get("source_refs", [])) + list(status.get("evidence", []))
    for item in checklist.get("items", []):
        if isinstance(item, dict) and item.get("status") == "completed":
            refs.extend(item.get("exit_evidence", []))
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref or ref in seen:
            continue
        seen.add(ref)
        if ref.startswith(("http://", "https://")):
            continue
        if not (root / ref).exists():
            errors.append(f"missing evidence/source reference: {ref}")
    rollback_ref = status.get("rollback_ref")
    if rollback_ref:
        rollback_path = root / rollback_ref
        if not rollback_path.is_file():
            errors.append(f"STATUS.json.rollback_ref does not resolve: {rollback_ref}")
        else:
            rollback = load_json(rollback_path, errors)
            archive_ref = rollback.get("archive_ref")
            if not isinstance(archive_ref, str) or not archive_ref:
                errors.append("rollback manifest: archive_ref is required")
            elif not (root / archive_ref).is_file():
                errors.append(f"rollback manifest archive does not resolve: {archive_ref}")


def validate_documentation_contracts(root: Path, errors: list[str]) -> None:
    for filename in ("README.md", "AGENTS.md"):
        if not (root / filename).is_file():
            errors.append(f"documentation contract missing: {filename}")
    if not (root / "docs" / "DOCUMENTATION-CONTRACT.md").is_file():
        errors.append("documentation contract missing: docs/DOCUMENTATION-CONTRACT.md")
    for directory in REQUIRED_DIRECTORY_AGENT_CONTRACTS:
        contract = root / directory / "AGENTS.md"
        if not contract.is_file():
            errors.append(f"directory Agent contract missing: {directory}/AGENTS.md")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--status", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    status_path = args.status if args.status and args.status.is_absolute() else root / args.status if args.status else (root / "STATUS.local.json" if (root / "STATUS.local.json").is_file() else root / "STATUS.json")
    status = load_json(status_path, errors)
    checklist = load_json(root / "config" / "governance-checklist.json", errors)
    contract = load_json(root / "config" / "execution-contract.json", errors)
    freshness = validate_status(root, status, errors, warnings)
    checklist_summary = validate_checklist(root, checklist, errors)
    contract_summary = validate_contract(contract, errors)
    validate_references(root, status, checklist, errors)
    validate_documentation_contracts(root, errors)
    result = {
        "schema_version": "governance-validation@1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": status.get("project_id"),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "freshness": freshness,
        "checklist": checklist_summary,
        "execution_contract": contract_summary,
    }
    if args.output:
        output = args.output if args.output.is_absolute() else root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
