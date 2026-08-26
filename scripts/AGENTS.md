# Scripts Agent Contract

## Scope

This directory contains local inventory, Dashboard, validation, and rollback generators.

## Operating rules

- Keep scripts deterministic, bounded to the supplied root/registry, and safe to run repeatedly.
- Default outputs containing local paths, project identifiers, evidence, traces, rollback archives, or rendered HTML to ignored runtime locations.
- Never print or persist credential values, private prompts, production logs, or deployment details.
- Treat validation failures and unknown external state as non-success; do not convert missing evidence into `pass`.
- Update the relevant schema, README, documentation contract, checklist, and changelog when a script changes machine-visible behavior.

## Verification

Run `python scripts/validate_governance.py` and the changed generator with the public template. When a private registry is available, run the local inventory path as well and inspect the output boundary.

`README.md` explains the repository role of this directory. This file governs Agent changes inside it.
