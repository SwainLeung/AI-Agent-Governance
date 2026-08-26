"""Build a detailed, read-only governance Dashboard from machine-readable state."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path, default: object) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def esc(value: object) -> str:
    return html.escape(str(value if value not in (None, "") else "-"))


def checklist_stats(checklist: dict) -> dict:
    items = [item for item in checklist.get("items", []) if isinstance(item, dict)]
    statuses = Counter(str(item.get("status", "unknown")) for item in items)
    priorities = Counter(str(item.get("priority", "unknown")) for item in items)
    total = len(items)
    completed = statuses.get("completed", 0)
    return {
        "total": total,
        "completed": completed,
        "in_progress": statuses.get("in_progress", 0),
        "pending": statuses.get("pending", 0),
        "blocked": statuses.get("blocked", 0),
        "not_applicable": statuses.get("not_applicable", 0),
        "completion_percent": round((completed / total) * 100, 1) if total else 0,
        "by_priority": dict(sorted(priorities.items())),
    }


def build_adoption_queue(projects: list[dict], evidence_ref: str) -> list[dict]:
    control_map = {
        "no_current_state_ledger": "current_state_ledger",
        "stale_current_state_ledger": "freshness_and_verification",
        "no_evidence_directory_or_reports": "evidence_bundle",
        "no_decision_record": "decision_record",
        "no_rollback_record": "rollback_reference_and_restore_test",
        "no_reconciliation_record": "external_reconciliation",
        "no_dashboard_projection": "read_only_dashboard_projection",
        "no_local_agent_contract": "local_agent_contract",
        "unclassified_execution_scope": "execution_scope",
    }
    queue = []
    for project in projects:
        risk = project.get("risk_tier")
        if risk not in {"L2", "L3"} or not project.get("exists"):
            continue
        missing = [control_map.get(gap, gap) for gap in project.get("blind_spots", [])]
        if not missing:
            continue
        priority = "P0" if risk == "L3" else "P1"
        preflight_complete = bool(
            project.get("current_state", {}).get("present")
            and project.get("documentation", {}).get("AGENTS.md")
            and project.get("evidence_sample")
            and project.get("execution_scope")
        )
        queue.append({
            "queue_id": f"ADOPT-{project['project_id']}",
            "project_id": project["project_id"],
            "role": project.get("role"),
            "risk_tier": risk,
            "priority": priority,
            "status": "preflight_complete" if preflight_complete else "todo",
            "missing_controls": missing,
            "completed_controls": ["local_agent_contract", "current_state_ledger", "evidence_bundle"] if preflight_complete else [],
            "first_action": "Create an L3 decision record and test rollback before any external mutation." if preflight_complete and risk == "L3" else "Add a current-state ledger and evidence index, then rerun the bounded inventory.",
            "evidence_ref": evidence_ref,
        })
    return sorted(queue, key=lambda item: (item["priority"], item["risk_tier"], item["project_id"]))


def collect_records(root: Path, status: dict) -> dict:
    decisions = []
    decision_dir = root / "decisions"
    if decision_dir.is_dir():
        for path in sorted(decision_dir.glob("*.json")):
            record = read_json(path, {})
            if isinstance(record, dict):
                decisions.append({"file": str(path.relative_to(root)).replace("\\", "/"), **record})
    rollback_ref = status.get("rollback_ref")
    rollback = []
    if isinstance(rollback_ref, str) and rollback_ref:
        manifest = read_json(root / rollback_ref, {})
        if isinstance(manifest, dict):
            rollback.append({"file": rollback_ref, "archive_ref": manifest.get("archive_ref"), "archive_sha256": manifest.get("archive_sha256"), "file_count": len(manifest.get("files", []))})
    return {
        "source_refs": status.get("source_refs", []),
        "evidence": status.get("evidence", []),
        "decisions": decisions,
        "rollback": rollback,
        "reconciliation": status.get("reconciliation"),
    }


def build_state(root: Path, output_dir: Path, private_mode: bool = True) -> dict:
    output_dir = output_dir.resolve()
    report_prefix = str(output_dir.relative_to(root)).replace("\\", "/")
    inventory = read_json(output_dir / "project-governance-inventory.json", {})
    checklist = read_json(root / "config/governance-checklist.json", {})
    contract = read_json(root / "config/execution-contract.json", {})
    tabs = read_json(root / "config/dashboard-tabs.json", {})
    status_path = root / "STATUS.local.json" if (root / "STATUS.local.json").is_file() else root / "STATUS.json"
    status = read_json(status_path, {})
    projects = inventory.get("projects", []) if isinstance(inventory, dict) else []
    summary = inventory.get("summary", {}) if isinstance(inventory, dict) else {}
    checklist_summary = checklist_stats(checklist if isinstance(checklist, dict) else {})
    adoption_queue = build_adoption_queue(projects, f"{report_prefix}/project-governance-inventory.json")
    blindspots = Counter(gap for project in projects for gap in project.get("blind_spots", []))
    state = {
        "schema_version": "governance-dashboard-state@1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "source_refs": [
            f"{report_prefix}/project-governance-inventory.json",
            "config/governance-checklist.json",
            "config/execution-contract.json",
            "config/project-operation-policy.json",
            "config/dashboard-tabs.json",
            "docs/PROJECT-START-SWITCH.md",
            "STATUS.json",
        ],
        "tabs": tabs.get("tabs", []) if isinstance(tabs, dict) else [],
        "features": tabs.get("features", []) if isinstance(tabs, dict) else [],
        "functions": tabs.get("functions", []) if isinstance(tabs, dict) else [],
        "summary": {
            **summary,
            "checklist": checklist_summary,
            "adoption_queue_total": len(adoption_queue),
            "adoption_l3": sum(item["risk_tier"] == "L3" for item in adoption_queue),
            "adoption_l2": sum(item["risk_tier"] == "L2" for item in adoption_queue),
            "adoption_preflight_complete": sum(item["status"] == "preflight_complete" for item in adoption_queue),
            "execution_stage_count": len(contract.get("stages", [])) if isinstance(contract, dict) else 0,
            "failure_class_count": len(contract.get("failure_taxonomy", [])) if isinstance(contract, dict) else 0,
            "blindspot_type_count": len(blindspots),
        },
        "projects": projects,
        "checklist": checklist.get("items", []) if isinstance(checklist, dict) else [],
        "adoption_queue": adoption_queue,
        "blindspots": [{"name": name, "count": count} for name, count in blindspots.most_common()],
        "failure_taxonomy": contract.get("failure_taxonomy", []) if isinstance(contract, dict) else [],
        "stages": contract.get("stages", []) if isinstance(contract, dict) else [],
        "records": collect_records(root, status if isinstance(status, dict) else {}),
        "report_prefix": report_prefix,
        "registry_mode": "private-local" if private_mode else "public-template",
        "architecture": {
            "planes": [
                {"id": "policy", "name": "Policy plane", "owner": "AI Agent Governance", "boundary": "rules, risk, evidence, approval, standards"},
                {"id": "control", "name": "Control plane", "owner": "control-plane maintainers", "boundary": "routing, graph, checkpoints, traces, feedback"},
                {"id": "project", "name": "Project plane", "owner": "registered project owners", "boundary": "code, content, tests, adapters, local state"},
                {"id": "external", "name": "External plane", "owner": "external-system owner + human reviewer", "boundary": "remote systems, users, live observations"},
            ],
            "current_stage": status.get("stage"),
            "current_status": status.get("status"),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "governance-adoption-queue.json").write_text(json.dumps({"schema_version": "governance-adoption-queue@1.0.0", "generated_at": state["generated_at"], "items": adoption_queue}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "governance-dashboard-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def table(headers: list[str], rows: list[list[object]], empty: str = "No records") -> str:
    head = "".join(f"<th>{esc(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell if isinstance(cell, str) and cell.startswith('<') else esc(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    if not body:
        body = f"<tr><td colspan=\"{len(headers)}\" class=\"empty\">{esc(empty)}</td></tr>"
    return f"<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def badge(value: object, kind: str = "neutral") -> str:
    return f'<span class="badge {kind}">{esc(value)}</span>'


def render_dashboard(state: dict, root: Path) -> None:
    summary = state["summary"]
    report_prefix = state.get("report_prefix", "reports/local")
    checklist = summary["checklist"]
    projects = state["projects"]
    tabs = sorted(state["tabs"], key=lambda item: item.get("order", 99))
    nav = "".join(f'<button class="nav-item{ " active" if item["id"] == "overview" else ""}" data-view="{esc(item["id"])}"><span>{int(item.get("order", 0)):02d}</span>{esc(item.get("label_zh") or item.get("label"))}</button>' for item in tabs)

    project_rows = []
    for item in projects:
        current = item.get("current_state", {})
        first_gap = item.get("blind_spots", ["-"])[0] if item.get("blind_spots") else "-"
        project_rows.append([item.get("project_id"), item.get("risk_tier"), item.get("execution_scope") or "unclassified", current.get("stage") or "missing", current.get("status") or "unknown", "stale" if current.get("stale") else "fresh/unknown", first_gap])
    checklist_rows = [[item.get("id"), item.get("priority"), item.get("domain"), badge(item.get("status"), "good" if item.get("status") == "completed" else "warn" if item.get("status") in {"in_progress", "pending"} else "bad"), item.get("owner"), item.get("next_action")] for item in state["checklist"]]
    adoption_rows = [[item.get("queue_id"), item.get("risk_tier"), item.get("priority"), badge(item.get("status"), "good" if item.get("status") == "preflight_complete" else "warn"), ", ".join(item.get("missing_controls", [])), item.get("first_action")] for item in state["adoption_queue"]]
    blind_rows = [[item["name"], item["count"], "system-theory / execution-chain"] for item in state["blindspots"]]
    feature_rows = [[item.get("name"), badge(item.get("status"), "good" if item.get("status") == "active" else "warn"), item.get("category"), item.get("source")] for item in state["features"]]
    function_rows = [[item.get("name"), badge(item.get("status"), "good" if item.get("status") == "active" else "warn"), item.get("trigger"), item.get("entrypoint"), item.get("output"), item.get("approval")] for item in state["functions"]]
    plane_rows = [[item.get("name"), item.get("owner"), item.get("boundary")] for item in state["architecture"]["planes"]]
    stage_rows = [[item.get("id"), ", ".join(item.get("entry_conditions", [])), ", ".join(item.get("exit_evidence", [])), item.get("failure_action"), item.get("reentry_policy")] for item in state["stages"]]
    source_rows = [[ref, badge("available" if (root / ref).exists() else "missing", "good" if (root / ref).exists() else "bad"), "source/evidence"] for ref in state["source_refs"]]
    record_rows = []
    for kind in ("source_refs", "evidence"):
        record_rows.extend([[kind, ref, "status ledger"] for ref in state["records"].get(kind, [])])
    for decision in state["records"].get("decisions", []):
        record_rows.append(["decision", decision.get("file"), decision.get("decision")])
    for rollback in state["records"].get("rollback", []):
        record_rows.append(["rollback", rollback.get("file"), f"archive: {rollback.get('archive_ref')}"])
    lineage_rows = [[item.get("id"), item.get("status"), ", ".join(item.get("exit_evidence", [])), item.get("next_action")] for item in state["checklist"]]

    panels = {
        "overview": f'''<section class="view active" data-view-panel="overview"><div class="hero"><div><div class="eyebrow">Policy plane · read-only</div><h1>AI Agent Governance</h1><p>展示治理状态、执行链、Checklist、证据与跨项目 TODO。Dashboard 只投影机器可读源，不执行审批或外部写入。</p><p class="muted">Generated {esc(state["generated_at"])} · Current state {esc(state["architecture"]["current_stage"])} / {esc(state["architecture"]["current_status"])}</p></div><div class="hero-badge">{badge("READ ONLY", "good")}</div></div><div class="stats"><div class="stat"><small>Registered projects</small><strong>{summary.get("project_count", 0)}</strong><span>bounded registry</span></div><div class="stat"><small>Checklist</small><strong>{checklist.get("completed", 0)}/{checklist.get("total", 0)}</strong><span>{checklist.get("completion_percent", 0)}% completed</span></div><div class="stat"><small>Adoption TODO</small><strong>{summary.get("adoption_queue_total", 0)}</strong><span>L3 {summary.get("adoption_l3", 0)} · L2 {summary.get("adoption_l2", 0)}</span></div><div class="stat"><small>Blind spots</small><strong>{summary.get("projects_with_blind_spots", 0)}</strong><span>{summary.get("blindspot_type_count", 0)} types</span></div><div class="stat"><small>Stale ledgers</small><strong>{summary.get("stale_state_ledger", 0)}</strong><span>unknown is not pass</span></div></div><div class="grid-2"><article class="card accent-green"><h2>Next decision</h2><p>Start with the highest-risk adoption queue. Each project first receives a state ledger and evidence index, then moves through decision, rollback, and reconciliation gates.</p><div class="links"><a href="CHECKLIST.md">Checklist</a><a href="{report_prefix}/governance-adoption-queue.json">Adoption queue</a><a href="{report_prefix}/governance-dashboard-state.json">Dashboard state</a></div></article><article class="card accent-teal"><h2>Control-loop status</h2><p>Execution contract: {summary.get("execution_stage_count", 0)} stages · Failure taxonomy: {summary.get("failure_class_count", 0)} classes · Decision records: {summary.get("decision_record_present", 0)} · Rollback records: {summary.get("rollback_record_present", 0)}</p><div class="pill-row">{badge("freshness-aware", "good")}{badge("fail-closed", "good")}{badge("evidence-bound", "good")}{badge("human review", "warn")}</div></article></div></section>''',
        "projects": f'''<section class="view" data-view-panel="projects"><div class="hero"><div><div class="eyebrow">02 · Projects</div><h1>Project inventory</h1><p>项目风险、执行范围、当前阶段、状态新鲜度和首个盲点。</p></div></div>{table(["Project", "Risk", "Execution scope", "Stage", "Status", "Freshness", "First gap"], project_rows)}</section>''',
        "governance-audit": f'''<section class="view" data-view-panel="governance-audit"><div class="hero"><div><div class="eyebrow">03 · Governance audit</div><h1>System-theory blind spots</h1><p>盲点计数来自注册项目库存；缺失数据保持为 unknown / TODO，不自动转绿。</p></div></div><div class="grid-3"><div class="stat"><small>Projects with blind spots</small><strong>{summary.get("projects_with_blind_spots", 0)}</strong><span>not completion</span></div><div class="stat"><small>Blind-spot types</small><strong>{summary.get("blindspot_type_count", 0)}</strong><span>drift / evidence / coupling</span></div><div class="stat"><small>Reconciliation records</small><strong>{summary.get("reconciliation_record_present", 0)}</strong><span>L2/L3 must add them</span></div></div>{table(["Blind spot", "Count", "Control family"], blind_rows)}</section>''',
        "features": f'''<section class="view" data-view-panel="features"><div class="hero"><div><div class="eyebrow">04 · Features</div><h1>Governance capabilities</h1><p>能力状态、所属类别和 SSOT 来源。</p></div></div>{table(["Feature", "Status", "Category", "Source"], feature_rows)}</section>''',
        "functions": f'''<section class="view" data-view-panel="functions"><div class="hero"><div><div class="eyebrow">05 · Functions</div><h1>Executable functions</h1><p>函数入口、触发条件、输出和审批边界。</p></div></div>{table(["Function", "Status", "Trigger", "Entrypoint", "Output", "Approval boundary"], function_rows)}</section>''',
        "architecture": f'''<section class="view" data-view-panel="architecture"><div class="hero"><div><div class="eyebrow">06 · Architecture</div><h1>Four-plane architecture</h1><p>政策、控制、项目、外部四个平面保持边界；状态阶段由当前账本提供。</p></div></div>{table(["Plane", "Owner", "Boundary"], plane_rows)}</section>''',
        "control-plane": f'''<section class="view" data-view-panel="control-plane"><div class="hero"><div><div class="eyebrow">07 · Control plane</div><h1>Route and checkpoint controls</h1><p>控制平面只负责路由、检查点、trace、重试和恢复，不替代项目事实源。</p></div></div><div class="grid-3"><div class="card"><h3>Route</h3><p>adapter prepare → route decision → run context</p></div><div class="card"><h3>Checkpoint</h3><p>stage exit evidence + resumable checkpoint</p></div><div class="card"><h3>Recovery</h3><p>unknown external state → stop writes → reconcile</p></div></div>{table(["Failure code", "Meaning", "Default action"], [[item.get("code"), item.get("meaning"), item.get("default_action")] for item in state["failure_taxonomy"]])}</section>''',
        "external-plane": f'''<section class="view" data-view-panel="external-plane"><div class="hero"><div><div class="eyebrow">08 · External plane</div><h1>External-write boundary</h1><p>外部写入必须通过精确范围审批、回滚材料、适配器回应和独立 live verification。</p></div></div><div class="grid-2"><article class="card accent-amber"><h2>Required gate</h2><p>human_review → deploy → verify → observe</p><div class="pill-row">{badge("scope-bound", "good")}{badge("artifact hash", "good")}{badge("expires_at", "good")}{badge("rollback", "good")}</div></article><article class="card accent-teal"><h2>Fail-closed conditions</h2><p>missing evidence · stale evidence · unknown state · scope changed · artifact changed · rollback not ready</p></article></div></section>''',
        "actions": f'''<section class="view" data-view-panel="actions"><div class="hero"><div><div class="eyebrow">09 · Actions</div><h1>Checklist and TODO queue</h1><p>Checklist 是治理工作队列；统计从 `config/governance-checklist.json` 生成，跨项目 TODO 从库存生成。</p></div></div><div class="stats"><div class="stat"><small>Completed</small><strong>{checklist.get("completed", 0)}</strong><span>evidence-backed</span></div><div class="stat"><small>In progress</small><strong>{checklist.get("in_progress", 0)}</strong><span>started safely</span></div><div class="stat"><small>Pending</small><strong>{checklist.get("pending", 0)}</strong><span>not silently complete</span></div><div class="stat"><small>Preflight complete</small><strong>{summary.get("adoption_preflight_complete", 0)}</strong><span>mutation still blocked</span></div></div>{table(["Checklist item", "Priority", "Domain", "Status", "Owner", "Next action"], checklist_rows)}<h2 class="section-title">L2/L3 adoption queue</h2>{table(["Queue", "Risk", "Priority", "Status", "Missing controls", "First action"], adoption_rows)}</section>''',
        "sections": f'''<section class="view" data-view-panel="sections"><div class="hero"><div><div class="eyebrow">10 · Sections</div><h1>Execution stages</h1><p>每个阶段都必须有进入条件、退出证据、失败动作和重入策略。</p></div></div>{table(["Stage", "Entry", "Exit evidence", "Failure action", "Re-entry"], stage_rows)}</section>''',
        "sources": f'''<section class="view" data-view-panel="sources"><div class="hero"><div><div class="eyebrow">11 · Sources</div><h1>Source registry</h1><p>源文件路径和存在性；哈希与详细证据留在机器可读记录中。</p></div></div>{table(["Source", "Status", "Kind"], source_rows)}</section>''',
        "records": f'''<section class="view" data-view-panel="records"><div class="hero"><div><div class="eyebrow">12 · Records</div><h1>Evidence and decision records</h1><p>状态、证据、决定、回滚和对账记录分开呈现。</p></div></div>{table(["Record type", "Reference", "Detail"], record_rows)}</section>''',
        "metrics": f'''<section class="view" data-view-panel="metrics"><div class="hero"><div><div class="eyebrow">13 · Metrics</div><h1>Governance metrics</h1><p>指标是覆盖和风险信号，不是批准分数。</p></div></div>{table(["Metric", "Value", "Interpretation"], [["registered_projects", summary.get("project_count", 0), "bounded registry"], ["state_ledger_present", summary.get("state_ledger_present", 0), "current-state coverage"], ["stale_state_ledger", summary.get("stale_state_ledger", 0), "must not be pass"], ["decision_record_present", summary.get("decision_record_present", 0), "approval coverage"], ["rollback_record_present", summary.get("rollback_record_present", 0), "recoverability coverage"], ["reconciliation_record_present", summary.get("reconciliation_record_present", 0), "external drift control"], ["checklist_completion_percent", checklist.get("completion_percent", 0), "evidence-backed checklist progress"], ["adoption_queue_total", summary.get("adoption_queue_total", 0), "L2/L3 TODO remaining"]])}</section>''',
        "lineage": f'''<section class="view" data-view-panel="lineage"><div class="hero"><div><div class="eyebrow">14 · Lineage</div><h1>Checklist to evidence lineage</h1><p>每个工作项连接到退出证据和下一步；跨项目采用先进入队列，再由项目负责人执行。</p></div></div>{table(["Item", "Status", "Exit evidence", "Next action"], lineage_rows)}</section>''',
    }
    panel_html = "".join(panels.get(item["id"], "") for item in tabs)
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#173b4d"><title>AI Agent Governance Dashboard</title><style>
:root{{--nav:#173b4d;--nav2:#245d69;--green:#286b57;--teal:#1f6f82;--amber:#a76110;--ink:#102330;--muted:#617585;--line:#dce6eb;--canvas:#f5f8fa;--paper:#fff;--shadow:0 14px 34px rgba(16,35,48,.07);--radius:9px}}*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:var(--canvas);font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.5}}button,a{{font:inherit}}button{{cursor:pointer}}.app{{min-height:100vh;display:grid;grid-template-columns:250px minmax(0,1fr)}}.sidebar{{position:sticky;top:0;height:100vh;overflow:auto;padding:22px 14px;color:#eaf5f6;background:var(--nav)}}.brand{{display:flex;gap:10px;align-items:center;padding:4px 10px 22px;border-bottom:1px solid rgba(255,255,255,.16)}}.brand-mark{{display:grid;place-items:center;width:34px;height:34px;border-radius:8px;color:var(--nav);background:#fff;font-weight:900}}.brand strong{{display:block;font-size:14px}}.brand small{{display:block;margin-top:3px;color:#abd0d1;font-size:11px}}.nav-label{{padding:20px 12px 8px;color:#9dc3c4;font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:800}}.nav{{display:grid;gap:3px}}.nav-item{{display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;border:0;border-radius:6px;color:#d1e7e8;background:transparent;text-align:left;font-size:12px}}.nav-item:hover,.nav-item.active{{color:#fff;background:rgba(255,255,255,.14)}}.nav-item span{{width:23px;color:#8eb7ba;font-size:10px;font-weight:800}}.side-foot{{margin:22px 10px 0;padding-top:13px;border-top:1px solid rgba(255,255,255,.16);color:#9dc3c4;font-size:11px}}.main{{min-width:0}}.topbar{{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;gap:18px;align-items:center;min-height:68px;padding:0 32px;background:rgba(255,255,255,.93);border-bottom:1px solid var(--line);backdrop-filter:blur(10px)}}.crumb{{color:var(--muted);font-size:12px}}.crumb strong{{color:var(--ink)}}.top-links{{display:flex;gap:9px;flex-wrap:wrap}}.top-links a,.links a{{display:inline-flex;padding:8px 10px;border:1px solid var(--line);border-radius:6px;color:var(--teal);background:#fff;text-decoration:none;font-size:11px;font-weight:750}}.content{{max-width:1500px;margin:0 auto;padding:32px}}.view{{display:none;animation:in .16s ease-out}}.view.active{{display:block}}@keyframes in{{from{{opacity:.4;transform:translateY(3px)}}to{{opacity:1;transform:none}}}}.hero{{display:flex;justify-content:space-between;align-items:end;gap:22px;margin-bottom:23px}}.eyebrow{{margin:0 0 7px;color:var(--green);font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:850}}h1{{margin:0;font-size:clamp(28px,3.3vw,42px);line-height:1.08;letter-spacing:-.035em}}h2{{margin:0 0 8px;font-size:19px}}h3{{margin:0 0 8px;font-size:16px}}p{{margin:0;color:#445d6d;font-size:13px}}.muted{{margin-top:10px!important;color:var(--muted)!important;font-size:11px!important}}.hero-badge{{padding-bottom:3px}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:11px;margin-bottom:25px}}.stat,.card{{padding:17px;border:1px solid var(--line);border-radius:var(--radius);background:var(--paper);box-shadow:var(--shadow)}}.stat small{{display:block;color:var(--muted);font-size:10px}}.stat strong{{display:block;margin-top:4px;font-size:28px;line-height:1.05}}.stat span{{display:block;margin-top:6px;color:#536b7a;font-size:11px}}.grid-2,.grid-3{{display:grid;gap:12px;margin-top:14px}}.grid-2{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid-3{{grid-template-columns:repeat(3,minmax(0,1fr))}}.accent-green{{border-top:3px solid #64ae84}}.accent-teal{{border-top:3px solid var(--teal)}}.accent-amber{{border-top:3px solid #d99b48}}.links,.pill-row{{display:flex;gap:7px;flex-wrap:wrap;margin-top:13px}}.badge{{display:inline-flex;align-items:center;min-height:22px;padding:0 8px;border-radius:999px;background:#eef3f6;color:var(--muted);font-size:10px;font-weight:800;white-space:nowrap}}.badge.good{{color:var(--green);background:#e7f4ec}}.badge.warn{{color:var(--amber);background:#fff2dc}}.badge.bad{{color:#a33737;background:#fdeaea}}.section-title{{margin:28px 0 11px;font-size:19px}}.table-wrap{{overflow:auto;margin-top:15px;border:1px solid var(--line);border-radius:var(--radius);background:#fff;box-shadow:var(--shadow)}}table{{width:100%;min-width:760px;border-collapse:collapse}}th,td{{padding:11px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:11px}}th{{color:var(--muted);font-size:9px;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap}}tr:last-child td{{border-bottom:0}}td.empty{{padding:24px;color:var(--muted);text-align:center}}code{{padding:2px 4px;border-radius:4px;background:#eef3f6;color:var(--teal)}}@media(max-width:1050px){{.stats{{grid-template-columns:repeat(3,minmax(0,1fr))}}.grid-3{{grid-template-columns:1fr 1fr}}}}@media(max-width:760px){{.app{{display:block}}.sidebar{{position:relative;height:auto;padding-bottom:12px}}.nav{{grid-template-columns:repeat(2,minmax(0,1fr))}}.side-foot{{display:none}}.topbar{{padding:12px 18px;align-items:flex-start;flex-wrap:wrap}}.content{{padding:23px 18px 35px}}.hero{{display:block}}.hero-badge{{margin-top:14px}}.stats,.grid-2,.grid-3{{grid-template-columns:1fr}}}}
    </style></head><body><div class="app"><aside class="sidebar"><div class="brand"><div class="brand-mark">AG</div><div><strong>AI Agent Governance</strong><small>Detailed read-only dashboard</small></div></div><div class="nav-label">Workspace</div><nav class="nav" id="nav">{nav}</nav><div class="side-foot">Generated from machine-readable state.<br>Mutation and approval remain outside Dashboard.</div></aside><main class="main"><header class="topbar"><div class="crumb">AI Agent Governance / <strong id="crumbTitle">Overview</strong></div><div class="top-links"><a href="CHECKLIST.md">Checklist</a><a href="{report_prefix}/governance-adoption-queue.json">TODO queue</a><a href="STATUS.json">Status</a></div></header><div class="content">{panel_html}</div></main></div><script>const titles={json.dumps({item["id"]: item.get("label_zh") or item.get("label") for item in tabs}, ensure_ascii=False)};const panels=[...document.querySelectorAll('[data-view-panel]')];const crumb=document.querySelector('#crumbTitle');document.querySelector('#nav').addEventListener('click',e=>{{const b=e.target.closest('[data-view]');if(!b)return;const v=b.dataset.view;panels.forEach(p=>p.classList.toggle('active',p.dataset.viewPanel===v));document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x.dataset.view===v));crumb.textContent=titles[v]||'Overview';}});</script></body></html>'''
    (root / "dashboard.html").write_text(document, encoding="utf-8")


def build_dashboard(root: Path, output_dir: Path | None = None, private_mode: bool = True) -> dict:
    root = root.resolve()
    output_dir = output_dir.resolve() if output_dir else root / "reports/local"
    state = build_state(root, output_dir, private_mode=private_mode)
    render_dashboard(state, root.resolve())
    return state["summary"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/local"))
    parser.add_argument("--public-template", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else args.root / args.output_dir
    summary = build_dashboard(args.root, output_dir=output_dir, private_mode=not args.public_template)
    print(json.dumps({"output": str(output_dir / "governance-dashboard-state.json"), "summary": summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
