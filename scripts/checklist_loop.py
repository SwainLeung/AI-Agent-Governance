"""Turn an actionable checklist item into a bounded goal and continue the loop.

The command writes run state only to the ignored local runtime directory by default.
The default goal mode is bounded write-authorized execution with advisory evidence
and dependency gates; it must record warnings, risks, recommendations, and human
follow-up. Updating the machine-readable checklist is never automatic and requires
an explicit approved approval reference.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = Path("config/checklist-loop-contract.json")
ITEM_STATUSES = {"pending", "in_progress", "blocked", "completed", "not_applicable"}
PERMISSION_MODES = {"restricted", "goal", "full_access"}


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
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "goal"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_inputs(root: Path, checklist_path: Path | None, contract_path: Path | None) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    contract_file = contract_path or root / DEFAULT_CONTRACT
    contract_file = contract_file if contract_file.is_absolute() else root / contract_file
    contract = read_json(contract_file)
    selected_checklist = checklist_path or Path(contract.get("source_checklist", "config/governance-checklist.json"))
    selected_checklist = selected_checklist if selected_checklist.is_absolute() else root / selected_checklist
    return selected_checklist.resolve(), read_json(selected_checklist), contract


def item_map(checklist: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = checklist.get("items")
    if not isinstance(items, list):
        raise ValueError("checklist.items must be an array")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result[item["id"]] = item
    return result


def dependencies_complete(item: dict[str, Any], items: dict[str, dict[str, Any]], acceptable: set[str]) -> bool:
    dependencies = item.get("depends_on", [])
    return isinstance(dependencies, list) and all(
        dependency in items and items[dependency].get("status") in acceptable
        for dependency in dependencies
    )


def choose_item(checklist: dict[str, Any], contract: dict[str, Any], requested_id: str | None) -> dict[str, Any]:
    items = item_map(checklist)
    selection = contract.get("selection", {})
    eligible = set(selection.get("eligible_statuses", []))
    acceptable = set(selection.get("dependency_statuses", []))
    priorities = selection.get("priority_order", [])
    priority_rank = {value: index for index, value in enumerate(priorities)}
    if requested_id:
        item = items.get(requested_id)
        if not item:
            raise ValueError(f"checklist item does not exist: {requested_id}")
        if item.get("status") not in eligible:
            raise ValueError(f"{requested_id} is not actionable from status {item.get('status')!r}")
        if not dependencies_complete(item, items, acceptable):
            raise ValueError(f"{requested_id} has unresolved dependencies")
        return item
    candidates = [
        item for item in items.values()
        if item.get("status") in eligible and dependencies_complete(item, items, acceptable)
    ]
    if not candidates:
        raise ValueError("no actionable checklist item is available")
    if selection.get("prefer_in_progress"):
        candidates.sort(key=lambda item: (item.get("status") != "in_progress", priority_rank.get(item.get("priority"), len(priority_rank)), item["id"]))
    else:
        candidates.sort(key=lambda item: (priority_rank.get(item.get("priority"), len(priority_rank)), item["id"]))
    return candidates[0]


def resolve_evidence(root: Path, item: dict[str, Any]) -> list[str]:
    evidence = item.get("exit_evidence", [])
    if not isinstance(evidence, list):
        return ["exit_evidence must be an array"]
    missing: list[str] = []
    for ref in evidence:
        if not isinstance(ref, str) or not ref:
            missing.append(repr(ref))
        elif ref.startswith(("http://", "https://")) or not (root / ref).exists():
            missing.append(ref)
    return missing


def runtime_dir(root: Path, contract: dict[str, Any], requested: Path | None) -> Path:
    directory = requested or Path(contract.get("runtime_output_dir", "reports/local/checklist-loop"))
    return (directory if directory.is_absolute() else root / directory).resolve()


def validate_execution_context(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.permission_mode == "full_access" and args.execution_scope != "project_root_execution":
        raise ValueError("full_access goals require project_root_execution; governance_root_only cannot run project commands")
    if args.execution_scope != "project_root_execution":
        return None
    if not args.startup_context:
        raise ValueError("project_root_execution requires --startup-context from prepare_project_context.py")
    context_path = args.startup_context.resolve()
    context = read_json(context_path)
    if context.get("status") != "ready":
        raise ValueError("startup context is not ready; resolve preflight blockers before project commands")
    if context.get("execution_scope") != "project_root_execution":
        raise ValueError("startup context does not authorize project_root_execution")
    return {"ref": str(context_path), "run_id": context.get("run_id"), "project_id": context.get("project_id")}


def authority_report(permission_mode: str, warnings: list[str] | None = None) -> dict[str, Any]:
    advisory = permission_mode in {"goal", "full_access"}
    return {
        "authority_mode": permission_mode,
        "writes_authorized": advisory,
        "gate_behavior": "advisory" if advisory else "enforced",
        "warnings": warnings or [],
        "risks": [],
        "recommendations": [],
        "human_follow_up": "Review warnings, risks, and recommendations after execution." if advisory else "Not required unless a later write request is proposed.",
    }


def goal_payload(item: dict[str, Any], run_id: str, reason: str, execution_scope: str, permission_mode: str, startup_context: dict[str, Any] | None) -> dict[str, Any]:
    objective = f"[{item['id']}] {item.get('title', item['id'])}"
    return {
        "command": "goal",
        "run_id": run_id,
        "objective": objective,
        "checklist_item_id": item["id"],
        "reason": reason,
        "execution_scope": execution_scope,
        "permission_mode": permission_mode,
        "authority": authority_report(permission_mode),
        "startup_context": startup_context,
        "exit_evidence": item.get("exit_evidence", []),
        "acceptance_criteria": item.get("exit_evidence", []),
        "next_action": item.get("next_action"),
        "instructions": [
            "Create one bounded goal from objective and keep its work within the resolved execution scope.",
            "Read the nearest AGENTS.md before edits and run the required tests before handoff.",
            "After producing the acceptance evidence, call the loop command with --outcome completed; source checklist updates require an explicit approval reference.",
        ],
    }


def record_goal(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    checklist_path, checklist, contract = load_inputs(root, args.checklist, args.contract)
    item = choose_item(checklist, contract, args.item_id)
    startup_context = validate_execution_context(args)
    now = utc_now()
    run_id = f"goal-{safe_token(item['id'])}-{now.strftime('%Y%m%dT%H%M%SZ')}"
    payload = goal_payload(item, run_id, args.reason, args.execution_scope, args.permission_mode, startup_context)
    output = runtime_dir(root, contract, args.output_dir) / f"{run_id}.json"
    record = {
        "schema_version": "checklist-goal-run@1.0.0",
        "created_at": now.isoformat(),
        "checklist_path": str(checklist_path),
        "goal": payload,
        "execution_note": "permission_mode is a declared runtime envelope. goal/full_access authorize bounded writes, make gates advisory, and require a post-run warning/risk report; they do not authorize scope expansion or unrecorded writes.",
    }
    write_json(output, record)
    print(json.dumps({"status": "ready", "run_id": run_id, "goal": payload, "record": str(output)}, ensure_ascii=False, indent=2))
    return 0


def advance_loop(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    startup_context = validate_execution_context(args)
    checklist_path, checklist, contract = load_inputs(root, args.checklist, args.contract)
    items = item_map(checklist)
    item = items.get(args.item_id)
    if not item:
        raise ValueError(f"checklist item does not exist: {args.item_id}")
    if args.outcome not in set(contract.get("loop_command", {}).get("accepted_outcomes", [])):
        raise ValueError(f"unsupported loop outcome: {args.outcome}")
    warnings: list[str] = []
    authority = authority_report(args.permission_mode, warnings)
    if args.outcome == "completed":
        missing = resolve_evidence(root, item)
        acceptable = set(contract.get("selection", {}).get("dependency_statuses", []))
        if missing:
            if args.permission_mode == "restricted":
                raise ValueError(f"cannot complete {args.item_id}; missing exit evidence: {', '.join(missing)}")
            warnings.append(f"gate advisory: missing exit evidence: {', '.join(missing)}")
            authority["risks"].append("completion evidence is incomplete")
            authority["recommendations"].append(f"Resolve or explicitly waive the missing exit evidence before the next review: {', '.join(missing)}")
        if not dependencies_complete(item, items, acceptable):
            if args.permission_mode == "restricted":
                raise ValueError(f"cannot complete {args.item_id}; dependencies are not complete")
            warnings.append("gate advisory: dependencies are not complete")
            authority["risks"].append("goal dependency chain is incomplete")
            authority["recommendations"].append("Complete or explicitly waive the unresolved dependencies before relying on the completed outcome")
    if args.write:
        if not args.approval_ref:
            raise ValueError("--write requires --approval-ref; submit and record the update approval before changing the checklist")
        item["status"] = args.outcome
        checklist_path.write_text(json.dumps(checklist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    now = utc_now()
    next_goal: dict[str, Any] | None = None
    next_error: str | None = None
    try:
        next_item = choose_item(checklist, contract, None)
        next_run_id = f"goal-{safe_token(next_item['id'])}-{now.strftime('%Y%m%dT%H%M%SZ')}"
        next_goal = goal_payload(next_item, next_run_id, "next actionable checklist item", args.execution_scope, args.permission_mode, startup_context)
    except ValueError as exc:
        next_error = str(exc)
    run_id = f"loop-{safe_token(args.item_id)}-{now.strftime('%Y%m%dT%H%M%SZ')}"
    output = runtime_dir(root, contract, args.output_dir) / f"{run_id}.json"
    record = {
        "schema_version": "checklist-loop-run@1.0.0",
        "created_at": now.isoformat(),
        "run_id": run_id,
        "checklist_path": str(checklist_path),
        "item_id": args.item_id,
        "outcome": args.outcome,
        "source_checklist_updated": args.write,
        "approval_ref": args.approval_ref,
        "authority": authority,
        "report": {
            "warnings": authority["warnings"],
            "risks": authority["risks"],
            "recommendations": authority["recommendations"],
            "human_follow_up": authority["human_follow_up"],
        },
        "next_goal": next_goal,
        "next_goal_error": next_error,
    }
    write_json(output, record)
    print(json.dumps({"status": "advanced", "record": str(output), **record}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--checklist", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--startup-context", type=Path, help="ready private context record from prepare_project_context.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    goal = subparsers.add_parser("goal", help="select an actionable item and emit one bounded goal")
    goal.add_argument("--item-id")
    goal.add_argument("--reason", required=True)
    goal.add_argument("--execution-scope", choices=("governance_root_only", "project_root_execution"), required=True)
    goal.add_argument("--permission-mode", choices=tuple(sorted(PERMISSION_MODES)), default="goal")
    goal.set_defaults(func=record_goal)
    loop = subparsers.add_parser("loop", help="record an outcome, optionally update the checklist, and emit the next goal")
    loop.add_argument("--item-id", required=True)
    loop.add_argument("--outcome", choices=("in_progress", "blocked", "completed"), required=True)
    loop.add_argument("--write", action="store_true", help="apply the outcome after an approval reference is supplied")
    loop.add_argument("--approval-ref", help="approval record/reference required for source checklist updates")
    loop.add_argument("--execution-scope", choices=("governance_root_only", "project_root_execution"), required=True)
    loop.add_argument("--permission-mode", choices=tuple(sorted(PERMISSION_MODES)), default="goal")
    loop.set_defaults(func=advance_loop)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
