# Reports Agent Contract

## Scope

This directory contains public report policy and sanitized assessments. Generated inventory, Dashboard state, evidence, adoption queues, and rollback archives are private runtime outputs.

## Operating rules

- Keep public reports anonymized and reproducible from public policy or sanitized examples.
- Keep local paths, project identifiers, evidence bundles, traces, rollback archives, credentials, and rendered Dashboard output in ignored runtime locations.
- Treat reports as observations and evidence references, not as approval authority or a replacement for source records.
- Preserve run IDs, timestamps, freshness, source references, and unresolved gaps when reporting runtime state.

## Verification

Run `python scripts/validate_governance.py` and confirm generated output remains under ignored runtime paths. Check that every public report contains no private project or credential data.

`README.md` explains the repository role of this directory. This file governs Agent changes inside it.
