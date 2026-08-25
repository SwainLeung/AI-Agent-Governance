"""Create a secret-free restore-point manifest for governance artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_FILES = (
    "README.md",
    "AGENTS.md",
    "CHECKLIST.md",
    "CHANGELOG.md",
    "STATUS.json",
    "dashboard.html",
    "config/project-roots.json",
    "config/project-governance.schema.json",
    "config/execution-contract.json",
    "config/governance-checklist.json",
    "config/dashboard-tabs.json",
    "docs/GOVERNANCE-DASHBOARD-DESIGN.md",
    "scripts/build_governance_inventory.py",
    "scripts/build_governance_dashboard.py",
    "scripts/validate_governance.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("reports/rollback/governance-restore-point.json"))
    parser.add_argument("--archive", type=Path, default=Path("reports/rollback/governance-restore-point.zip"))
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    archive = args.archive if args.archive.is_absolute() else root / args.archive
    files = []
    for relative in DEFAULT_FILES:
        path = root / relative
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for item in files:
            bundle.write(root / item["path"], arcname=item["path"])
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "governance-restore-point@1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "secret-free governance artifacts only",
        "restore_rule": "Restore only after human review; verify archive and file hashes before replacing files.",
        "archive_ref": str(archive.relative_to(root)).replace("\\", "/"),
        "archive_sha256": archive_hash,
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "file_count": len(files)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
