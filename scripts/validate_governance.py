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
ALLOWED_EXECUTION_SCOPES = {"governance_root_only", "governance_observation", "project_root_execution"}


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


def validate_status(root: Path, status: dict, errors: list[str], warnings: list[str], label: str = "STATUS.json") -> dict:
    required = ("schema_version", "project_id", "stage", "status", "owner", "generated_at", "evidence", "next_action")
    for field in required:
        if field not in status:
            errors.append(f"{label}: missing required field {field}")
    if status.get("stage") not in ALLOWED_STAGES:
        errors.append(f"{label}: invalid stage {status.get('stage')!r}")
    if status.get("status") not in ALLOWED_STATUSES:
        errors.append(f"{label}: invalid status {status.get('status')!r}")
    generated = parse_datetime(status.get("generated_at"), f"{label}.generated_at", errors)
    ttl = status.get("freshness_ttl_hours", 24)
    if not isinstance(ttl, (int, float)) or ttl <= 0:
        errors.append(f"{label}.freshness_ttl_hours: must be positive")
        ttl = 24
    stale = False
    if generated:
        age_hours = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600
        stale = age_hours > ttl
        if stale and status.get("status") == "pass":
            errors.append(f"{label}: pass state is stale ({age_hours:.1f}h > {ttl}h)")
        elif stale:
            warnings.append(f"{label}: state is stale ({age_hours:.1f}h > {ttl}h)")
    if status.get("status") == "pass" and not status.get("evidence"):
        errors.append(f"{label}: pass requires evidence")
    if status.get("stage") in {"blocked", "recovery"} and not status.get("failure"):
        errors.append(f"{label}: {status['stage']} requires a failure/recovery record")
    if status.get("stage") == "human_review":
        decision = status.get("decision")
        if not isinstance(decision, dict):
            errors.append(f"{label}: human_review requires a decision object")
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
    clarification = contract.get("clarification_policy")
    if not isinstance(clarification, dict):
        errors.append("execution-contract.json: clarification_policy must be an object")
    else:
        for field in ("must_request_clarification_when", "safe_default_when", "safe_default_action"):
            if field not in clarification:
                errors.append(f"execution-contract.json.clarification_policy: missing field {field}")
        if not isinstance(clarification.get("must_request_clarification_when"), list) or not clarification.get("must_request_clarification_when"):
            errors.append("execution-contract.json.clarification_policy.must_request_clarification_when must be a non-empty array")
        if not isinstance(clarification.get("safe_default_when"), list) or not clarification.get("safe_default_when"):
            errors.append("execution-contract.json.clarification_policy.safe_default_when must be a non-empty array")
        if not isinstance(clarification.get("safe_default_action"), str) or not clarification.get("safe_default_action"):
            errors.append("execution-contract.json.clarification_policy.safe_default_action must be a non-empty string")
    authority = contract.get("execution_authority_policy")
    if not isinstance(authority, dict):
        errors.append("execution-contract.json: execution_authority_policy must be an object")
    else:
        for mode in ("restricted", "goal", "full_access"):
            policy = authority.get(mode)
            if not isinstance(policy, dict):
                errors.append(f"execution-contract.json.execution_authority_policy.{mode} must be an object")
                continue
            for field in ("writes_authorized", "gate_behavior", "required_report_fields"):
                if field not in policy:
                    errors.append(f"execution-contract.json.execution_authority_policy.{mode}: missing field {field}")
            if policy.get("gate_behavior") not in {"enforced", "advisory"}:
                errors.append(f"execution-contract.json.execution_authority_policy.{mode}: gate_behavior must be enforced or advisory")
            if not isinstance(policy.get("required_report_fields"), list) or not policy.get("required_report_fields"):
                errors.append(f"execution-contract.json.execution_authority_policy.{mode}: required_report_fields must be a non-empty array")
        if not isinstance(authority.get("source_update_rule"), str) or not authority.get("source_update_rule"):
            errors.append("execution-contract.json.execution_authority_policy.source_update_rule is required")
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


