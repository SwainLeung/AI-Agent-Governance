# Documentation Agent Contract

## Scope

This directory contains normative system models, execution standards, security rules, migration guidance, and Dashboard design documents.

## Operating rules

- Keep normative rules explicit, testable, and consistent with machine-readable contracts under `config/`.
- Distinguish policy, control-plane behavior, project behavior, and external behavior; do not let one plane silently impersonate another.
- Update cross-references when terminology, ownership, stages, evidence, or approval boundaries change.
- Do not present a generated Dashboard, report, checklist, or changelog as the source of truth for policy.
- Use `DOCUMENTATION-CONTRACT.md` to decide whether content belongs in README, AGENTS, CHANGELOG, CHECKLIST, or a runtime record.

## Verification

After documentation changes, run `python scripts/validate_governance.py` and check that every referenced local path exists. Update the root `README.md`, `CHANGELOG.md`, or `CHECKLIST.md` when the change affects current boundaries or work state.

`README.md` explains the repository role of this directory. This file governs Agent changes inside it.
