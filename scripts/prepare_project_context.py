"""Run the private preflight required before starting or switching projects."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_REGISTRY_NAME = "project-roots.local.json"
STATE_CANDIDATES = ("STATUS.json", "status.json", "project-state.json", "pipeline-state.json")


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "project"


def resolve_registry(root: Path, requested: Path | None) -> tuple[Path, bool]:
    if requested:
        path = requested if requested.is_absolute() else root / requested
    else:
        local = root / "config" / LOCAL_REGISTRY_NAME
        path = local if local.is_file() else root / "config" / "project-roots.json"
    return path.resolve(), path.name == LOCAL_REGISTRY_NAME


def check_files(base: Path, relative_paths: list[str]) -> tuple[list[str], list[str]]:
    checked = []
    missing = []
    for relative in relative_paths:
        candidates = [item.strip() for item in relative.split(" or ")]
        found = next((item for item in candidates if (base / item).is_file()), None)
        if found:
            checked.append(str((base / found).resolve()))
        else:
            missing.append(relative)
    return checked, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/local/startup-context"))
    args = parser.parse_args()

    root = args.root.resolve()
    registry_path, private_mode = resolve_registry(root, args.registry)
    registry = read_json(registry_path)
    policy = read_json(root / "config" / "project-operation-policy.json")
    projects = [item for item in registry.get("projects", []) if isinstance(item, dict)]
    project = next((item for item in projects if item.get("id") == args.project_id), None)
    modes = policy.get("execution_scopes", {}) if isinstance(policy, dict) else {}
    scope = project.get("execution_scope") if project else None
    errors: list[str] = []

    if not project:
        errors.append(f"project is not registered: {args.project_id}")
    if scope not in modes:
        errors.append("execution_scope is missing or unknown; classify it in the private registry")

    root_checked, root_missing = check_files(
        root,
        ["AGENTS.md", "README.md", "CHECKLIST.md", "STATUS.local.json or STATUS.json", "config/project-operation-policy.json"],
    )
    errors.extend(f"governance root file missing: {item}" for item in root_missing)

    project_root = None
    project_checked: list[str] = []
    project_missing: list[str] = []
    if project and isinstance(project.get("path"), str):
        project_root = Path(project["path"]).expanduser().resolve()
    elif project:
        errors.append("registered project path is missing")

    if scope == "project_root_execution":
        if not project_root or not project_root.is_dir():
            errors.append("registered project root does not exist")
        else:
            project_checked, project_missing = check_files(
                project_root,
                ["AGENTS.md", "README.md", "CHECKLIST.md", "STATUS.json or status.json or project-state.json or pipeline-state.json"],
            )
            errors.extend(f"project root file missing: {item}" for item in project_missing)

    prepared_at = datetime.now(timezone.utc)
    run_id = f"startup-{safe_token(args.project_id)}-{prepared_at.strftime('%Y%m%dT%H%M%SZ')}"
    context = {
        "schema_version": "project-start-context@1.0.0",
        "run_id": run_id,
        "prepared_at": prepared_at.isoformat(),
        "project_id": args.project_id,
        "reason": args.reason,
        "execution_scope": scope,
        "status": "blocked" if errors else "ready",
        "governance_root": str(root),
        "project_root": str(project_root) if project_root else None,
        "registry": str(registry_path),
        "registry_mode": "private-local" if private_mode else "public-template",
        "root_files_checked": root_checked,
        "project_files_checked": project_checked,
        "missing": errors,
        "next_action": "Resolve blockers before project commands." if errors else ("Remain at governance root; no project commands allowed." if scope == "governance_root_only" else "Enter the project root and follow its nearest AGENTS.md before running commands."),
    }
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{run_id}.json"
    latest = output_dir / "latest.json"
    payload = json.dumps(context, ensure_ascii=False, indent=2) + "\n"
    output.write_text(payload, encoding="utf-8")
    latest.write_text(payload, encoding="utf-8")
    print(json.dumps({"status": context["status"], "project_id": args.project_id, "execution_scope": scope, "run_id": run_id, "output": str(output), "missing": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
