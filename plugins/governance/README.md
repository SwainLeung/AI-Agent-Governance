# Governance Codex plugin

This repo-local plugin exposes the checklist loop as deterministic Codex slash commands:

- `/governance:claim-goal` claims exactly one actionable checklist item.
- `/governance:advance-goal` records one outcome and selects the next eligible goal.

Both commands call the repository's `scripts/checklist_loop.py` CLI, which remains the non-UI fallback. The default goal mode and full-access project work authorize bounded writes and make normal thresholds advisory; they still require a resolved scope, traceability, warnings/risks reporting, and human follow-up. Governance-source updates require an explicit approved `--approval-ref`.