def validate_operation_policy(root: Path, policy: dict, errors: list[str]) -> dict:
    modes = policy.get("execution_scopes")
    if not isinstance(modes, dict):
        errors.append("project-operation-policy.json: execution_scopes must be an object")
        return {"scope_count": 0}
    for scope in ALLOWED_EXECUTION_SCOPES:
        mode = modes.get(scope)
        if not isinstance(mode, dict):
            errors.append(f"project-operation-policy.json: missing execution scope {scope}")
            continue
        for field in ("enter_project_root", "execute_project_commands", "required_preflight", "stable_files_to_check", "state_files_to_refresh", "change_record"):
            if field not in mode:
                errors.append(f"project-operation-policy.json.{scope}: missing field {field}")
        if scope == "governance_observation" and (mode.get("enter_project_root") or mode.get("execute_project_commands")):
            errors.append("project-operation-policy.json.governance_observation: must not enter or execute project commands")
    gate = policy.get("startup_switch_gate")
    if not isinstance(gate, dict):
        errors.append("project-operation-policy.json: startup_switch_gate must be an object")
    else:
        for field in ("required_before_every_start_or_switch", "stable_file_rule", "unknown_scope_action"):
            if field not in gate:
                errors.append(f"project-operation-policy.json.startup_switch_gate: missing field {field}")
    if policy.get("default_unclassified_action") != "blocked":
        errors.append("project-operation-policy.json: default_unclassified_action must be blocked")
    if policy.get("required_registry_field") != "execution_scope":
        errors.append("project-operation-policy.json: required_registry_field must be execution_scope")
    gate = policy.get("startup_switch_gate", {})
    if not isinstance(gate.get("observation_exception"), str) or not gate.get("observation_exception"):
        errors.append("project-operation-policy.json.startup_switch_gate: observation_exception is required")
    envelopes = policy.get("permission_envelopes")
    full_access = envelopes.get("full_access") if isinstance(envelopes, dict) else None
    if not isinstance(full_access, dict):
        errors.append("project-operation-policy.json: permission_envelopes.full_access must be an object")
    else:
        for field in ("allowed_execution_scope", "preflight_required", "allows_direct_project_commands", "writes_authorized", "gate_behavior", "requires_post_run_report", "requires_human_follow_up", "does_not_authorize"):
            if field not in full_access:
                errors.append(f"project-operation-policy.json.permission_envelopes.full_access: missing field {field}")
        if full_access.get("allowed_execution_scope") != "project_root_execution":
            errors.append("project-operation-policy.json.permission_envelopes.full_access: allowed_execution_scope must be project_root_execution")
        if full_access.get("preflight_required") is not True:
            errors.append("project-operation-policy.json.permission_envelopes.full_access: preflight_required must be true")
        if full_access.get("writes_authorized") is not True or full_access.get("gate_behavior") != "advisory":
            errors.append("project-operation-policy.json.permission_envelopes.full_access: must be advisory and write-authorized")
    envelopes = policy.get("permission_envelopes")
    for mode in ("goal", "restricted"):
        envelope = envelopes.get(mode) if isinstance(envelopes, dict) else None
        if not isinstance(envelope, dict):
            errors.append(f"project-operation-policy.json.permission_envelopes.{mode} must be an object")
        else:
            for field in ("writes_authorized", "gate_behavior", "requires_post_run_report", "requires_human_follow_up", "does_not_authorize"):
                if field not in envelope:
                    errors.append(f"project-operation-policy.json.permission_envelopes.{mode}: missing field {field}")
    registry = load_json(root / "config" / "project-roots.json", errors)
    allowed = registry.get("allowed_execution_scopes")
    if set(allowed or []) != ALLOWED_EXECUTION_SCOPES:
        errors.append("project-roots.json: allowed_execution_scopes must match project-operation-policy.json")
    if registry.get("operation_policy_file") != "config/project-operation-policy.json":
        errors.append("project-roots.json: operation_policy_file must reference config/project-operation-policy.json")
    return {"scope_count": len(modes)}


def validate_checklist_loop_contract(root: Path, contract: dict, errors: list[str]) -> dict:
    for field in ("source_checklist", "runtime_output_dir", "selection", "goal_command", "loop_command"):
        if field not in contract:
            errors.append(f"checklist-loop-contract.json: missing field {field}")
    source = contract.get("source_checklist")
    if not isinstance(source, str) or not (root / source).is_file():
        errors.append("checklist-loop-contract.json: source_checklist must resolve inside the repository")
    selection = contract.get("selection", {})
    for field in ("eligible_statuses", "dependency_statuses", "priority_order", "prefer_in_progress"):
        if field not in selection:
            errors.append(f"checklist-loop-contract.json.selection: missing field {field}")
    loop = contract.get("loop_command", {})
    for field in ("accepted_outcomes", "completed_requires_resolved_exit_evidence", "source_checklist_write_requires_explicit_flag", "select_next_goal_after_outcome"):
        if field not in loop:
            errors.append(f"checklist-loop-contract.json.loop_command: missing field {field}")
    goal_command = contract.get("goal_command", {})
    for field in ("default_permission_mode", "required_report_fields"):
        if field not in goal_command:
            errors.append(f"checklist-loop-contract.json.goal_command: missing field {field}")
    if goal_command.get("default_permission_mode") not in {"restricted", "goal", "full_access"}:
        errors.append("checklist-loop-contract.json.goal_command.default_permission_mode must be a valid permission mode")
    if not isinstance(goal_command.get("required_report_fields"), list) or not goal_command.get("required_report_fields"):
        errors.append("checklist-loop-contract.json.goal_command.required_report_fields must be a non-empty array")
    if loop.get("source_update_requires_approval_ref") is not True:
        errors.append("checklist-loop-contract.json.loop_command.source_update_requires_approval_ref must be true")
    if not (root / "scripts" / "checklist_loop.py").is_file():
        errors.append("checklist-loop-contract.json: scripts/checklist_loop.py is missing")
    return {"enabled": not any(error.startswith("checklist-loop-contract.json") for error in errors)}


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


