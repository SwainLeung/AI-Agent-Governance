---
site: "ai-agent-governance"
type: "public-governance-contract"
version: "1.1.0"
last_modified: "2026-08-25"
---

# AI Agent Governance Contract

This public repository contains policy, schemas, generators, and sanitized examples for AI Agent governance.

## Documentation hierarchy

- `README.md` is the stable orientation layer: purpose, boundaries, repository map, and entrypoints.
- `AGENTS.md` is the operational contract layer: what an Agent may change, what must remain private, and which checks are required.
- The nearest `AGENTS.md` governs work in its directory. Directory contracts refine this file; they do not weaken its public/private boundary or fail-closed rules.
- Key directory contracts live in `config/AGENTS.md`, `docs/AGENTS.md`, `scripts/AGENTS.md`, `decisions/AGENTS.md`, and `reports/AGENTS.md`.
- Do not create one `AGENTS.md` per artifact. Add a directory contract only where ownership, authority, privacy, or validation behavior differs.

## Public/private boundary

- Public Git may contain policy, execution contracts, schemas, tab definitions, generators, and anonymized examples.
- Private local runtime data belongs in ignored files, especially `config/project-roots.local.json`, `STATUS.local.json`, `reports/local/`, `reports/evidence/`, `reports/rollback/`, and the rendered `dashboard.html`.
- Never commit personal project names, local paths, credentials, private prompts, production logs, provider values, or copied deployment details.
- A public template must remain useful without requiring a private project registry.

## Change contract

1. Read `README.md` and the relevant document under `docs/`.
2. Update machine-readable contracts when behavior changes.
3. Run `python scripts/build_governance_inventory.py` with the private local registry when working locally.
4. Run `python scripts/validate_governance.py` before handoff.
5. Record unresolved adoption gaps in private runtime reports, never as hidden completion.

The Dashboard is a local read-only projection. Its source configuration and generator are public; its rendered HTML and private runtime data are not.