def validate_status_refresh_policy(root: Path, policy: dict, errors: list[str]) -> dict:
    for field in ("schema_version", "status_candidates", "preferred_private_status", "interval_hours", "proposal_output_dir", "auto_refresh_fields", "protected_fields", "source_update_rule"):
        if field not in policy:
            errors.append(f"status-refresh-policy.json: missing field {field}")
    if policy.get("preferred_private_status") != "STATUS.local.json":
        errors.append("status-refresh-policy.json: preferred_private_status must be STATUS.local.json")
    if not isinstance(policy.get("interval_hours"), (int, float)) or policy.get("interval_hours") <= 0:
        errors.append("status-refresh-policy.json: interval_hours must be positive")
    if "STATUS.json" not in policy.get("status_candidates", []) or "STATUS.local.json" not in policy.get("status_candidates", []):
        errors.append("status-refresh-policy.json: status_candidates must include STATUS.local.json and STATUS.json")
    if "status" not in policy.get("protected_fields", []) or "stage" not in policy.get("protected_fields", []):
        errors.append("status-refresh-policy.json: protected_fields must include status and stage")
    if not (root / "scripts" / "refresh_governance_status.py").is_file():
        errors.append("status-refresh-policy.json: scripts/refresh_governance_status.py is missing")
    return {"interval_hours": policy.get("interval_hours"), "preferred_private_status": policy.get("preferred_private_status")}


def validate_ledger_refresh_registry(root: Path, registry: dict, errors: list[str]) -> dict:
    for field in ("schema_version", "source_registry", "default_interval_hours", "runtime_registry_output", "trigger_type", "scan_command", "apply_command", "all_scan_command", "source_update_rule"):
        if field not in registry:
            errors.append(f"ledger-refresh-registry.json: missing field {field}")
    if registry.get("trigger_type") != "central_governance_runner":
        errors.append("ledger-refresh-registry.json: trigger_type must be central_governance_runner")
    for script in ("register_ledger_refresh.py", "refresh_registered_ledger.py", "ledger_refresh_scheduler.py"):
        if not (root / "scripts" / script).is_file():
            errors.append(f"ledger-refresh-registry.json: scripts/{script} is missing")
    scheduler = registry.get("scheduler")
    if not isinstance(scheduler, dict):
        errors.append("ledger-refresh-registry.json: scheduler must be an object")
    else:
        for field in ("entrypoint", "default_interval_hours", "default_mode", "supports_once", "supports_daemon", "writes_applied_by_default", "heartbeat_output"):
            if field not in scheduler:
                errors.append(f"ledger-refresh-registry.json.scheduler: missing field {field}")
        if scheduler.get("writes_applied_by_default") is not False:
            errors.append("ledger-refresh-registry.json.scheduler: writes_applied_by_default must be false")
    return {"trigger_type": registry.get("trigger_type"), "default_interval_hours": registry.get("default_interval_hours")}


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
    operation_policy = load_json(root / "config" / "project-operation-policy.json", errors)
    checklist_loop_contract = load_json(root / "config" / "checklist-loop-contract.json", errors)
    status_refresh_policy = load_json(root / "config" / "status-refresh-policy.json", errors)
    ledger_refresh_registry = load_json(root / "config" / "ledger-refresh-registry.json", errors)
    freshness = validate_status(root, status, errors, warnings, status_path.name)
    checklist_summary = validate_checklist(root, checklist, errors)
    contract_summary = validate_contract(contract, errors)
    operation_policy_summary = validate_operation_policy(root, operation_policy, errors)
    checklist_loop_summary = validate_checklist_loop_contract(root, checklist_loop_contract, errors)
    status_refresh_summary = validate_status_refresh_policy(root, status_refresh_policy, errors)
    ledger_refresh_summary = validate_ledger_refresh_registry(root, ledger_refresh_registry, errors)
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
        "operation_policy": operation_policy_summary,
        "checklist_loop": checklist_loop_summary,
        "status_refresh": status_refresh_summary,
        "ledger_refresh": ledger_refresh_summary,
    }
    if args.output:
        output = args.output if args.output.is_absolute() else root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
